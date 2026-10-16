from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .models import Choice, Course, Enrollment, Lesson, Question

staff_only = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="login")


# ---------- Formalar ----------

class CourseForm(forms.ModelForm):
    price = forms.CharField(
        label="Narxi (so'm)",
        required=False,
        widget=forms.TextInput(attrs={
            "inputmode": "numeric",
            "autocomplete": "off",
            "placeholder": "masalan: 200 000",
            "oninput": "this.value=this.value.replace(/\\D/g,'').replace(/\\B(?=(\\d{3})+(?!\\d))/g,' ')",
        }),
        help_text="Bepul bo'lsa 0 yozing. Raqamlar avtomatik ajratiladi: 200 000.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["price"] = f"{int(self.instance.price or 0):,}".replace(",", " ")

    def clean_price(self):
        raw = (self.cleaned_data.get("price") or "")
        for ch in (" ", "\u00a0", ",", "."):
            raw = raw.replace(ch, "")
        if raw == "":
            return 0
        if not raw.isdigit():
            raise forms.ValidationError("Narxni faqat raqam bilan yozing, masalan: 200 000")
        return int(raw)

    class Meta:
        model = Course
        fields = ["title", "category", "description", "price", "duration_minutes", "is_published"]
        labels = {
            "title": "Nomi",
            "category": "Toifa (qaysi bo'limda ko'rinadi)",
            "description": "Qisqacha tavsif",
            "duration_minutes": "Test davomiyligi (daqiqa)",
            "is_published": "Saytda ko'rinsin",
        }
        help_texts = {
            "duration_minutes": "Masalan 60. Ko'rsatmoqchi bo'lmasangiz 0 qoldiring.",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            base = slugify(obj.title) or "kurs"
            slug, n = base, 2
            while Course.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            obj.slug = slug
        if commit:
            obj.save()
        return obj


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "video_url", "content", "order", "is_free_preview"]
        labels = {
            "title": "Dars nomi",
            "video_url": "Video havolasi",
            "content": "Dars matni / izoh",
            "order": "Tartib raqami",
            "is_free_preview": "Bepul ko'rsatilsin (kursga yozilmaganlar ham ko'rsin)",
        }
        help_texts = {
            "video_url": "To'liq havola yozing, masalan: https://youtu.be/abc123. Video bo'lmasa bo'sh qoldiring.",
            "order": "1, 2, 3 ... Kichik raqam birinchi chiqadi.",
        }
        widgets = {
            "video_url": forms.TextInput(),
            "content": forms.Textarea(attrs={"rows": 6}),
        }


LETTERS = ["A", "B", "C", "D"]


class QuestionForm(forms.Form):
    text = forms.CharField(label="Savol matni", widget=forms.Textarea(attrs={"rows": 3}))
    order = forms.IntegerField(label="Tartib raqami", min_value=0, initial=1,
                               help_text="Savol nechanchi bo'lib chiqishi.")
    qtype = forms.ChoiceField(
        label="Savol turi",
        choices=[("choice", "Variantli (A, B, C, D)"), ("open", "Javobi yoziladi (o'quvchi o'zi yozadi)")],
        initial="choice",
    )
    choice1 = forms.CharField(label="A variant", max_length=300, required=False)
    choice2 = forms.CharField(label="B variant", max_length=300, required=False)
    choice3 = forms.CharField(label="C variant", max_length=300, required=False)
    choice4 = forms.CharField(label="D variant", max_length=300, required=False)
    correct = forms.ChoiceField(
        label="To'g'ri javob",
        choices=[("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")],
        required=False,
    )
    open_answer = forms.CharField(
        label="To'g'ri javob (o'quvchi yozadigan)", max_length=200, required=False,
        help_text="Masalan: 15 yoki 3/4 yoki 0.75. Bir nechta to'g'ri yozilish bo'lsa | bilan ajrating: 0.5|1/2. "
                  "Kasr va o'nli yozuv bir xil hisoblanadi.",
    )

    def clean(self):
        data = super().clean()
        qtype = data.get("qtype") or "choice"
        if qtype == "open":
            ans = (data.get("open_answer") or "").strip()
            if not ans:
                self.add_error("open_answer", "To'g'ri javobni yozing.")
            data["open_answer"] = ans
        else:
            if not data.get("choice1"):
                self.add_error("choice1", "Bu maydonni to'ldiring.")
            if not data.get("choice2"):
                self.add_error("choice2", "Bu maydonni to'ldiring.")
            correct = data.get("correct")
            if not correct:
                self.add_error("correct", "To'g'ri javobni tanlang.")
            elif not data.get(f"choice{correct}"):
                self.add_error("correct", "To'g'ri javob sifatida tanlangan variant bo'sh. Uni to'ldiring.")
        return data


def _ctx(section, **extra):
    data = {
        "section": section,
        "pending_count": Enrollment.objects.filter(is_active=False).count(),
    }
    data.update(extra)
    return data


def _kind_info(kind):
    if kind == "test":
        return {
            "kind": "test",
            "plural": "Testlar",
            "singular": "test",
            "list_url": "manage_tests",
            "new_url": "manage_test_new",
            "section": "tests",
        }
    return {
        "kind": "kurs",
        "plural": "Kurslar",
        "singular": "kurs",
        "list_url": "manage_courses",
        "new_url": "manage_course_new",
        "section": "courses",
    }


# ---------- Kurslar va testlar ----------

def _list_view(request, kind):
    info = _kind_info(kind)
    items = Course.objects.filter(kind=kind).annotate(
        lessons_count=Count("lessons", distinct=True),
        questions_count=Count("questions", distinct=True),
    )
    return render(
        request,
        "academy/manage/courses.html",
        _ctx(info["section"], courses=items, info=info),
    )


@staff_only
def manage_courses(request):
    return _list_view(request, "kurs")


@staff_only
def manage_tests(request):
    return _list_view(request, "test")


def _form_view(request, pk, kind):
    course = get_object_or_404(Course, pk=pk) if pk else None
    if course:
        kind = course.kind
    info = _kind_info(kind)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if kind == "kurs":
            form.fields.pop("duration_minutes", None)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.kind = kind
            obj.save()
            messages.success(request, "Saqlandi.")
            return redirect(info["list_url"])
    else:
        form = CourseForm(instance=course)
        if kind == "kurs":
            form.fields.pop("duration_minutes", None)
    return render(
        request,
        "academy/manage/course_form.html",
        _ctx(info["section"], form=form, course=course, info=info),
    )


@staff_only
def manage_course_form(request, pk=None):
    return _form_view(request, pk, "kurs")


@staff_only
def manage_test_form(request, pk=None):
    return _form_view(request, pk, "test")


@staff_only
@require_POST
def manage_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    title = course.title
    info = _kind_info(course.kind)
    course.delete()
    messages.success(request, f"«{title}» o'chirildi.")
    return redirect(info["list_url"])


# ---------- Darslar ----------

@staff_only
def manage_lessons(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    lessons = course.lessons.all()
    return render(
        request,
        "academy/manage/lessons.html",
        _ctx("courses", course=course, lessons=lessons),
    )


@staff_only
def manage_lesson_form(request, course_id, pk=None):
    course = get_object_or_404(Course, pk=course_id)
    lesson = get_object_or_404(Lesson, pk=pk, course=course) if pk else None
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()
            messages.success(request, "Dars saqlandi.")
            return redirect("manage_lessons", course_id=course.pk)
    else:
        initial = {} if lesson else {"order": course.lessons.count() + 1}
        form = LessonForm(instance=lesson, initial=initial)
    return render(
        request,
        "academy/manage/lesson_form.html",
        _ctx("courses", course=course, lesson=lesson, form=form),
    )


@staff_only
@require_POST
def manage_lesson_delete(request, course_id, pk):
    lesson = get_object_or_404(Lesson, pk=pk, course_id=course_id)
    lesson.delete()
    messages.success(request, "Dars o'chirildi.")
    return redirect("manage_lessons", course_id=course_id)


# ---------- Savollar ----------

@staff_only
def manage_questions(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    info = _kind_info(course.kind)
    questions = list(course.questions.prefetch_related("choices"))
    for q in questions:
        q.rows = [
            {"letter": LETTERS[i], "text": c.text, "is_correct": c.is_correct}
            for i, c in enumerate(q.choices.all()[:4])
        ]
        q.is_open_q = q.is_open
        q.open_answer = q.answer_text
    return render(
        request,
        "academy/manage/questions.html",
        _ctx(info["section"], course=course, questions=questions, info=info),
    )


@staff_only
def manage_question_form(request, course_id, pk=None):
    course = get_object_or_404(Course, pk=course_id)
    info = _kind_info(course.kind)
    question = get_object_or_404(Question, pk=pk, course=course) if pk else None

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            with transaction.atomic():
                if question is None:
                    question = Question(course=course)
                question.text = cd["text"]
                question.order = cd["order"]
                is_open = cd.get("qtype") == "open"
                question.answer_text = cd["open_answer"] if is_open else ""
                question.save()
                question.choices.all().delete()
                if not is_open:
                    for i in range(1, 5):
                        text = cd.get(f"choice{i}")
                        if text:
                            Choice.objects.create(
                                question=question,
                                text=text,
                                is_correct=(cd["correct"] == str(i)),
                            )
            messages.success(request, "Savol saqlandi.")
            return redirect("manage_questions", course_id=course.pk)
    else:
        if question:
            initial = {"text": question.text, "order": question.order, "correct": "1",
                       "qtype": "open" if question.is_open else "choice",
                       "open_answer": question.answer_text}
            for i, c in enumerate(question.choices.all()[:4], start=1):
                initial[f"choice{i}"] = c.text
                if c.is_correct:
                    initial["correct"] = str(i)
        else:
            initial = {"order": course.questions.count() + 1, "correct": "1", "qtype": "choice"}
        form = QuestionForm(initial=initial)

    return render(
        request,
        "academy/manage/question_form.html",
        _ctx(info["section"], course=course, question=question, form=form, info=info),
    )


@staff_only
@require_POST
def manage_question_delete(request, course_id, pk):
    question = get_object_or_404(Question, pk=pk, course_id=course_id)
    question.delete()
    messages.success(request, "Savol o'chirildi.")
    return redirect("manage_questions", course_id=course_id)


# ---------- So'rovlar ----------

@staff_only
def manage_requests(request):
    if request.method == "POST":
        enrollment = get_object_or_404(Enrollment, pk=request.POST.get("id"))
        action = request.POST.get("action")
        if action == "open":
            enrollment.is_active = True
            enrollment.save()
            messages.success(request, f"{enrollment.student.username} uchun kirish ochildi.")
        elif action == "close":
            enrollment.is_active = False
            enrollment.save()
            messages.success(request, f"{enrollment.student.username} uchun kirish yopildi.")
        elif action == "delete":
            enrollment.delete()
            messages.success(request, "So'rov o'chirildi.")
        return redirect(request.get_full_path())

    holat = request.GET.get("holat", "")
    enrollments = Enrollment.objects.select_related("student", "course").order_by("-created_at")
    if holat == "kutilmoqda":
        enrollments = enrollments.filter(is_active=False)
    elif holat == "ochiq":
        enrollments = enrollments.filter(is_active=True)
    else:
        holat = ""
    return render(
        request,
        "academy/manage/requests.html",
        _ctx("requests", enrollments=enrollments, holat=holat),
    )
