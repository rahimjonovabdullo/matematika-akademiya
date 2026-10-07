import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render

from .models import Choice, Course, Question

LETTERS = "ABCDEF"
Q_RE = re.compile(r"^\s*(\d+)\s*[.)]\s*(.*\S)\s*$")
O_RE = re.compile(r"^\s*([A-Fa-f])\s*[.)]\s*(.*\S)\s*$")
KEY_RE = re.compile(r"(\d+)\s*[-:.)]?\s*([A-Fa-f])(?![A-Za-z])")


def _is_staff(user):
    return user.is_authenticated and user.is_staff


def parse_questions(text):
    """Matndan savollar ro'yxatini ajratadi: [{num, text, options[]}]."""
    items = []
    cur = None
    for line in text.replace("\r", "").split("\n"):
        if not line.strip():
            continue
        om = O_RE.match(line)
        qm = Q_RE.match(line)
        if om and cur is not None:
            cur["options"].append(om.group(2).strip())
        elif qm:
            cur = {"num": int(qm.group(1)), "text": qm.group(2).strip(), "options": []}
            items.append(cur)
        elif cur is not None:
            if cur["options"]:
                cur["options"][-1] += " " + line.strip()
            else:
                cur["text"] += " " + line.strip()
    return items


@login_required
@user_passes_test(_is_staff)
def manage_bulk_questions(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    errors = []
    if request.method == "POST":
        raw = request.POST.get("questions", "")
        key_raw = request.POST.get("key", "")
        items = parse_questions(raw)
        key = {int(n): l.upper() for n, l in KEY_RE.findall(key_raw)}

        if not items:
            errors.append("Savollar topilmadi. Har bir savol «1. matn» ko'rinishida boshlansin.")
        for it in items:
            n = it["num"]
            if len(it["options"]) < 2:
                errors.append(f"{n}-savolda kamida 2 ta variant (A, B...) bo'lishi kerak.")
            elif n not in key:
                errors.append(f"{n}-savol uchun kalitda javob yo'q.")
            elif LETTERS.index(key[n]) >= len(it["options"]):
                errors.append(f"{n}-savolda {key[n]} varianti yo'q.")

        if not errors:
            start = (course.questions.aggregate(m=Max("order"))["m"] or 0)
            with transaction.atomic():
                for i, it in enumerate(items, 1):
                    q = Question.objects.create(course=course, text=it["text"], order=start + i)
                    right = LETTERS.index(key[it["num"]])
                    for idx, opt in enumerate(it["options"]):
                        Choice.objects.create(question=q, text=opt[:300], is_correct=(idx == right))
            messages.success(request, f"{len(items)} ta savol qo'shildi.")
            return redirect(f"/boshqaruv/kurs/{course.id}/testlar/")
        return render(request, "academy/manage/bulk_questions.html",
                      {"course": course, "errors": errors, "raw": raw, "key": key_raw})
    return render(request, "academy/manage/bulk_questions.html",
                  {"course": course, "errors": [], "raw": "", "key": ""})
