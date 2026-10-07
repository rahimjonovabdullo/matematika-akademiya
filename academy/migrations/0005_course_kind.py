from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0004_course_duration"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="kind",
            field=models.CharField(
                choices=[("kurs", "Kurs"), ("test", "Test")],
                default="kurs",
                max_length=10,
                verbose_name="Turi",
            ),
        ),
    ]
