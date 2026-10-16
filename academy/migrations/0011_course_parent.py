from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0010_quizattempt_answers"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                help_text="Savollar bazasi bo'lsa, qaysi kurs ichida ko'rinishini tanlang.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="banks",
                to="academy.course",
                verbose_name="Qaysi kursga tegishli",
            ),
        ),
    ]
