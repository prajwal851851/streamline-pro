from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_alter_usermoviestate_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="OTP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254)),
                ("code", models.CharField(max_length=6)),
                ("purpose", models.CharField(choices=[("verify", "Verify Email"), ("reset", "Reset Password")], max_length=16)),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
            ],
        ),
        migrations.AddIndex(
            model_name="otp",
            index=models.Index(fields=["email", "purpose"], name="core_otp_email_7ae5f1_idx"),
        ),
    ]

