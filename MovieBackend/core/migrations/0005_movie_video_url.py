from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_otp"),
    ]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="video_url",
            field=models.URLField(blank=True),
        ),
    ]

