# Learning Pathway 🎓

A professional educational platform with AI-powered personalized learning recommendations and automated quiz generation.

## ✨ Features

- **🤖 AI-Powered Learning**: Personalized study recommendations based on learning style
- **📝 Smart Study Plans**: Create and manage custom study plans
- **🎯 Automated Quizzes**: AI-generated quizzes tailored to your topics
- **👤 User Profiles**: Track learning style, goals, and progress
- **📊 Dashboard**: Beautiful dashboard with stats and recommendations
- **🎨 Modern UI**: Professional design with smooth animations

## 🚀 Technology Stack

- **Backend**: Django 5.2.7
- **Database**: PostgreSQL
- **AI**: Google Gemini API (Free tier - 60 requests/minute)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Custom session-based auth

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL
- Google Gemini API Key (free from Google AI Studio)

## 🔧 Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Procrastinators
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Main Dependencies:**
- Django 5.2.7
- Google Gemini AI (`google-generativeai`)
- PostgreSQL adapter (`psycopg2`)
- Environment management (`python-dotenv`)
- Database URL parsing (`dj-database-url`)
- Image processing (`pillow`)

### 4. Get Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

**Note**: Gemini API is completely free with 60 requests per minute limit that refreshes every 60 seconds.

### 5. Configure Environment Variables

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/your_database
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser!

## 🎯 User Guide

### Registration
1. Go to `/register/`
2. Fill in your details
3. **Select your learning style**:
   - **Visual**: Learn through images, diagrams, videos
   - **Auditory**: Learn through listening, discussions
   - **Kinesthetic**: Learn through hands-on activities
   - **Reading/Writing**: Learn through text and notes
4. **Describe your learning goals** (at least 10 characters)

### AI-Powered Features

Once registered, you'll see:

1. **Personalized Study Techniques**: AI recommends techniques matching your learning style
2. **Curated Resources**: AI suggests videos, articles, or hands-on projects based on your preferences
3. **Time Allocation**: AI creates a daily study schedule
4. **Learning Milestones**: Track your progress with AI-generated goals
5. **Pro Tips**: Learning style-specific advice

### Creating Study Plans
1. Click "Create Study Plan" from the dashboard
2. AI will generate recommendations based on:
   - Your learning style
   - Your stated goals
   - The topic you're studying

### Quiz Generation (Coming Soon)
- Automated quizzes based on study plan topics
- Difficulty levels: Easy, Medium, Hard
- AI-powered explanations for each answer

## 📁 Project Structure

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

## 🤖 AI Service Features

The `core/ai_service.py` module provides:

### `generate_study_recommendations(learning_style, goals, topic=None)`
Returns personalized recommendations including:
- Study techniques tailored to learning style
- Recommended resources (videos, articles, practice)
- Time allocation (daily minutes and breakdown)
- Learning milestones
- Pro tips

### `generate_quiz(topic, difficulty, num_questions, learning_objective=None)`
Generates quizzes with:
- Multiple choice questions
- Correct answers with explanations
- Difficulty matching (easy/medium/hard)
- Educational focus

### `analyze_progress(quiz_results, learning_style)`
Analyzes performance and provides:
- Overall performance assessment
- Strengths and weaknesses
- Personalized recommendations
- Focus areas
- Encouragement messages

### `suggest_resources(topic, learning_style, resource_type)`
Curates learning resources:
- Matches learning style preferences
- Various resource types (video/article/practice/course/book)
- Estimated completion time
- Difficulty levels

## 🎨 Design Features

- **Modern Gradients**: Purple, pink, and blue color schemes
- **Smooth Animations**: Float, shimmer, bounce effects
- **Humanoid Mascot**: Friendly student character on login page
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Professional Typography**: Clean, readable fonts
- **Card-Based Layout**: Beautiful component design

## 🔒 Security Notes

⚠️ **Development Mode**: This project currently uses:
- Plain text password storage (NOT for production)
- Session-based authentication
- Debug mode enabled

For production deployment, please:
- Use Django's built-in password hashing
- Enable HTTPS
- Set `DEBUG = False`
- Configure proper secret keys
- Use environment-specific settings

## 📝 API Rate Limits

**Google Gemini Free Tier**:
- ✅ 60 requests per minute
- ✅ Refreshes every 60 seconds
- ✅ Completely free forever
- ✅ No credit card required

## 🐛 Troubleshooting

### AI Recommendations Not Showing
1. Check your `.env` file has `GEMINI_API_KEY` set
2. Verify API key is valid at [Google AI Studio](https://makersuite.google.com)
3. Check console for error messages
4. Ensure you selected a learning style during registration

### Database Connection Issues
1. Verify PostgreSQL is running
2. Check `DATABASE_URL` in `.env` file
3. Ensure database exists: `createdb your_database`

### Migration Errors
```bash
# Reset migrations (development only!)
python manage.py migrate authentication zero
python manage.py migrate studyplan zero
python manage.py makemigrations
python manage.py migrate
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

- Google Gemini API for AI-powered features
- Django framework
- Modern CSS design patterns
- Educational psychology research on learning styles

---

**Made with ❤️ for learners everywhere!**
