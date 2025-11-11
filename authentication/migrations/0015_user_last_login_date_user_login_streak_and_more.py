# Generated migration for user tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0014_remove_learningstyle'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_login_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='login_streak',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='session_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='total_app_time',
            field=models.IntegerField(default=0),
        ),
    ]
