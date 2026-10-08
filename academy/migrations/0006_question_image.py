from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academy", "0005_course_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="image_data",
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="question",
            name="image_type",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
    ]
