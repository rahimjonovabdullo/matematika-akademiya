from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Matematika Akademiya — boshqaruv paneli"
admin.site.site_title = "Matematika Akademiya"
admin.site.index_title = "Xush kelibsiz, admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("academy.urls")),
]
