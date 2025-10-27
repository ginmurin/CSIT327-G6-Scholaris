# Migration to ensure Django auth tables exist

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0012_hash_existing_passwords'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Create auth_permission table if it doesn't exist
                CREATE TABLE IF NOT EXISTS auth_permission (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    content_type_id INTEGER NOT NULL REFERENCES django_content_type(id) ON DELETE CASCADE,
                    codename VARCHAR(100) NOT NULL,
                    UNIQUE (content_type_id, codename)
                );

                -- Create auth_group table if it doesn't exist
                CREATE TABLE IF NOT EXISTS auth_group (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL UNIQUE
                );

                -- Create auth_group_permissions table if it doesn't exist
                CREATE TABLE IF NOT EXISTS auth_group_permissions (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
                    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
                    UNIQUE (group_id, permission_id)
                );

                -- Create auth_user table if it doesn't exist
                CREATE TABLE IF NOT EXISTS auth_user (
                    id SERIAL PRIMARY KEY,
                    password VARCHAR(128) NOT NULL,
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    first_name VARCHAR(150) NOT NULL DEFAULT '',
                    last_name VARCHAR(150) NOT NULL DEFAULT '',
                    email VARCHAR(254) NOT NULL DEFAULT '',
                    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );

                -- Create auth_user_groups table if it doesn't exist
                CREATE TABLE IF NOT EXISTS auth_user_groups (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                    group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
                    UNIQUE (user_id, group_id)
                );

                -- Create auth_user_user_permissions table if it doesn't exist
                CREATE TABLE IF NOT EXISTS auth_user_user_permissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                    permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
                    UNIQUE (user_id, permission_id)
                );
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
                DROP TABLE IF EXISTS auth_user_groups CASCADE;
                DROP TABLE IF EXISTS auth_user CASCADE;
                DROP TABLE IF EXISTS auth_group_permissions CASCADE;
                DROP TABLE IF EXISTS auth_group CASCADE;
                DROP TABLE IF EXISTS auth_permission CASCADE;
            """,
        ),
    ]
