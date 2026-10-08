import os
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
KEYLINE_RE = re.compile(r"^\s*(kalit|javoblar)\b", re.I)
NUM_RE = re.compile(r"\d+")

ALLOWED_IMAGES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE = 2 * 1024 * 1024


class _SaveError(Exception):
    pass


def _is_staff(user):
    return user.is_authenticated and user.is_staff


def parse_questions(text):
    """Matndan savollarni ajratadi. Qaytaradi: (savollar, matn ichidagi kalit qatorlari)."""
    items = []
    key_lines = []
    cur = None
    in_key = False
    for line in text.replace("\r", "").split("\n"):
        if not line.strip():
            continue
        if in_key or KEYLINE_RE.match(line):
            in_key = True
            key_lines.append(line)
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
    return items, "\n".join(key_lines)


@login_required
@user_passes_test(_is_staff)
def manage_bulk_questions(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    errors = []
    if request.method == "POST":
        raw = request.POST.get("questions", "")
        key_raw = request.POST.get("key", "")
        items, inline_key = parse_questions(raw)
        if not key_raw.strip() and inline_key:
            key_raw = inline_key
        key = {int(n): l.upper() for n, l in KEY_RE.findall(key_raw)}

        if not items:
            errors.append("Savollar topilmadi. Har bir savol «1. matn» ko'rinishida boshlansin.")
        nums = [it["num"] for it in items]
        if len(set(nums)) != len(nums):
            errors.append("Ba'zi savol raqamlari ikki marta yozilgan. Raqamlar takrorlanmasin.")
        for it in items:
            n = it["num"]
            if len(it["options"]) < 2:
                errors.append(f"{n}-savolda kamida 2 ta variant (A, B...) bo'lishi kerak.")
            elif n not in key:
                errors.append(f"{n}-savol uchun kalitda javob yo'q.")
            elif LETTERS.index(key[n]) >= len(it["options"]):
                errors.append(f"{n}-savolda {key[n]} varianti yo'q.")

        # Rasmlar: fayl nomidagi birinchi raqam = savol raqami (5.png, 5-rasm.jpg ...)
        images = {}
        for f in request.FILES.getlist("images"):
            name = os.path.basename(f.name)
            m = NUM_RE.search(name)
            if not m:
                errors.append(f"«{name}» fayl nomida savol raqami yo'q (masalan 5.png).")
                continue
            n = int(m.group(0))
            if n not in nums:
                errors.append(f"«{name}»: {n}-savol yuqoridagi matnda topilmadi.")
                continue
            if n in images:
                errors.append(f"{n}-savol uchun bittadan ortiq rasm tanlangan.")
                continue
            if f.content_type not in ALLOWED_IMAGES:
                errors.append(f"«{name}»: faqat PNG, JPG, WEBP yoki GIF mumkin.")
                continue
            if f.size > MAX_IMAGE:
                errors.append(f"«{name}»: rasm 2 MB dan katta.")
                continue
            data = f.read()
            if not data:
                errors.append(f"«{name}» fayl bo'sh (0 bayt). Rasmni qaytadan saqlab tanlang.")
                continue
            images[n] = (data, f.content_type)

        if not errors:
            start = (course.questions.aggregate(m=Max("order"))["m"] or 0)
            try:
                with transaction.atomic():
                    for i, it in enumerate(items, 1):
                        data, ctype = images.get(it["num"], (None, ""))
                        q = Question.objects.create(
                            course=course, text=it["text"], order=start + i,
                            image_data=data, image_type=ctype,
                        )
                        if data:
                            saved = Question.objects.only("image_data").get(pk=q.pk).image_data
                            got = len(bytes(saved)) if saved is not None else 0
                            if got != len(data):
                                raise _SaveError(
                                    f"{it['num']}-savol rasmi bazaga to'liq yozilmadi: "
                                    f"yuborilgan {len(data)} bayt, bazada {got} bayt. Hech narsa saqlanmadi."
                                )
                        right = LETTERS.index(key[it["num"]])
                        for idx, opt in enumerate(it["options"]):
                            Choice.objects.create(question=q, text=opt[:300], is_correct=(idx == right))
            except _SaveError as e:
                errors.append(str(e))
            else:
                msg = f"{len(items)} ta savol qo'shildi"
                if images:
                    total = sum(len(v[0]) for v in images.values())
                    msg += f", {len(images)} tasiga rasm biriktirildi ({total // 1024} KB)"
                messages.success(request, msg + ".")
                return redirect(f"/boshqaruv/kurs/{course.id}/testlar/")
        return render(request, "academy/manage/bulk_questions.html",
                      {"course": course, "errors": errors, "raw": raw, "key": key_raw})
    return render(request, "academy/manage/bulk_questions.html",
                  {"course": course, "errors": [], "raw": "", "key": ""})
