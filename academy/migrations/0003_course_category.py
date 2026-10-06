from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0002_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="category",
            field=models.CharField(
                choices=[
                    ("asosiy", "Asosiy"),
                    ("milliy", "Milliy Sertifikat"),
                    ("attestatsiya", "Attestatsiya"),
                    ("sat", "SAT"),
                ],
                default="asosiy",
                max_length=20,
                verbose_name="Toifa",
            ),
        ),
    ]
