"""SAT (Bluebook uslubidagi) testlar uchun yordamchi funksiyalar."""
import re

from django.utils.html import escape
from django.utils.safestring import mark_safe

# Savollar tartib bo'yicha 4 modulga bo'linadi: R&W 1 (27), R&W 2 (27), Math 1 (22), Math 2 (22)
SAT_MODULES = [
    ("rw", "Reading and Writing", 1, 27, 32),
    ("rw", "Reading and Writing", 2, 27, 32),
    ("math", "Math", 1, 22, 35),
    ("math", "Math", 2, 22, 35),
]


# Mavzular (Bluebook "Knowledge and Skills"): kod, nomi, bo'lim
SAT_DOMAINS = [
    ("CS", "Craft and Structure", "rw"),
    ("II", "Information and Ideas", "rw"),
    ("SEC", "Standard English Conventions", "rw"),
    ("EI", "Expression of Ideas", "rw"),
    ("ALG", "Algebra", "math"),
    ("ADV", "Advanced Math", "math"),
    ("PSDA", "Problem-Solving and Data Analysis", "math"),
    ("GT", "Geometry and Trigonometry", "math"),
]
SAT_DOMAIN_NAMES = {c: n for c, n, _ in SAT_DOMAINS}


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


_SPLIT_RE = re.compile(r'(?<=[.!?:"\u201d\u2019)_\]])\s+(?=[A-Z])|\n+')


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


_TAIL_RE = re.compile(r'(?<=[.!?])\s+(?=The (?:student|writer)\b)')


def _fmt_passage(p):
    """Bluebook "notes" matni (• belgilari bilan) har bir band alohida qatorda chiqadi."""
    if not p or "\u2022" not in p:
        return p
    parts = [x.strip() for x in p.split("\u2022")]
    intro, bullets = parts[0], [x for x in parts[1:] if x]
    if not bullets:
        return p
    tail = ""
    m = _TAIL_RE.search(bullets[-1])
    if m:
        tail = bullets[-1][m.end():].strip()
        bullets[-1] = bullets[-1][:m.start()].strip()
    html = ""
    if intro:
        html += '<span style="display:block;margin-bottom:8px">%s</span>' % escape(intro)
    for b in bullets:
        html += '<span style="display:block;padding-left:26px;text-indent:-16px;margin:0 0 6px">&bull;&nbsp;&nbsp;%s</span>' % escape(b)
    if tail:
        html += '<span style="display:block;margin-top:12px">%s</span>' % escape(tail)
    return mark_safe(html)


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
            passage = _fmt_passage(passage)
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
    dom = {}
    for i, qs in enumerate(_sat_split(questions)):
        c = a = 0
        for q in qs:
            sel = post.get("q%d" % q.id)
            if sel:
                a += 1
            good = False
            if q.is_open:
                good = bool(sel and q.check_open_answer(sel))
            else:
                ok = next((x for x in q.choices.all() if x.is_correct), None)
                good = bool(sel and ok and str(ok.id) == sel)
            if good:
                c += 1
            d = (getattr(q, "domain", "") or "").strip()
            if d in SAT_DOMAIN_NAMES:
                e = dom.setdefault(d, [0, 0])
                e[1] += 1
                if good:
                    e[0] += 1
        stats.append({"sec": SAT_MODULES[i][0], "mn": SAT_MODULES[i][2], "c": c, "a": a, "n": len(qs)})
    try:
        secs = max(0, min(int(post.get("secs", "0")), 4 * 3600))
    except (TypeError, ValueError):
        secs = 0
    return {"mods": stats, "secs": secs, "doms": dom}


def _review_rows(attempt):
    """Urinishdagi har bir savol: o'quvchi javobi va to'g'ri javob (ko'rib chiqish sahifasi uchun)."""
    given = attempt.answers or {}
    questions = list(attempt.course.questions.prefetch_related("choices"))
    is_sat = attempt.course.category == "sat"
    secs = {}
    if is_sat:
        for i, qs in enumerate(_sat_split(questions)):
            for q in qs:
                secs[q.id] = (SAT_MODULES[i][0], SAT_MODULES[i][1], SAT_MODULES[i][2])
    rows = []
    for n, q in enumerate(questions, start=1):
        sel = (given.get(str(q.id)) or "").strip()
        sec = secs.get(q.id)
        passage, stem = "", q.text
        if "||" in q.text:
            passage, stem = [x.strip() for x in q.text.split("||", 1)]
        elif sec and sec[0] == "rw":
            passage, stem = _auto_split(q.text)
        passage = _fmt_passage(passage)
        row = {
            "n": n, "id": q.id, "passage": passage, "stem": stem, "img": q.has_image,
            "open": q.is_open, "given": sel,
            "domain": SAT_DOMAIN_NAMES.get((getattr(q, "domain", "") or "").strip(), ""),
            "where": ("%s, Module %d" % ("Reading and Writing" if sec[0] == "rw" else "Math", sec[2])) if sec else "",
        }
        if q.is_open:
            row["correct_text"] = (q.answer_text or "").split("|")[0].strip()
            ok = bool(sel and q.check_open_answer(sel))
            row["choices"] = []
        else:
            choices = sorted(q.choices.all(), key=lambda c: c.id)
            row["choices"] = [
                {"letter": "ABCDEF"[j], "text": c.text, "right": c.is_correct, "mine": bool(sel) and str(c.id) == sel}
                for j, c in enumerate(choices[:6])
            ]
            ok = any(c["right"] and c["mine"] for c in row["choices"])
            row["correct_text"] = next((c["letter"] for c in row["choices"] if c["right"]), "")
        row["status"] = "ok" if ok else ("skip" if not sel else "bad")
        rows.append(row)
    return rows


def _sat_scale(c, n):
    if not n:
        return None
    return 200 + int(round(600.0 * c / n / 10.0)) * 10


def _sat_scores(attempt, payload):
    secs = 0
    doms = {}
    if isinstance(payload, dict):
        stats, secs = payload.get("mods") or [], payload.get("secs") or 0
        doms = payload.get("doms") or {}
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
    def dom_rows(sec):
        rows = []
        for code, name, sc in SAT_DOMAINS:
            if sc != sec or code not in doms:
                continue
            c, n = doms[code]
            if n:
                rows.append({"code": code, "name": name, "c": c, "n": n, "pct": int(round(100.0 * c / n))})
        return rows

    out["rw_doms"], out["m_doms"] = (dom_rows("rw"), dom_rows("math")) if exact else ([], [])
    out["has_doms"] = bool(out["rw_doms"] or out["m_doms"])
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
