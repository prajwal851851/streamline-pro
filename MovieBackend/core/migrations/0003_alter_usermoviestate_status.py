from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_seed_movies"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usermoviestate",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[("watching", "Watching"), ("watched", "Watched")],
                default=None,
                max_length=16,
                null=True,
            ),
        ),
    ]

