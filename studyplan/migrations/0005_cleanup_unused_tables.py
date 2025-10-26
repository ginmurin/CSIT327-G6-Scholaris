# Migration to clean up unnecessary tables from database
# Note: We keep Django auth tables as they're required by Django admin

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('studyplan', '0004_drop_old_quiz_tables'),
    ]

    operations = [
        # No operations - Django auth tables are required
        # This migration is a placeholder for future cleanup
    ]
