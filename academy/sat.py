"""SAT (Bluebook uslubidagi) testlar uchun yordamchi funksiyalar."""
import re

# Savollar tartib bo'yicha 4 modulga bo'linadi: R&W 1 (27), R&W 2 (27), Math 1 (22), Math 2 (22)
SAT_MODULES = [
    ("rw", "Reading and Writing", 1, 27, 32),
    ("rw", "Reading and Writing", 2, 27, 32),
    ("math", "Math", 1, 22, 35),
    ("math", "Math", 2, 22, 35),
]


def _sat_split(questions):
    n = len(questions)
    total = sum(m[3] for m in SAT_MODULES)
    parts, cum, prev = [], 0, 0
    for i, m in enumerate(SAT_MODULES):
        cum += m[3]
        end = n if i == len(SAT_MODULES) - 1 else int(round(n * cum / float(total)))
        parts.append(questions[prev:end])
        prev = end
    return parts


_SPLIT_RE = re.compile(r'(?<=[.!?:"\u201d\u2019)])\s+(?=[A-Z])|\n+')


def _auto_split(text):
    """Reading and Writing: if the teacher did not use ||, treat the last
    sentence (the question) as the stem and everything before it as the passage."""
    t = text.strip()
    if not t.endswith("?"):
        return "", t
    last = None
    for last in _SPLIT_RE.finditer(t[:-1]):
        pass
    if not last:
        return "", t
    return t[:last.start()].strip(), t[last.end():].strip()


def _sat_modules(questions):
    out = []
    for i, qs in enumerate(_sat_split(questions)):
        if not qs:
            continue
        sec, name, mn, _cnt, minutes = SAT_MODULES[i]
        items = []
        for k, q in enumerate(qs, start=1):
            passage, stem = "", q.text
            if "||" in q.text:
                passage, stem = [x.strip() for x in q.text.split("||", 1)]
            elif sec == "rw":
                passage, stem = _auto_split(q.text)
            choices = sorted(q.choices.all(), key=lambda c: c.id)
            items.append({
                "id": q.id, "n": k, "passage": passage, "stem": stem, "img": q.has_image,
                "open": q.is_open,
                "choices": [{"id": c.id, "letter": "ABCDEF"[j], "text": c.text} for j, c in enumerate(choices[:6])],
            })
        out.append({
            "i": len(out), "slot": i, "sec": sec, "title": name, "sn": 1 if sec == "rw" else 2,
            "mn": mn, "minutes": minutes, "qs": items,
        })
    return out


def _sat_stats(questions, post):
    stats = []
    for i, qs in enumerate(_sat_split(questions)):
        c = a = 0
        for q in qs:
            sel = post.get("q%d" % q.id)
            if sel:
                a += 1
            if q.is_open:
                if sel and q.check_open_answer(sel):
                    c += 1
                continue
            ok = next((x for x in q.choices.all() if x.is_correct), None)
            if sel and ok and str(ok.id) == sel:
                c += 1
        stats.append({"sec": SAT_MODULES[i][0], "mn": SAT_MODULES[i][2], "c": c, "a": a, "n": len(qs)})
    try:
        secs = max(0, min(int(post.get("secs", "0")), 4 * 3600))
    except (TypeError, ValueError):
        secs = 0
    return {"mods": stats, "secs": secs}


def _sat_scale(c, n):
    if not n:
        return None
    return 200 + int(round(600.0 * c / n / 10.0)) * 10


def _sat_scores(attempt, payload):
    secs = 0
    if isinstance(payload, dict):
        stats, secs = payload.get("mods") or [], payload.get("secs") or 0
    else:
        stats = payload
    if not stats:
        pct = attempt.score / float(attempt.total or 1)
        stats = [
            {"sec": "rw", "c": pct * 54, "a": 54, "n": 54},
            {"sec": "math", "c": pct * 44, "a": 44, "n": 44},
        ]
        exact = False
    else:
        exact = True

    def part(sec):
        c = sum(s["c"] for s in stats if s["sec"] == sec)
        a = sum(s.get("a", s["n"]) for s in stats if s["sec"] == sec)
        n = sum(s["n"] for s in stats if s["sec"] == sec)
        return c, a, n

    rw_c, rw_a, rw_n = part("rw")
    m_c, m_a, m_n = part("math")
    rw, mt = _sat_scale(rw_c, rw_n), _sat_scale(m_c, m_n)
    total = (rw or 0) + (mt or 0) if (rw or mt) else None
    out = {
        "rw": rw, "mt": mt, "total": total, "exact": exact,
        "rw_c": int(round(rw_c)), "rw_n": rw_n, "rw_w": int(round(rw_a - rw_c)), "rw_s": rw_n - rw_a,
        "m_c": int(round(m_c)), "m_n": m_n, "m_w": int(round(m_a - m_c)), "m_s": m_n - m_a,
        "rw_pct": int(round(100.0 * rw_c / rw_n)) if rw_n else 0,
        "m_pct": int(round(100.0 * m_c / m_n)) if m_n else 0,
        "modules": [dict(x, pct=int(round(100.0 * x["c"] / x["n"]))) for x in stats if x["n"]] if exact else [],
        "mins": max(1, int(round(secs / 60.0))) if secs else None,
    }
    if total:
        out["lo"], out["hi"] = max(400, total - 30), min(1600, total + 30)
        out["pos"] = int(round((total - 400) / 12.0))
    return out


def sat_percentile(attempt):
    """Shu testni yechgan boshqalarning necha foizidan yuqori ekani (kamida 2 ta urinish bo'lsa)."""
    from .models import QuizAttempt
    rows = list(QuizAttempt.objects.filter(
        course=attempt.course, student__is_staff=False, student__is_superuser=False, total__gt=0
    ).values_list("score", "total"))
    if len(rows) < 2:
        return None
    mine = attempt.score / float(attempt.total or 1)
    lower = sum(1 for sc, t in rows if sc / float(t) < mine - 1e-9)
    return int(round(100.0 * lower / len(rows)))
