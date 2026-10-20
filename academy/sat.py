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
_BR_RE = re.compile(r'\[(.+?)\]', re.S)
_SHOWN_RE = re.compile(r'\s*\((?:shown )?in brackets\)', re.I)


def _fmt_passage(p, stem=""):
    """Matn ko'rinishi: "notes" bandlari (•) alohida qatorda, [qavs] ichidagi qism esa tagiga chiziladi
    (savolda "underlined" so'zi bo'lsa)."""
    if not p:
        return p
    under = "underlined" in (stem or "").lower() and bool(_BR_RE.search(p))

    def e(text):
        t = escape(text)
        return _BR_RE.sub(r"<u>\1</u>", t, count=1) if under else t

    if "\u2022" not in p:
        return mark_safe(e(p)) if under else p
    parts = [x.strip() for x in p.split("\u2022")]
    intro, bullets = parts[0], [x for x in parts[1:] if x]
    if not bullets:
        return mark_safe(e(p)) if under else p
    tail = ""
    m = _TAIL_RE.search(bullets[-1])
    if m:
        tail = bullets[-1][m.end():].strip()
        bullets[-1] = bullets[-1][:m.start()].strip()
    html = ""
    if intro:
        html += '<span style="display:block;margin-bottom:8px">%s</span>' % e(intro)
    for b in bullets:
        html += '<span style="display:block;padding-left:26px;text-indent:-16px;margin:0 0 6px">&bull;&nbsp;&nbsp;%s</span>' % e(b)
    if tail:
        html += '<span style="display:block;margin-top:12px">%s</span>' % e(tail)
    return mark_safe(html)


def _fix_stem(passage_raw, stem):
    """Matnda [qavs] tagiga chizilsa, savoldagi "(shown in brackets)" ni olib tashlaydi."""
    if "underlined" in (stem or "").lower() and _BR_RE.search(passage_raw or ""):
        return _SHOWN_RE.sub("", stem)
    return stem


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
            stem = _fix_stem(passage, stem)
            passage = _fmt_passage(passage, stem)
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
