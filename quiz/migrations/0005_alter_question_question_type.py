# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_quiz_is_public_quizattempt_points_earned'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(
                choices=[
                    ('multiple_choice', 'Multiple Choice'),
                    ('checkboxes', 'Checkboxes'),
                    ('dropdown', 'Dropdown'),
                    ('true_false', 'True/False'),
                ],
                default='multiple_choice',
                max_length=20
            ),
        ),
    ]
