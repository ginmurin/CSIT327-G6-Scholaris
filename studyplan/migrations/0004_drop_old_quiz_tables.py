# Generated migration to drop old quiz tables from previous implementation

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('studyplan', '0003_alter_studyplan_estimated_hours_per_week_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Drop tables in reverse order of dependencies
            sql="""
                DROP TABLE IF EXISTS "quizanswer" CASCADE;
                DROP TABLE IF EXISTS "quizattempt" CASCADE;
                DROP TABLE IF EXISTS "quizquestion" CASCADE;
                DROP TABLE IF EXISTS "quiz" CASCADE;
                DROP TABLE IF EXISTS "Progress" CASCADE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
