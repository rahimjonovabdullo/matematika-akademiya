from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Question

ALLOWED = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_BYTES = 2 * 1024 * 1024


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(_is_staff)
def manage_question_image(request, course_id, pk):
    question = get_object_or_404(Question, pk=pk, course_id=course_id)
    back = f"/boshqaruv/kurs/{course_id}/testlar/"
    error = ""

    if request.method == "POST":
        if request.POST.get("action") == "delete":
            question.image_data = None
            question.image_type = ""
            question.save(update_fields=["image_data", "image_type"])
            messages.success(request, "Rasm o'chirildi.")
            return redirect(back)

        f = request.FILES.get("image")
        if not f:
            error = "Rasm tanlanmadi."
        elif f.content_type not in ALLOWED:
            error = "Faqat PNG, JPG, WEBP yoki GIF rasm yuklash mumkin."
        elif f.size > MAX_BYTES:
            error = "Rasm juda katta (2 MB dan oshmasin)."
        else:
            question.image_data = f.read()
            question.image_type = f.content_type
            question.save(update_fields=["image_data", "image_type"])
            messages.success(request, "Rasm saqlandi.")
            return redirect(back)

    return render(request, "academy/manage/question_image.html", {
        "course": question.course,
        "question": question,
        "back": back,
        "error": error,
    })


def question_image(request, pk):
    """Savol rasmini ko'rsatadi."""
    q = get_object_or_404(Question.objects.only("id", "image_data", "image_type"), pk=pk)
    if not q.image_type:
        return HttpResponse(f"Savol {pk}: rasm turi yozilmagan (rasm yo'q).", status=404,
                            content_type="text/plain; charset=utf-8")
    data = bytes(q.image_data) if q.image_data is not None else b""
    if not data:
        return HttpResponse(
            f"Savol {pk}: rasm turi bor ({q.image_type}), lekin rasm ma'lumoti bazada bo'sh.",
            status=404, content_type="text/plain; charset=utf-8")
    resp = HttpResponse(data, content_type=q.image_type)
    resp["Cache-Control"] = "public, max-age=60"
    return resp
