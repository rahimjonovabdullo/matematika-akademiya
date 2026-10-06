from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .models import Course, Enrollment

staff_only = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="login")


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["title", "category", "description", "price", "is_published"]
        labels = {
            "title": "Kurs nomi",
            "category": "Toifa (qaysi bo'limda ko'rinadi)",
            "description": "Kurs haqida qisqacha",
            "price": "Narxi (so'm)",
            "is_published": "Saytda ko'rinsin",
        }
        help_texts = {"price": "Bepul bo'lsa 0 yozing."}
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


def _ctx(section, **extra):
    data = {
        "section": section,
        "pending_count": Enrollment.objects.filter(is_active=False).count(),
    }
    data.update(extra)
    return data


@staff_only
def manage_courses(request):
    courses = Course.objects.annotate(
        lessons_count=Count("lessons", distinct=True),
        questions_count=Count("questions", distinct=True),
    )
    return render(request, "academy/manage/courses.html", _ctx("courses", courses=courses))


@staff_only
def manage_course_form(request, pk=None):
    course = get_object_or_404(Course, pk=pk) if pk else None
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Kurs saqlandi.")
            return redirect("manage_courses")
    else:
        form = CourseForm(instance=course)
    return render(
        request,
        "academy/manage/course_form.html",
        _ctx("courses", form=form, course=course),
    )


@staff_only
@require_POST
def manage_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    title = course.title
    course.delete()
    messages.success(request, f"«{title}» kursi o'chirildi.")
    return redirect("manage_courses")


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
