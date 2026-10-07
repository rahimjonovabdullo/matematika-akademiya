from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0003_course_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="duration_minutes",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Test uchun vaqt. 0 bo'lsa ko'rsatilmaydi.",
                verbose_name="Davomiyligi (daqiqa)",
            ),
        ),
    ]
