from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('year', models.PositiveIntegerField()),
                ('duration_minutes', models.PositiveIntegerField(default=0)),
                ('rating', models.CharField(blank=True, max_length=20)),
                ('genre', models.JSONField(blank=True, default=list)),
                ('image_url', models.URLField(blank=True)),
                ('match_score', models.PositiveIntegerField(default=0)),
                ('is_new', models.BooleanField(default=False)),
                ('is_trending', models.BooleanField(default=False)),
                ('rank', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-is_trending', 'title'],
            },
        ),
        migrations.CreateModel(
            name='UserMovieState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('watching', 'Watching'), ('watched', 'Watched')], default='watching', max_length=16)),
                ('progress_percent', models.PositiveSmallIntegerField(default=0)),
                ('position_seconds', models.PositiveIntegerField(default=0)),
                ('in_my_list', models.BooleanField(default=False)),
                ('is_favorite', models.BooleanField(default=False)),
                ('is_downloaded', models.BooleanField(default=False)),
                ('last_watched_at', models.DateTimeField(auto_now=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='core.movie')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-last_watched_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='usermoviestate',
            unique_together={('user', 'movie')},
        ),
    ]

