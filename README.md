Procrastinators – Personalized Learning Pathway System

This project is a Django web application connected to a shared Supabase (PostgreSQL) database.

⚡ Every developer must:

Create their own virtual environment (.venv)

Create their own .env file with the shared Supabase DATABASE_URL

Never commit .venv or .env (already ignored in .gitignore)

🚀 Project Setup
1. Clone the Repository
git clone https://github.com/Dreee03/Procrastinators.git
cd Procrastinators


If you forked the repo:

git clone https://github.com/<your-username>/Procrastinators.git
cd Procrastinators

2. Create a Virtual Environment
python -m venv .venv


Activate it:

Windows (CMD/PowerShell):

.venv\Scripts\activate


Mac/Linux (bash/zsh):

source .venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt


(If requirements.txt doesn’t exist yet, install manually:)

pip install django "psycopg[binary]" dj-database-url python-dotenv

4. Create a .env File

At the root of the project (beside manage.py), create a file named .env:

DATABASE_URL=postgresql://postgres.tawjlgqpixwynqqdcjjj:<password>@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require


⚠️ Notes:

Use the shared Supabase password provided by the project owner.

Do NOT commit this file.

Every developer must add this file locally.

5. Apply Migrations

Run:

python manage.py migrate


This will create/update the necessary tables in the shared Supabase database.

6. Run the Development Server
python manage.py runserver


Visit: http://127.0.0.1:8000

📝 Contribution Workflow

Always create a new branch that starts with your GitHub username. Example:

git checkout -b ginmurin/django-setup


Push your branch to your fork:

git push -u origin ginmurin/django-setup


Open a Pull Request to main in the class repo.

✅ Notes

.venv/ and .env must never be committed (already in .gitignore).

Everyone shares one Supabase database. Changes made via migrations will affect all developers.

To stay in sync:

Pull the latest code

Run python manage.py migrate
