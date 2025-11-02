# Generated migration to remove learningstyle field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0013_create_auth_tables'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='learningstyle',
        ),
    ]
