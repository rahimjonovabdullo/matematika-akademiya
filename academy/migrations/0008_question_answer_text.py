from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0007_paymentsettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="answer_text",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Bo'sh bo'lmasa, savol variantsiz: o'quvchi javobni o'zi yozadi. Bir nechta to'g'ri yozilish | bilan ajratiladi.",
                max_length=200,
                verbose_name="Yoziladigan javob",
            ),
        ),
    ]
