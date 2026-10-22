import io
from datetime import datetime

from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.http import HttpResponse

superuser_only = user_passes_test(lambda u: u.is_active and u.is_superuser, login_url="login")


@superuser_only
def download_backup(request):
    """Barcha ma'lumotlar (o'quvchilar, kurslar, savollar, rasmlar, natijalar) bitta JSON fayl bo'lib yuklanadi."""
    buf = io.StringIO()
    call_command(
        "dumpdata",
        exclude=["contenttypes", "auth.permission", "sessions", "admin.logentry"],
        indent=1,
        stdout=buf,
    )
    resp = HttpResponse(buf.getvalue(), content_type="application/json; charset=utf-8")
    name = "zahira_%s.json" % datetime.now().strftime("%Y-%m-%d_%H-%M")
    resp["Content-Disposition"] = 'attachment; filename="%s"' % name
    return resp
