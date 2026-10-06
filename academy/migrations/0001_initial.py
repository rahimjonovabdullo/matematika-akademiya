import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Nomi")),
                ("slug", models.SlugField(help_text="Manzilda ko'rinadigan qism, masalan: algebra-asoslari", unique=True, verbose_name="Slug")),
                ("description", models.TextField(blank=True, verbose_name="Tavsif")),
                ("price", models.PositiveIntegerField(default=0, verbose_name="Narxi (so'm)")),
                ("is_published", models.BooleanField(default=True, verbose_name="Sahifada ko'rinsinmi")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Kurs", "verbose_name_plural": "Kurslar", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Sarlavha")),
                ("video_url", models.URLField(blank=True, verbose_name="Video havolasi (YouTube va h.k.)")),
                ("content", models.TextField(blank=True, verbose_name="Dars matni / izoh")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")),
                ("is_free_preview", models.BooleanField(default=False, verbose_name="To'lovsiz ham ko'rinadimi (demo)")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="academy.course", verbose_name="Kurs")),
            ],
            options={"verbose_name": "Dars", "verbose_name_plural": "Darslar", "ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(verbose_name="Savol matni")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="academy.course", verbose_name="Kurs")),
            ],
            options={"verbose_name": "Savol", "verbose_name_plural": "Savollar", "ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=300, verbose_name="Variant matni")),
                ("is_correct", models.BooleanField(default=False, verbose_name="To'g'ri javobmi")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="academy.question", verbose_name="Savol")),
            ],
            options={"verbose_name": "Javob varianti", "verbose_name_plural": "Javob variantlari"},
        ),
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveIntegerField(verbose_name="To'g'ri javoblar soni")),
                ("total", models.PositiveIntegerField(verbose_name="Jami savollar soni")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="academy.course", verbose_name="Kurs")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to=settings.AUTH_USER_MODEL, verbose_name="O'quvchi")),
            ],
            options={"verbose_name": "Test natijasi", "verbose_name_plural": "Test natijalari", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=False, verbose_name="Kursga kirish ochilganmi")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="Telefon raqami")),
                ("note", models.CharField(blank=True, max_length=300, verbose_name="Izoh (masalan, to'lov cheki haqida)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="academy.course", verbose_name="Kurs")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to=settings.AUTH_USER_MODEL, verbose_name="O'quvchi")),
            ],
            options={"verbose_name": "Ro'yxatga olish", "verbose_name_plural": "Ro'yxatga olishlar", "unique_together": {("student", "course")}},
        ),
    ]
