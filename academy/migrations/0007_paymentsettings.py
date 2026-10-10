from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0006_question_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaymentSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("card_number", models.CharField(blank=True, max_length=30, verbose_name="Karta raqami")),
                ("card_owner", models.CharField(blank=True, max_length=100, verbose_name="Karta egasining ism-familiyasi")),
                ("bank_name", models.CharField(blank=True, max_length=60, verbose_name="Bank nomi (ixtiyoriy)")),
                ("telegram", models.CharField(blank=True, max_length=100, verbose_name="Telegram manzili (chek yuboriladigan)")),
                ("instructions", models.TextField(blank=True, verbose_name="Qo'shimcha izoh (ixtiyoriy)")),
            ],
            options={"verbose_name": "To'lov sozlamasi", "verbose_name_plural": "To'lov sozlamalari"},
        ),
    ]
