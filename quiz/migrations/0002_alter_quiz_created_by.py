# Generated migration to make created_by nullable for AI-generated quizzes

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def fix_invalid_creators(apps, schema_editor):
    """Set invalid created_by references to NULL"""
    # Use raw SQL to set invalid foreign keys to NULL
    schema_editor.execute(
        """
        UPDATE quiz 
        SET created_by_id = NULL 
        WHERE created_by_id NOT IN (SELECT id FROM auth_user)
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # First, drop the foreign key constraint
        migrations.RunSQL(
            sql='ALTER TABLE quiz DROP CONSTRAINT IF EXISTS quiz_created_by_id_428da3bc_fk_auth_user_id',
            reverse_sql='',
        ),
        
        # Clean up invalid data
        migrations.RunPython(fix_invalid_creators, migrations.RunPython.noop),
        
        # Now alter the field to allow NULL and recreate constraint
        migrations.AlterField(
            model_name='quiz',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='created_quizzes',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
