import math

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
    # Bosh sahifada faqat darsi bor kurslar chiqadi. Darssiz (faqat test) kurslar
    # "Testlar" bo'limida ko'rinadi.
    courses = (
        Course.objects.filter(is_published=True)
        .annotate(lesson_total=Count("lessons"))
        .filter(lesson_total__gt=0)
    )
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
    courses = Course.objects.filter(is_published=True)
    bolim = request.GET.get("bolim", "")
    if bolim in ("milliy", "attestatsiya", "sat"):
        courses = courses.filter(category=bolim)
    else:
        bolim = ""
    courses = list(courses.annotate(questions_count=Count("questions", distinct=True)))

    # Ishtirokchi = testni kamida bir marta yechgan o'quvchilar soni
    part_rows = QuizAttempt.objects.values_list("course_id").annotate(n=Count("student", distinct=True))
    participants = {course_id: n for course_id, n in part_rows}
    for c in courses:
        c.participants = participants.get(c.id, 0)

    return render(request, "academy/tests_list.html", {"courses": courses, "bolim": bolim})


@login_required
def results_list(request):
    attempts = QuizAttempt.objects.filter(student=request.user).select_related("course")
    return render(request, "academy/results_list.html", {"attempts": attempts})


@login_required
def my_groups(request):
    groups = request.user.study_groups.select_related("course")
    return render(request, "academy/groups.html", {"groups": groups})


def _level(pct):
    if pct >= 85:
        return "A'lo", "#2fa84f"
    if pct >= 70:
        return "Yaxshi", "#8cc63f"
    if pct >= 50:
        return "O'rta", "#f2a93b"
    if pct >= 30:
        return "Boshlang'ich", "#ee6b3b"
    return "Past", "#e5393f"


def _build_leaderboard(attempts, me_id):
    """attempts: har bir urinish uchun dict. Natija: tartiblangan o'quvchilar ro'yxati."""
    people = {}
    for a in attempts:
        total = a["total"]
        if not total:
            continue
        pct = a["score"] * 100.0 / total
        sid = a["student_id"]
        p = people.get(sid)
        if p is None:
            full = ("%s %s" % (a["student__first_name"], a["student__last_name"])).strip()
            p = {
                "id": sid,
                "name": full or a["student__username"],
                "attempts": 0,
                "sum": 0.0,
                "best": -1.0,
                "bs": 0,
                "bn": 0,
                "courses": {},
            }
            people[sid] = p
        p["attempts"] += 1
        p["sum"] += pct
        if pct > p["best"]:
            p["best"], p["bs"], p["bn"] = pct, a["score"], total
        c = p["courses"].get(a["course_id"])
        if c is None or pct > c["pct"]:
            p["courses"][a["course_id"]] = {"t": a["course__title"], "pct": pct, "s": a["score"], "n": total}

    ordered = sorted(
        people.values(),
        key=lambda p: (-(p["sum"] / p["attempts"]), -p["best"], p["attempts"], p["id"]),
    )

    rows = []
    for i, p in enumerate(ordered, start=1):
        top = int(p["best"] + 0.5)
        avg_exact = p["sum"] / p["attempts"]
        avg = int(avg_exact + 0.5)
        level, color = _level(avg)
        tests = sorted(p["courses"].values(), key=lambda c: -c["pct"])
        rows.append(
            {
                "rank": i,
                "name": p["name"],
                "initial": p["name"][:1].upper(),
                "best": avg,
                "best_exact": avg_exact,
                "top": top,
                "avg": avg,
                "attempts": p["attempts"],
                "tests": len(tests),
                "bs": p["bs"],
                "bn": p["bn"],
                "level": level,
                "color": color,
                "off": round(276.46 * (1 - avg / 100.0), 2),
                "me": p["id"] == me_id,
                "list": [{"t": c["t"], "p": int(c["pct"] + 0.5), "s": c["s"], "n": c["n"]} for c in tests[:8]],
            }
        )
    return rows


def leaderboard(request):
    # Reyting O'RTACHA o'zlashtirish foizi bo'yicha (best = o'rtacha, top = eng yaxshi urinish). Admin va xodimlar chiqarib tashlangan.
    attempts = QuizAttempt.objects.filter(
        student__is_staff=False, student__is_superuser=False, total__gt=0
    ).values(
        "student_id",
        "student__username",
        "student__first_name",
        "student__last_name",
        "course_id",
        "course__title",
        "score",
        "total",
    )
    me_id = request.user.id if request.user.is_authenticated else None
    rows = _build_leaderboard(attempts, me_id)

    me = next((r for r in rows if r["me"]), None)
    me_gap = 0
    me_prev_rank = 0
    if me and me["rank"] > 1:
        prev = rows[me["rank"] - 2]
        diff = prev["best_exact"] - me["best_exact"]
        me_gap = int(math.ceil(diff - 1e-9)) if diff > 1e-9 else 0
        me_prev_rank = prev["rank"]

    shown = rows[:103]
    lb_data = {
        str(r["rank"]): {
            "rank": r["rank"],
            "name": r["name"],
            "best": r["best"],
            "top": r["top"],
            "avg": r["avg"],
            "attempts": r["attempts"],
            "tests": r["tests"],
            "bs": r["bs"],
            "bn": r["bn"],
            "level": r["level"],
            "color": r["color"],
            "list": r["list"],
        }
        for r in shown
    }

    return render(
        request,
        "academy/leaderboard.html",
        {
            "podium": shown[:3],
            "rest": shown[3:],
            "me": me,
            "me_gap": me_gap,
            "me_prev_rank": me_prev_rank,
            "total_students": len(rows),
            "top_pct": rows[0]["best"] if rows else 0,
            "total_attempts": sum(r["attempts"] for r in rows),
            "lb_data": lb_data,
        },
    )


def help_page(request):
    return render(request, "academy/help.html")


@login_required
def payment_page(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related("course")
    return render(request, "academy/payment.html", {"enrollments": enrollments})
