"""SAT (Bluebook uslubidagi) testlar uchun yordamchi funksiyalar."""

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
            choices = sorted(q.choices.all(), key=lambda c: c.id)
            items.append({
                "id": q.id, "n": k, "passage": passage, "stem": stem, "img": q.has_image,
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
        c = 0
        for q in qs:
            sel = post.get("q%d" % q.id)
            ok = next((x for x in q.choices.all() if x.is_correct), None)
            if sel and ok and str(ok.id) == sel:
                c += 1
        stats.append({"sec": SAT_MODULES[i][0], "mn": SAT_MODULES[i][2], "c": c, "n": len(qs)})
    return stats


def _sat_scale(c, n):
    if not n:
        return None
    return 200 + int(round(600.0 * c / n / 10.0)) * 10


def _sat_scores(attempt, stats):
    if not stats:
        pct = attempt.score / float(attempt.total or 1)
        stats = [{"sec": "rw", "c": pct * 54, "n": 54}, {"sec": "math", "c": pct * 44, "n": 44}]
        exact = False
    else:
        exact = True
    rw_c = sum(s["c"] for s in stats if s["sec"] == "rw")
    rw_n = sum(s["n"] for s in stats if s["sec"] == "rw")
    m_c = sum(s["c"] for s in stats if s["sec"] == "math")
    m_n = sum(s["n"] for s in stats if s["sec"] == "math")
    rw, mt = _sat_scale(rw_c, rw_n), _sat_scale(m_c, m_n)
    total = (rw or 0) + (mt or 0)
    return {
        "rw": rw, "mt": mt, "total": total if (rw or mt) else None,
        "rw_c": int(round(rw_c)), "rw_n": rw_n, "m_c": int(round(m_c)), "m_n": m_n,
        "exact": exact, "modules": [x for x in stats if x["n"]] if exact else [],
        "rw_pct": int(round(100.0 * rw_c / rw_n)) if rw_n else 0,
        "m_pct": int(round(100.0 * m_c / m_n)) if m_n else 0,
    }
