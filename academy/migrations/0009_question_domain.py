from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0008_question_answer_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="domain",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Faqat SAT testlari uchun: savol qaysi mavzuga tegishli.",
                max_length=5,
                verbose_name="Mavzu (SAT)",
            ),
        ),
    ]
