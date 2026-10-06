import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Group",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="Nomi")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("course", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="groups", to="academy.course", verbose_name="Bog'liq kurs")),
                ("members", models.ManyToManyField(blank=True, related_name="study_groups", to=settings.AUTH_USER_MODEL, verbose_name="A'zolar")),
            ],
            options={"verbose_name": "Guruh", "verbose_name_plural": "Guruhlar", "ordering": ["-created_at"]},
        ),
    ]
