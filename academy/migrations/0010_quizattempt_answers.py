from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0009_question_domain"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizattempt",
            name="answers",
            field=models.JSONField(blank=True, default=dict, verbose_name="Javoblar"),
        ),
    ]
