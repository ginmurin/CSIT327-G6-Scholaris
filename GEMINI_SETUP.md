# 🤖 Google Gemini AI Setup Guide

## Quick Setup (5 minutes)

### Step 1: Get Your Free API Key

1. **Visit Google AI Studio**
   - Go to: https://makersuite.google.com/app/apikey
   - Sign in with your Google account (any Gmail account works)

2. **Create API Key**
   - Click the blue **"Create API Key"** button
   - Choose **"Create API key in new project"**
   - Your API key will be generated instantly
   - Click **"Copy"** to copy the key to clipboard

3. **Save Your API Key**
   - The key looks like: `AIzaSyD...` (39 characters)
   - Keep it safe - you'll need it in the next step

### Step 2: Add API Key to Your Project

1. **Open your `.env` file** in the project root
   ```
   Procrastinators/.env
   ```

2. **Add the API key**
   ```env
   GEMINI_API_KEY=AIzaSyD_YOUR_ACTUAL_API_KEY_HERE
   ```
   Replace `AIzaSyD_YOUR_ACTUAL_API_KEY_HERE` with your actual key

3. **Save the file**

### Step 3: Test It!

1. **Start your Django server**
   ```bash
   python manage.py runserver
   ```

2. **Register a new account** at `http://localhost:8000/register/`
   - Fill in your details
   - **Important**: Select a learning style and add goals (required!)

3. **Check the Dashboard** at `http://localhost:8000/home/`
   - You should see AI-powered recommendations! 🎉

---

## 📊 API Limits (Free Tier)

✅ **60 requests per minute**
- Refreshes every 60 seconds
- Perfect for development and small apps

✅ **Completely FREE Forever**
- No credit card required
- No trial period that expires
- Google's commitment to developers

✅ **What counts as a request?**
- Each AI recommendation generation = 1 request
- Each quiz generation = 1 request
- Each progress analysis = 1 request

---

## 🎯 What the AI Does

### 1. Personalized Study Recommendations
Based on your learning style, the AI generates:
- **Study techniques** tailored to how you learn best
- **Resource recommendations** (videos for Visual learners, podcasts for Auditory, etc.)
- **Time allocation** suggestions (daily study schedule)
- **Learning milestones** to track progress
- **Pro tips** specific to your learning style

### 2. Quiz Generation (Coming Soon)
- Creates multiple-choice questions about any topic
- Adjusts difficulty (easy/medium/hard)
- Provides explanations for correct answers
- Focuses on learning objectives

### 3. Progress Analysis (Coming Soon)
- Analyzes quiz performance
- Identifies strengths and weaknesses
- Provides personalized improvement recommendations
- Encourages continued learning

---

## 🔧 Troubleshooting

### ❌ "AI Recommendations not showing"

**Check 1: API Key is set**
```bash
# Open .env file and verify:
GEMINI_API_KEY=AIzaSyD...  # Should be your actual key, not "your_gemini_api_key_here"
```

**Check 2: Restart the server**
```bash
# Stop the server (Ctrl+C)
# Start it again
python manage.py runserver
```

**Check 3: Learning style and goals are required**
- Go to `/register/` and create a new account
- Make sure you select a learning style from the dropdown
- Add learning goals (at least 10 characters)

**Check 4: Check the console for errors**
- Look for error messages in the terminal where Django is running
- Common error: `Invalid API key` → Get a new key from Google AI Studio

### ❌ "API key not valid"

1. Generate a **new API key** at https://makersuite.google.com/app/apikey
2. Delete the old one
3. Copy the new key to `.env` file
4. Restart Django server

### ❌ "Rate limit exceeded"

This means you've used all 60 requests in the last minute.

**Solution**: Wait 60 seconds, then try again.

**For development**: 
- Don't refresh the home page too quickly
- Each page load generates AI recommendations
- Consider caching recommendations (advanced)

---

## 💡 Pro Tips

### Tip 1: Cache Recommendations (Optional)
For production, consider caching AI recommendations to reduce API calls:
```python
# In views.py, check if user already has recommendations cached
# Only call AI service if cache is empty or expired
```

### Tip 2: Error Handling
The AI service has built-in fallbacks:
- If API fails, it returns basic recommendations
- Your app never breaks, even if API is down
- Users always get helpful content

### Tip 3: Monitor Usage
- Keep track of how many API calls you make
- 60/minute is generous for most apps
- A typical user visit = 1-2 API calls

### Tip 4: Customize Prompts
Edit `core/ai_service.py` to customize how the AI generates recommendations:
- Change the prompt structure
- Add more specific instructions
- Request different output formats

---

## 🚀 Next Steps

1. ✅ **Test the dashboard** - See AI recommendations in action
2. ✅ **Create a study plan** - See how AI integrates with your goals
3. ✅ **Try different learning styles** - Create test accounts to see different recommendations
4. 🔜 **Implement quiz generation** - Use the `generate_quiz()` function
5. 🔜 **Add progress tracking** - Use the `analyze_progress()` function

---

## 📚 Learn More

- **Google Gemini API Docs**: https://ai.google.dev/docs
- **Rate Limits**: https://ai.google.dev/pricing
- **Best Practices**: https://ai.google.dev/docs/best_practices

---

**Need help?** Check the console output for detailed error messages!

**Happy Learning! 🎓**
