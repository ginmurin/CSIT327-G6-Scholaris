# Learning Pathway 🎓

**A professional educational platform with AI-powered personalized learning recommendations and automated quiz generation.**

---

## ✨ Short Description

Learning Pathway is an AI-driven learning platform that offers personalized study recommendations, smart study plans, automated quiz generation, user profiles to track progress, and a beautiful dashboard with actionable insights. It's designed for learners who want a modern, adaptive, and motivating study experience.

---

## 🚀 Tech Stack

* **Backend:** Django 5.2.7
* **Database:** PostgreSQL
* **AI:** Google Gemini API (via `google-generativeai`)
* **Frontend:** HTML, CSS, JavaScript
* **Authentication:** Custom session-based auth
* **Other:** `psycopg2`, `python-dotenv`, `dj-database-url`, `pillow`

---

## 📋 Prerequisites

* Python 3.8+
* PostgreSQL
* Google Gemini API Key (create via Google AI Studio)

---

## 🔧 Setup & Run Instructions

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd Procrastinators
```

2. **Create a virtual environment (recommended)**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Obtain Google Gemini API Key**

* Visit Google AI Studio and create an API key.
* Paste it into your `.env` file (see next step).

5. **Configure environment variables**

```bash
cp .env.example .env
# then edit .env with your values
```

Example `.env` values:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/your_database
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Note:** The README documents use of the Gemini free tier (60 requests/minute). Verify your quota in Google AI Studio.

6. **Database migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Start development server**

```bash
python manage.py runserver
```

Open `http://localhost:8000` in your browser.

---

## 🎯 Usage Guide (Quick)

* **Register** at `/register/` and select a learning style (Visual, Auditory, Kinesthetic, Reading/Writing).
* **Create a Study Plan** from the dashboard — AI will generate tailored recommendations.
* **View Dashboard** for progress, milestones, and AI "Pro Tips".
* **Quiz Generation** (coming soon): AI-generated quizzes with difficulty levels and explanations.

---

## 🧠 AI Service (core/ai_service.py)

Key functions (examples):

* `generate_study_recommendations(learning_style, goals, topic=None)`
* `generate_quiz(topic, difficulty, num_questions, learning_objective=None)`
* `analyze_progress(quiz_results, learning_style)`
* `suggest_resources(topic, learning_style, resource_type)`

These functions interact with the Google Gemini API and return structured recommendations, quiz items, and analysis.

---

## 🎨 Design Highlights

* Modern gradients (purple / pink / blue)
* Smooth animations and responsive design
* Friendly humanoid mascot on the login page
* Card-based layout and professional typography

---

## 🔒 Security Notes

> **Development warnings**

* Plain text password storage is used in this demo (do **not** use in production).
* `DEBUG = True` in development.

**For production:**

* Use Django's password hashing and authentication framework
* Enable HTTPS
* Set `DEBUG = False`
* Store secrets in a secure vault or environment variables
* Use environment-specific settings

---

## 🐛 Troubleshooting

**AI Recommendations Not Showing**

1. Check `.env` contains `GEMINI_API_KEY`.
2. Verify API key in Google AI Studio.
3. Inspect console logs for errors.
4. Ensure learning style selected during registration.

**Database Connection Issues**

1. Ensure PostgreSQL is running.
2. Check `DATABASE_URL` in `.env`.
3. Create the database: `createdb your_database`.

**Migration Issues (development only)**

```bash
python manage.py migrate authentication zero
python manage.py migrate studyplan zero
python manage.py makemigrations
python manage.py migrate
```

---

## 📁 Project Structure (overview)

```
Procrastinators/
├── authentication/          # User authentication & AI features
│   ├── models.py           # User model with learning profile
│   ├── forms.py            # Registration with required fields
│   ├── views.py            # Auth views
│   ├── templates/          # HTML templates
│   └── static/             # CSS with modern designs
├── studyplan/              # Study plan management
│   ├── models.py           # StudyPlan model
│   ├── views.py            # CRUD operations
│   └── templates/          # Study plan pages
├── core/                   # Project settings
│   ├── settings.py         # Django configuration
│   ├── urls.py             # Main URL routing
│   └── ai_service.py       # 🤖 AI Service (Gemini integration)
└── manage.py               # Django management script
```

---

## 👥 Team Members

* **Product Owner (PO):** Jeff Lloyd Seloterio
* **Business Analyst (BA):** Andre Jay Sarraga
* **Scrum Master:** Tycoon A. Sebellita
* **Lead Developer:** John Emmanuel S. Sevilla
* **Front End:** Kurt Jusam K. Soco
* **Back End:** Brye Kane L. Sy

---

## 📝 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

* Google Gemini API
* Django framework
* Educational psychology research on learning styles

**Made with ❤️ for learners everywhere!**
