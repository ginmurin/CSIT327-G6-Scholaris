from django.db import migrations
from django.contrib.auth.hashers import make_password


def hash_passwords(apps, schema_editor):
    User = apps.get_model('authentication', 'User')
    for user in User.objects.all():
        # Check if password is already hashed (starts with algorithm identifier)
        if not user.password.startswith('pbkdf2_'):
            user.password = make_password(user.password)
            user.save(update_fields=['password'])


def reverse_hash_passwords(apps, schema_editor):
    # Cannot reverse password hashing
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_alter_user_learningstyle'),
    ]

    operations = [
        migrations.RunPython(hash_passwords, reverse_hash_passwords),
    ]
