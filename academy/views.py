from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EnrollRequestForm, RegisterForm
from .models import Choice, Course, Enrollment, Group, PaymentSettings, QuizAttempt


def _open_free_access(user, course):
    """Bepul kurs/test: kirish darrov ochiladi (to'lov va so'rov kerak emas)."""
    enrollment, _ = Enrollment.objects.get_or_create(
        student=user, course=course, defaults={"is_active": True}
    )
    if not enrollment.is_active:
        enrollment.is_active = True
        enrollment.save(update_fields=["is_active"])
    return enrollment


def home(request):
    courses = Course.objects.filter(is_published=True)
    bolim = request.GET.get("bolim", "")
    if bolim in ("milliy", "attestatsiya", "sat"):
        courses = courses.filter(category=bolim)
    else:
        bolim = ""
    return render(request, "academy/home.html", {"courses": courses, "bolim": bolim})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Xush kelibsiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course")
    attempts = QuizAttempt.objects.filter(student=request.user).select_related("course")[:10]
    return render(
        request,
        "academy/dashboard.html",
        {"enrollments": enrollments, "attempts": attempts},
    )


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    is_free = course.price == 0
    enrollment = None
    if request.user.is_authenticated:
        if is_free:
            enrollment = _open_free_access(request.user, course)
        else:
            enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    has_access = bool(enrollment and enrollment.is_active)

    form = None
    if request.user.is_authenticated and enrollment is None:
        if request.method == "POST":
            form = EnrollRequestForm(request.POST)
            if form.is_valid():
                Enrollment.objects.create(
                    student=request.user,
                    course=course,
                    phone=form.cleaned_data["phone"],
                    note=form.cleaned_data["note"],
                )
                messages.success(
                    request,
                    "So'rovingiz qabul qilindi. To'lov chekini Telegramdan yuborganingizdan so'ng, "
                    "to'lov tasdiqlanib kirish ochiladi.",
                )
                return redirect("course_detail", slug=slug)
        else:
            form = EnrollRequestForm()

    pay = None
    if not is_free and not has_access:
        try:
            pay = PaymentSettings.load()
        except Exception:
            pay = None

    lessons = course.lessons.all()
    if not has_access:
        lessons = lessons.filter(is_free_preview=True)

    return render(
        request,
        "academy/course_detail.html",
        {
            "course": course,
            "lessons": lessons,
            "has_access": has_access,
            "enrollment": enrollment,
            "form": form,
            "is_free": is_free,
            "pay": pay,
        },
    )


@login_required
def take_quiz(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if course.price == 0:
        _open_free_access(request.user, course)
    enrollment = Enrollment.objects.filter(student=request.user, course=course, is_active=True).first()
    if not enrollment:
        messages.error(request, "Bu kurs testiga kirish uchun avval kursga yozilib, to'lovni tasdiqlating.")
        return redirect("course_detail", slug=slug)

    questions = list(course.questions.prefetch_related("choices"))

    if request.method == "POST":
        score = 0
        for q in questions:
            selected = request.POST.get(f"q{q.id}")
            correct_choice = next((c for c in q.choices.all() if c.is_correct), None)
            if selected and correct_choice and str(correct_choice.id) == selected:
                score += 1
        attempt = QuizAttempt.objects.create(
            student=request.user, course=course, score=score, total=len(questions)
        )
        return redirect("quiz_result", attempt_id=attempt.id)

    if not questions:
        messages.info(request, "Bu kurs uchun hali savollar qo'shilmagan.")
        return redirect("course_detail", slug=slug)

    return render(request, "academy/take_quiz.html", {"course": course, "questions": questions})


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    return render(request, "academy/quiz_result.html", {"attempt": attempt})


def tests_list(request):
    courses = Course.objects.filter(is_published=True).prefetch_related("questions")
    return render(request, "academy/tests_list.html", {"courses": courses})


@login_required
def results_list(request):
    attempts = QuizAttempt.objects.filter(student=request.user).select_related("course")
    return render(request, "academy/results_list.html", {"attempts": attempts})


@login_required
def my_groups(request):
    groups = request.user.study_groups.select_related("course")
    return render(request, "academy/groups.html", {"groups": groups})


def leaderboard(request):
    rows = (
        QuizAttempt.objects.values("student__username", "student__first_name")
        .annotate(best=Max("score"), attempts_count=Count("id"), avg_total=Avg("total"))
        .order_by("-best")[:50]
    )
    return render(request, "academy/leaderboard.html", {"rows": rows})


def help_page(request):
    return render(request, "academy/help.html")


@login_required
def payment_page(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course")
    return render(request, "academy/payment.html", {"enrollments": enrollments})
