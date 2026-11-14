from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.shortcuts import render

from .models import Course, QuizAttempt

staff_only = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="login")

BOLIMLAR = [
    ("milliy", "Milliy Sertifikat"),
    ("attestatsiya", "Attestatsiya"),
    ("sat", "SAT"),
]
LIMIT = 300


@staff_only
def manage_results(request):
    """Barcha o'quvchilarning test natijalari (faqat admin/xodim uchun)."""
    attempts = QuizAttempt.objects.select_related("student", "course").order_by("-created_at")

    bolim = request.GET.get("bolim", "")
    if bolim in dict(BOLIMLAR):
        attempts = attempts.filter(course__category=bolim)
    else:
        bolim = ""

    test = request.GET.get("test", "")
    if test.isdigit():
        attempts = attempts.filter(course_id=int(test))
    else:
        test = ""

    q = request.GET.get("q", "").strip()
    if q:
        attempts = attempts.filter(
            Q(student__first_name__icontains=q)
            | Q(student__last_name__icontains=q)
            | Q(student__username__icontains=q)
        )

    found = attempts.count()
    rows = []
    for a in attempts[:LIMIT]:
        name = ("%s %s" % (a.student.first_name, a.student.last_name)).strip()
        rows.append({
            "id": a.id,
            "name": name or a.student.username,
            "username": a.student.username,
            "course": a.course.title,
            "sat": a.course.category == "sat",
            "score": a.score,
            "total": a.total,
            "pct": a.percent,
            "date": a.created_at,
            "review": bool(a.answers),
        })

    tests = Course.objects.filter(attempts__isnull=False).distinct().order_by("title")
    if bolim:
        tests = tests.filter(category=bolim)

    return render(request, "academy/manage/results.html", {
        "rows": rows,
        "found": found,
        "limit": LIMIT,
        "bolim": bolim,
        "bolimlar": BOLIMLAR,
        "test": test,
        "tests": tests,
        "q": q,
    })
