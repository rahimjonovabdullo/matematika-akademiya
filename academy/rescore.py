from .models import QuizAttempt


def rescore_course(course):
    """Savol javobi tuzatilganda: shu testni topshirganlarning ballini saqlangan javoblardan qayta hisoblaydi.
    Nechta natija o'zgarganini qaytaradi."""
    questions = list(course.questions.prefetch_related("choices"))
    right_choice = {}
    for q in questions:
        if not q.is_open:
            ok = next((c for c in q.choices.all() if c.is_correct), None)
            right_choice[q.id] = str(ok.id) if ok else None

    changed = 0
    for a in QuizAttempt.objects.filter(course=course).only("id", "score", "answers"):
        given = a.answers or {}
        if not given:
            continue  # juda eski urinish: javoblar saqlanmagan
        score = 0
        for q in questions:
            sel = str(given.get(str(q.id)) or "").strip()
            if not sel:
                continue
            if q.is_open:
                good = q.check_open_answer(sel)
            else:
                good = right_choice.get(q.id) is not None and right_choice[q.id] == sel
            if good:
                score += 1
        if score != a.score:
            a.score = score
            a.save(update_fields=["score"])
            changed += 1
    return changed
