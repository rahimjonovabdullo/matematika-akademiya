import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from django.shortcuts import render

from .backup_views import superuser_only

TASHKENT = timezone(timedelta(hours=5))


def _fetch():
    """Botdan statistikani oladi. (data, xato_matni) qaytaradi."""
    url = os.environ.get("BOT_STATS_URL", "").strip()
    key = os.environ.get("BOT_STATS_KEY", "").strip()
    if not url or not key:
        return None, "BOT_STATS_URL yoki BOT_STATS_KEY o'zgaruvchisi Railway'da topilmadi."
    req = urllib.request.Request(
        url, headers={"X-Stats-Key": key, "User-Agent": "matematika-akademiya"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode("utf-8")), ""
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None, "Kalit mos kelmadi (STATS_KEY va BOT_STATS_KEY bir xil bo'lishi kerak)."
        return None, f"Bot xato qaytardi: {e.code}"
    except Exception as e:
        return None, f"Botga ulanib bo'lmadi: {e}"


def _fmt(ts):
    try:
        return datetime.fromtimestamp(float(ts), TASHKENT).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return "-"


def _pct(correct, total):
    return round(100 * correct / total) if total else 0


def build_stats(data, kod=""):
    users = data.get("users", [])
    tests = data.get("tests", [])
    now = data.get("now") or time.time()
    week_ago = now - 7 * 86400
    day_ago = now - 86400

    attempts = []
    students = []
    active_week = set()
    for u in users:
        hist = u.get("history", []) or []
        last = 0
        for h in hist:
            t = h.get("time", 0) or 0
            total = h.get("total", 0) or 0
            correct = h.get("correct", 0) or 0
            attempts.append({
                "name": u.get("name", ""),
                "code": h.get("code", ""),
                "correct": correct,
                "total": total,
                "pct": _pct(correct, total),
                "ts": t,
            })
            last = max(last, t)
            if t >= week_ago:
                active_week.add(u.get("id"))
        tq = u.get("total_questions", 0) or 0
        tc = u.get("total_correct", 0) or 0
        students.append({
            "name": u.get("name", ""),
            "tests_done": u.get("tests_done", 0) or 0,
            "total_correct": tc,
            "pct": _pct(tc, tq),
            "last": _fmt(last) if last else "-",
        })
    students.sort(key=lambda s: (-s["total_correct"], s["name"]))

    per_test = {}
    for a in attempts:
        per_test.setdefault(a["code"], []).append(a)
    test_rows = []
    known = set()
    for t in tests:
        code = t.get("code", "")
        known.add(code)
        items = per_test.get(code, [])
        test_rows.append({
            "code": code,
            "questions": t.get("questions", 0),
            "count": len(items),
            "avg": round(sum(i["pct"] for i in items) / len(items)) if items else 0,
            "best": max((i["pct"] for i in items), default=0),
        })
    test_rows.sort(key=lambda r: (-r["count"], r["code"]))

    recent = sorted(attempts, key=lambda a: -a["ts"])[:20]
    for a in recent:
        a["when"] = _fmt(a["ts"])

    selected = None
    kod = (kod or "").strip().upper()
    if kod:
        items = sorted(per_test.get(kod, []), key=lambda a: (-a["correct"], a["ts"]))
        for i, a in enumerate(items, start=1):
            a["rank"] = i
            a["when"] = _fmt(a["ts"])
        selected = {"code": kod, "items": items, "exists": kod in known}

    return {
        "n_students": len(users),
        "n_tests": len(tests),
        "n_attempts": len(attempts),
        "avg_pct": round(sum(a["pct"] for a in attempts) / len(attempts)) if attempts else 0,
        "active_week": len(active_week),
        "today": sum(1 for a in attempts if a["ts"] >= day_ago),
        "students": students,
        "tests": test_rows,
        "recent": recent,
        "selected": selected,
    }


@superuser_only
def manage_bot_stats(request):
    data, error = _fetch()
    ctx = {"error": error, "stats": None, "kod": request.GET.get("kod", "").strip().upper()}
    if data is not None:
        ctx["stats"] = build_stats(data, ctx["kod"])
    return render(request, "academy/manage/bot_stats.html", ctx)
