"""
Script to delete quiz app migration records from Django's migration history.
This allows us to recreate migrations cleanly after dropping the quiz tables.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.migrations.recorder import MigrationRecorder

def delete_quiz_migrations():
    """Delete all migration records for the quiz app."""
    try:
        # Get all quiz app migrations
        migrations = MigrationRecorder.Migration.objects.filter(app='quiz')
        count = migrations.count()
        
        if count == 0:
            print("No quiz migrations found in the database.")
            return
        
        print(f"Found {count} quiz migration record(s):")
        for migration in migrations:
            print(f"  - {migration.app}.{migration.name}")
        
        # Delete the migrations
        migrations.delete()
        print(f"\n✓ Successfully deleted {count} quiz migration record(s).")
        
    except Exception as e:
        print(f"✗ Error deleting migrations: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("Quiz Migration Cleanup Script")
    print("=" * 60)
    print()
    
    success = delete_quiz_migrations()
    
    print()
    if success:
        print("Next steps:")
        print("1. Delete the old migration file:")
        print("   del quiz\\migrations\\0001_initial.py")
        print("2. Create fresh migrations:")
        print("   python manage.py makemigrations quiz")
        print("3. Apply the migrations:")
        print("   python manage.py migrate quiz")
    else:
        print("Please fix the errors above and try again.")
    print()
