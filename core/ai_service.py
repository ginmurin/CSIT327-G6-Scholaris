import google.generativeai as genai
from django.conf import settings
import json

genai.configure(api_key=settings.GEMINI_API_KEY)
# Use the correct model name from Google AI Studio
model = genai.GenerativeModel('gemini-2.5-flash-lite')


class LearningAIService:
    
    @staticmethod
    def generate_study_recommendations(learning_style, goals, topic=None):
        prompt = f"""
        You are an expert educational advisor. Create personalized study recommendations for a student with the following profile:
        
        Learning Style: {learning_style}
        Goals: {goals}
        {f'Current Topic: {topic}' if topic else ''}
        
        Please provide recommendations in the following JSON format:
        {{
            "study_techniques": ["technique1", "technique2", "technique3"],
            "recommended_resources": [
                {{"type": "video", "title": "resource name", "description": "why it fits their learning style"}},
                {{"type": "article", "title": "resource name", "description": "why it's helpful"}},
                {{"type": "practice", "title": "resource name", "description": "hands-on activity"}}
            ],
            "time_allocation": {{
                "daily_minutes": 60,
                "breakdown": {{"theory": 40, "practice": 60}}
            }},
            "milestones": ["milestone1", "milestone2", "milestone3"],
            "tips": ["tip1", "tip2", "tip3"]
        }}
        
        Make sure recommendations match their {learning_style} learning style:
        - Visual: Videos, diagrams, infographics, mind maps
        - Auditory: Podcasts, lectures, discussions, audio books
        - Kinesthetic: Hands-on projects, experiments, practice exercises
        - Reading/Writing: Articles, books, note-taking, written summaries
        """
        
        try:
            response = model.generate_content(prompt)
            # Parse the JSON response
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            recommendations = json.loads(result_text.strip())
            return recommendations
        except Exception as e:
            # Return a basic fallback if AI fails
            return {
                "study_techniques": [
                    f"Use {learning_style.lower()}-focused learning methods",
                    "Practice regularly with spaced repetition",
                    "Set specific, measurable goals"
                ],
                "recommended_resources": [
                    {"type": "general", "title": "Start with fundamentals", "description": "Build a strong foundation"}
                ],
                "time_allocation": {
                    "daily_minutes": 60,
                    "breakdown": {"theory": 40, "practice": 60}
                },
                "milestones": ["Complete basic concepts", "Practice intermediate topics", "Master advanced material"],
                "tips": [f"Focus on {learning_style.lower()} learning methods", "Stay consistent", "Track your progress"],
                "error": str(e)
            }
    
    @staticmethod
    def generate_quiz(topic, difficulty="medium", num_questions=5, learning_objective=None):
        prompt = f"""
        Create a {difficulty} difficulty quiz about: {topic}
        {f'Learning Objective: {learning_objective}' if learning_objective else ''}
        
        Generate exactly {num_questions} multiple choice questions.
        
        Return the quiz in this JSON format:
        {{
            "title": "{topic} Quiz",
            "difficulty": "{difficulty}",
            "questions": [
                {{
                    "question": "Question text here?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": "Why this answer is correct and what students should learn"
                }}
            ]
        }}
        
        Important:
        - correct_answer should be the index (0-3) of the correct option
        - Make questions educational and relevant to {topic}
        - Provide clear explanations for learning
        - Difficulty should match {difficulty} level
        """
        
        try:
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            quiz = json.loads(result_text.strip())
            return quiz
        except Exception as e:
            # Return a basic fallback quiz if AI fails
            return {
                "title": f"{topic} Quiz",
                "difficulty": difficulty,
                "questions": [
                    {
                        "question": f"What is an important concept in {topic}?",
                        "options": [
                            "Concept A",
                            "Concept B", 
                            "Concept C",
                            "Concept D"
                        ],
                        "correct_answer": 0,
                        "explanation": "This is a placeholder question. Please try again."
                    }
                ],
                "error": str(e)
            }
    
    @staticmethod
    def analyze_progress(quiz_results, learning_style):
        prompt = f"""
        Analyze this student's quiz performance:
        
        Learning Style: {learning_style}
        Quiz Results: {json.dumps(quiz_results)}
        
        Provide analysis in JSON format:
        {{
            "overall_performance": "Good/Needs Improvement/Excellent",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "recommendations": [
                "specific recommendation 1",
                "specific recommendation 2",
                "specific recommendation 3"
            ],
            "focus_areas": ["area1", "area2"],
            "encouragement": "motivational message"
        }}
        
        Consider their {learning_style} learning style in recommendations.
        """
        
        try:
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            analysis = json.loads(result_text.strip())
            return analysis
        except Exception as e:
            return {
                "overall_performance": "Unable to analyze",
                "strengths": ["Completed the quiz"],
                "weaknesses": [],
                "recommendations": ["Keep practicing", "Review the material"],
                "focus_areas": ["Continue learning"],
                "encouragement": "Great effort! Keep up the good work!",
                "error": str(e)
            }
    
    @staticmethod
    def suggest_resources(topic, learning_style, resource_type="all", context=None):
        # Build enhanced prompt with full context
        context_info = ""
        if context:
            # Use learning style from context if provided, otherwise use parameter
            actual_learning_style = context.get('learning_style', learning_style)
            
            context_info = f"""
        
        STUDY PLAN DETAILS:
        - Learning Style: {actual_learning_style} (CRITICAL: Prioritize {actual_learning_style}-friendly resources!)
        - Study Plan Description: {context.get('description', 'Not provided')}
        - Learning Objective: {context.get('learning_objective', 'Not specified')}
        - Preferred Resource Types: {context.get('preferred_resources', 'Any type')}
        - Study Duration: {context.get('duration', 'Not specified')}
        - Time Commitment: {context.get('hours_per_week', 'Flexible')}
        
        IMPORTANT: Recommend resources that specifically help achieve the Learning Objective stated above.
        Focus on resources that match:
        1. Their {actual_learning_style} learning style (MOST IMPORTANT)
        2. The specific learning objective they want to achieve
        3. Their preferred resource formats
        4. Their study timeline and time commitment
        """
            learning_style = actual_learning_style  # Update to use context value
        
        prompt = f"""
        You are a learning resource curator. Find 7 REAL, SPECIFIC learning resources with DIRECT URLs for:
        
        Topic: {topic}
        Learning Style: {learning_style}
        Resource Type: {resource_type}
        {context_info}
        
        CRITICAL REQUIREMENTS:
        1. Provide DIRECT URLs to specific resources (NOT search pages, NOT "youtube.com/results")
        2. Each URL must be a real, working link to a specific video, article, course, or interactive tool
        3. Examples of GOOD URLs:
           - https://www.youtube.com/watch?v=rfscVS0vtbw (specific YouTube video)
           - https://www.freecodecamp.org/news/learn-python-free-python-courses-for-beginners/
           - https://react.dev/learn
           - https://www.w3schools.com/python/
           - https://www.coursera.org/learn/machine-learning
        4. NEVER use search result pages like "youtube.com/results?search_query="
        
        Return ONLY valid JSON array (no extra text):
        [
            {{
                "title": "Exact name of the resource",
                "type": "video",
                "url": "https://direct-url-to-specific-resource.com",
                "description": "Clear description of what learner will gain",
                "estimated_time": "2 hours",
                "difficulty": "beginner",
                "platform": "YouTube",
                "is_free": true
            }}
        ]
        
        Resource types: video, article, interactive, course, practice, documentation
        Platforms: YouTube, freeCodeCamp, MDN, W3Schools, Coursera, Khan Academy, Udemy, Codecademy, Real Python, etc.
        
        For {learning_style} learners, prioritize:
        - Visual: YouTube tutorials with visuals, animated explanations
        - Auditory: Video lectures with clear narration, podcasts
        - Kinesthetic: Interactive coding platforms (Codecademy, freeCodeCamp), hands-on projects
        - Reading/Writing: Documentation, blog tutorials, written guides
        
        Return ONLY the JSON array, no markdown, no extra text.
        """
        
        try:
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean markdown formatting
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # Parse JSON
            resources = json.loads(result_text)
            
            # Validate that we got real URLs (not search pages)
            valid_resources = []
            for r in resources:
                url = r.get('url', '')
                # Filter out search pages and invalid URLs
                if url and 'results?search_query=' not in url and 'search?q=' not in url:
                    valid_resources.append(r)
            
            if valid_resources:
                return valid_resources
            else:
                # If AI gave us search pages, use curated fallback
                return LearningAIService._get_curated_fallback_resources(topic, learning_style)
                
        except Exception as e:
            # Use curated fallback resources
            return LearningAIService._get_curated_fallback_resources(topic, learning_style)
    
    @staticmethod
    def _get_curated_fallback_resources(topic, learning_style):
        # Extensive curated resource database with REAL URLs
        curated_resources = {
            "python": [
                {"title": "Python Full Course - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "4 hours", "is_free": True, "description": "Complete Python tutorial for beginners"},
                {"title": "Python Official Tutorial", "type": "article", "url": "https://docs.python.org/3/tutorial/", "platform": "Python.org", "difficulty": "beginner", "estimated_time": "3 hours", "is_free": True, "description": "Official Python documentation and tutorial"},
                {"title": "Real Python Tutorials", "type": "article", "url": "https://realpython.com/", "platform": "Real Python", "difficulty": "intermediate", "estimated_time": "Varies", "is_free": True, "description": "In-depth Python tutorials and articles"},
                {"title": "Python for Everybody - Coursera", "type": "course", "url": "https://www.coursera.org/specializations/python", "platform": "Coursera", "difficulty": "beginner", "estimated_time": "8 months", "is_free": True, "description": "University of Michigan's Python course"},
                {"title": "Automate the Boring Stuff", "type": "interactive", "url": "https://automatetheboringstuff.com/", "platform": "Online Book", "difficulty": "beginner", "estimated_time": "Self-paced", "is_free": True, "description": "Practical Python programming"},
                {"title": "LeetCode Python Practice", "type": "practice", "url": "https://leetcode.com/problemset/", "platform": "LeetCode", "difficulty": "intermediate", "estimated_time": "Ongoing", "is_free": True, "description": "Coding challenges in Python"},
                {"title": "Python Crash Course", "type": "video", "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "6 hours", "is_free": True, "description": "Programming with Mosh Python tutorial"},
            ],
            "javascript": [
                {"title": "JavaScript Full Course - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "3 hours", "is_free": True, "description": "Complete JavaScript tutorial"},
                {"title": "MDN JavaScript Guide", "type": "article", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "platform": "MDN", "difficulty": "all", "estimated_time": "10 hours", "is_free": True, "description": "Comprehensive JavaScript documentation"},
                {"title": "JavaScript30", "type": "practice", "url": "https://javascript30.com/", "platform": "JavaScript30", "difficulty": "intermediate", "estimated_time": "30 days", "is_free": True, "description": "30 projects in 30 days"},
                {"title": "Eloquent JavaScript", "type": "article", "url": "https://eloquentjavascript.net/", "platform": "Online Book", "difficulty": "beginner", "estimated_time": "Self-paced", "is_free": True, "description": "Free interactive JavaScript book"},
                {"title": "freeCodeCamp JavaScript", "type": "interactive", "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "platform": "freeCodeCamp", "difficulty": "beginner", "estimated_time": "300 hours", "is_free": True, "description": "Interactive JavaScript curriculum"},
                {"title": "JavaScript Info Tutorial", "type": "article", "url": "https://javascript.info/", "platform": "JavaScript.info", "difficulty": "beginner", "estimated_time": "Self-paced", "is_free": True, "description": "Modern JavaScript tutorial"},
            ],
            "web development": [
                {"title": "Full Stack Web Development - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=nu_pCVPKzTk", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "4 hours", "is_free": True, "description": "HTML, CSS, JavaScript tutorial"},
                {"title": "freeCodeCamp Curriculum", "type": "interactive", "url": "https://www.freecodecamp.org/learn/", "platform": "freeCodeCamp", "difficulty": "beginner", "estimated_time": "1800 hours", "is_free": True, "description": "Complete web development curriculum"},
                {"title": "The Odin Project", "type": "course", "url": "https://www.theodinproject.com/", "platform": "Odin Project", "difficulty": "beginner", "estimated_time": "1000 hours", "is_free": True, "description": "Free full-stack curriculum"},
                {"title": "W3Schools Tutorials", "type": "interactive", "url": "https://www.w3schools.com/", "platform": "W3Schools", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Interactive web tutorials"},
                {"title": "MDN Web Docs", "type": "article", "url": "https://developer.mozilla.org/en-US/docs/Learn", "platform": "MDN", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Web development learning pathway"},
                {"title": "CSS-Tricks", "type": "article", "url": "https://css-tricks.com/", "platform": "CSS-Tricks", "difficulty": "intermediate", "estimated_time": "Ongoing", "is_free": True, "description": "CSS and web design articles"},
            ],
            "react": [
                {"title": "React Official Tutorial", "type": "article", "url": "https://react.dev/learn", "platform": "React.dev", "difficulty": "beginner", "estimated_time": "3 hours", "is_free": True, "description": "Official React documentation"},
                {"title": "React Course - Scrimba", "type": "interactive", "url": "https://scrimba.com/learn/learnreact", "platform": "Scrimba", "difficulty": "beginner", "estimated_time": "12 hours", "is_free": True, "description": "Interactive React course"},
                {"title": "Full React Course - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=bMknfKXIFA8", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "10 hours", "is_free": True, "description": "Comprehensive React tutorial"},
                {"title": "React for Beginners", "type": "video", "url": "https://www.youtube.com/watch?v=Ke90Tje7VS0", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "2 hours", "is_free": True, "description": "Programming with Mosh React course"},
                {"title": "freeCodeCamp React", "type": "interactive", "url": "https://www.freecodecamp.org/learn/front-end-development-libraries/", "platform": "freeCodeCamp", "difficulty": "intermediate", "estimated_time": "300 hours", "is_free": True, "description": "React certification course"},
            ],
            "data science": [
                {"title": "Data Science Full Course", "type": "video", "url": "https://www.youtube.com/watch?v=ua-CiDNNj30", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "12 hours", "is_free": True, "description": "Complete data science tutorial"},
                {"title": "Kaggle Learn", "type": "interactive", "url": "https://www.kaggle.com/learn", "platform": "Kaggle", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Interactive data science courses"},
                {"title": "Python for Data Science", "type": "course", "url": "https://www.coursera.org/learn/python-for-applied-data-science-ai", "platform": "Coursera", "difficulty": "beginner", "estimated_time": "5 weeks", "is_free": True, "description": "IBM's Python for Data Science"},
                {"title": "Data Analysis with Pandas", "type": "video", "url": "https://www.youtube.com/watch?v=vmEHCJofslg", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "1 hour", "is_free": True, "description": "Pandas tutorial for beginners"},
                {"title": "Google Data Analytics", "type": "course", "url": "https://www.coursera.org/professional-certificates/google-data-analytics", "platform": "Coursera", "difficulty": "beginner", "estimated_time": "6 months", "is_free": False, "description": "Google's professional certificate"},
            ],
            "machine learning": [
                {"title": "Machine Learning Course - Andrew Ng", "type": "course", "url": "https://www.coursera.org/learn/machine-learning", "platform": "Coursera", "difficulty": "intermediate", "estimated_time": "11 weeks", "is_free": True, "description": "Stanford's famous ML course"},
                {"title": "ML Crash Course - Google", "type": "interactive", "url": "https://developers.google.com/machine-learning/crash-course", "platform": "Google", "difficulty": "beginner", "estimated_time": "15 hours", "is_free": True, "description": "Google's ML crash course"},
                {"title": "Fast.ai Practical Deep Learning", "type": "course", "url": "https://course.fast.ai/", "platform": "Fast.ai", "difficulty": "intermediate", "estimated_time": "7 weeks", "is_free": True, "description": "Practical deep learning course"},
                {"title": "Machine Learning with Python", "type": "video", "url": "https://www.youtube.com/watch?v=7eh4d6sabA0", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "2 hours", "is_free": True, "description": "freeCodeCamp ML tutorial"},
                {"title": "Elements of AI", "type": "course", "url": "https://www.elementsofai.com/", "platform": "University of Helsinki", "difficulty": "beginner", "estimated_time": "30 hours", "is_free": True, "description": "Introduction to AI concepts"},
            ],
            "cooking": [
                {"title": "Basics with Babish - Cooking Techniques", "type": "video", "url": "https://www.youtube.com/watch?v=1WT35Jy5Ixw&list=PLopY4n17t8RD-xx0UdVqemiSa0sRfyX19", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Essential cooking techniques from Babish"},
                {"title": "Gordon Ramsay's Ultimate Cookery Course", "type": "video", "url": "https://www.youtube.com/watch?v=STS8SjQ93I8&list=PLjg7WfZf-CAHWqaEPNGqKN85TyR5xG2rz", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "20 episodes", "is_free": True, "description": "Cooking fundamentals from Gordon Ramsay"},
                {"title": "Budget Bytes - Recipes & Tutorials", "type": "article", "url": "https://www.budgetbytes.com/", "platform": "Budget Bytes", "difficulty": "beginner", "estimated_time": "Self-paced", "is_free": True, "description": "Budget-friendly recipes with step-by-step photos"},
                {"title": "Serious Eats - Cooking Techniques", "type": "article", "url": "https://www.seriouseats.com/", "platform": "Serious Eats", "difficulty": "intermediate", "estimated_time": "Ongoing", "is_free": True, "description": "Science-based cooking guides and recipes"},
                {"title": "America's Test Kitchen", "type": "video", "url": "https://www.youtube.com/c/AmericasTestKitchen", "platform": "YouTube", "difficulty": "intermediate", "estimated_time": "Varies", "is_free": True, "description": "Professional cooking techniques and recipes"},
                {"title": "Salt Fat Acid Heat Basics", "type": "video", "url": "https://www.youtube.com/watch?v=gqhg6dollars", "platform": "Netflix/YouTube", "difficulty": "beginner", "estimated_time": "4 hours", "is_free": True, "description": "Fundamental cooking elements explained"},
                {"title": "The Food Lab by Kenji López-Alt", "type": "article", "url": "https://www.seriouseats.com/the-food-lab", "platform": "Serious Eats", "difficulty": "intermediate", "estimated_time": "Self-paced", "is_free": True, "description": "Scientific approach to cooking"},
            ],
            "guitar": [
                {"title": "JustinGuitar Beginner Course", "type": "video", "url": "https://www.justinguitar.com/categories/beginner-guitar-course-grade-1", "platform": "JustinGuitar", "difficulty": "beginner", "estimated_time": "3 months", "is_free": True, "description": "Complete beginner guitar course"},
                {"title": "Marty Music - Guitar Basics", "type": "video", "url": "https://www.youtube.com/c/MartyMusic", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Easy guitar lessons and song tutorials"},
                {"title": "Guitar Lessons by GuitarZero2Hero", "type": "video", "url": "https://www.youtube.com/c/GuitarZero2Hero", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Step-by-step guitar tutorials"},
                {"title": "Ultimate Guitar - Tabs & Lessons", "type": "interactive", "url": "https://www.ultimate-guitar.com/", "platform": "Ultimate Guitar", "difficulty": "all", "estimated_time": "Ongoing", "is_free": True, "description": "Guitar tabs and chord charts"},
                {"title": "Fender Play Free Trial", "type": "course", "url": "https://www.fender.com/play", "platform": "Fender", "difficulty": "beginner", "estimated_time": "Self-paced", "is_free": False, "description": "Structured guitar learning path"},
            ],
            "drawing": [
                {"title": "Drawabox - Free Drawing Course", "type": "interactive", "url": "https://drawabox.com/", "platform": "Drawabox", "difficulty": "beginner", "estimated_time": "6 months", "is_free": True, "description": "Comprehensive drawing fundamentals"},
                {"title": "Proko - Figure Drawing", "type": "video", "url": "https://www.youtube.com/c/ProkoTV", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Professional figure drawing tutorials"},
                {"title": "Ctrl+Paint - Digital Painting", "type": "video", "url": "https://www.ctrlpaint.com/library", "platform": "Ctrl+Paint", "difficulty": "beginner", "estimated_time": "Self-paced", "is_free": True, "description": "Digital painting fundamentals"},
                {"title": "Draw a Box - Fundamentals", "type": "article", "url": "https://drawabox.com/lesson/0", "platform": "Drawabox", "difficulty": "beginner", "estimated_time": "50 hours", "is_free": True, "description": "Drawing basics and exercises"},
                {"title": "Skillshare Drawing Basics", "type": "course", "url": "https://www.skillshare.com/browse/drawing", "platform": "Skillshare", "difficulty": "beginner", "estimated_time": "Varies", "is_free": False, "description": "Structured drawing courses"},
            ],
            "fitness": [
                {"title": "Fitness Blender - Free Workouts", "type": "video", "url": "https://www.fitnessblender.com/", "platform": "Fitness Blender", "difficulty": "all", "estimated_time": "Varies", "is_free": True, "description": "Free workout videos for all levels"},
                {"title": "DAREBEE Workouts", "type": "interactive", "url": "https://darebee.com/", "platform": "DAREBEE", "difficulty": "all", "estimated_time": "Ongoing", "is_free": True, "description": "No-equipment workouts and programs"},
                {"title": "Chloe Ting Programs", "type": "video", "url": "https://www.chloeting.com/program", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "2-4 weeks", "is_free": True, "description": "Popular workout challenges"},
                {"title": "Nike Training Club", "type": "interactive", "url": "https://www.nike.com/ntc-app", "platform": "Nike", "difficulty": "all", "estimated_time": "Ongoing", "is_free": True, "description": "Free workout app with programs"},
                {"title": "Yoga with Adriene", "type": "video", "url": "https://www.youtube.com/c/yogawithadriene", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Beginner-friendly yoga sessions"},
            ],
            "language": [
                {"title": "Duolingo", "type": "interactive", "url": "https://www.duolingo.com/", "platform": "Duolingo", "difficulty": "beginner", "estimated_time": "Ongoing", "is_free": True, "description": "Gamified language learning"},
                {"title": "Language Transfer", "type": "video", "url": "https://www.languagetransfer.org/", "platform": "Language Transfer", "difficulty": "beginner", "estimated_time": "10-20 hours", "is_free": True, "description": "Audio language courses"},
                {"title": "Easy Languages YouTube", "type": "video", "url": "https://www.youtube.com/c/learnlanguages", "platform": "YouTube", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Street interviews in target languages"},
                {"title": "Anki Flashcards", "type": "interactive", "url": "https://apps.ankiweb.net/", "platform": "Anki", "difficulty": "all", "estimated_time": "Ongoing", "is_free": True, "description": "Spaced repetition flashcard system"},
                {"title": "italki - Language Exchange", "type": "interactive", "url": "https://www.italki.com/", "platform": "italki", "difficulty": "all", "estimated_time": "Ongoing", "is_free": False, "description": "Connect with native speakers"},
            ],
        }
        
        # Find matching resources
        topic_lower = topic.lower()
        matched_resources = []
        
        # Try to find exact or partial topic match
        for key, resources in curated_resources.items():
            if key in topic_lower or topic_lower in key:
                matched_resources = resources
                break
        
        # If no match found, provide general learning resources
        if not matched_resources:
            matched_resources = [
                {"title": "freeCodeCamp", "type": "interactive", "url": "https://www.freecodecamp.org/learn", "platform": "freeCodeCamp", "difficulty": "beginner", "estimated_time": "Varies", "is_free": True, "description": "Free coding curriculum"},
                {"title": "Khan Academy", "type": "interactive", "url": "https://www.khanacademy.org/", "platform": "Khan Academy", "difficulty": "all", "estimated_time": "Varies", "is_free": True, "description": "Free courses on many topics"},
                {"title": "Coursera Free Courses", "type": "course", "url": "https://www.coursera.org/courses?query=free", "platform": "Coursera", "difficulty": "all", "estimated_time": "Varies", "is_free": True, "description": "University-level free courses"},
                {"title": "MIT OpenCourseWare", "type": "course", "url": "https://ocw.mit.edu/", "platform": "MIT", "difficulty": "advanced", "estimated_time": "Varies", "is_free": True, "description": "Free MIT course materials"},
                {"title": "YouTube EDU", "type": "video", "url": "https://www.youtube.com/edu", "platform": "YouTube", "difficulty": "all", "estimated_time": "Varies", "is_free": True, "description": "Educational videos"},
            ]
        
        # Sort by learning style preference
        if learning_style == "Visual":
            matched_resources.sort(key=lambda x: 0 if x['type'] == 'video' else 1)
        elif learning_style == "Auditory":
            matched_resources.sort(key=lambda x: 0 if x['type'] == 'video' else 1)
        elif learning_style == "Kinesthetic":
            matched_resources.sort(key=lambda x: 0 if x['type'] in ['interactive', 'practice'] else 1)
        elif learning_style == "Reading/Writing":
            matched_resources.sort(key=lambda x: 0 if x['type'] in ['article', 'course'] else 1)
        
        return matched_resources[:7]  # Return top 7
    
    @staticmethod
    def get_topic_specific_resources(topic, learning_style):
        # Common resource databases by topic
        resource_db = {
            "python": [
                {"title": "Python Full Course - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "platform": "YouTube", "difficulty": "beginner"},
                {"title": "Python Documentation", "type": "article", "url": "https://docs.python.org/3/tutorial/", "platform": "Python.org", "difficulty": "all levels"},
                {"title": "Real Python Tutorials", "type": "article", "url": "https://realpython.com/", "platform": "Real Python", "difficulty": "intermediate"},
                {"title": "LeetCode Python", "type": "practice", "url": "https://leetcode.com/problemset/all/?difficulty=EASY&page=1&topicSlugs=array", "platform": "LeetCode", "difficulty": "intermediate"},
            ],
            "javascript": [
                {"title": "JavaScript Tutorial - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg", "platform": "YouTube", "difficulty": "beginner"},
                {"title": "MDN JavaScript Guide", "type": "article", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "platform": "MDN", "difficulty": "all levels"},
                {"title": "JavaScript30", "type": "practice", "url": "https://javascript30.com/", "platform": "JavaScript30", "difficulty": "intermediate"},
                {"title": "Eloquent JavaScript (Free Book)", "type": "article", "url": "https://eloquentjavascript.net/", "platform": "Online Book", "difficulty": "beginner"},
            ],
            "web development": [
                {"title": "Web Development Full Course", "type": "video", "url": "https://www.youtube.com/watch?v=nu_pCVPKzTk", "platform": "YouTube", "difficulty": "beginner"},
                {"title": "FreeCodeCamp Curriculum", "type": "interactive", "url": "https://www.freecodecamp.org/learn/", "platform": "freeCodeCamp", "difficulty": "beginner"},
                {"title": "W3Schools Tutorials", "type": "interactive", "url": "https://www.w3schools.com/", "platform": "W3Schools", "difficulty": "beginner"},
                {"title": "The Odin Project", "type": "course", "url": "https://www.theodinproject.com/", "platform": "Odin Project", "difficulty": "beginner"},
            ],
            "react": [
                {"title": "React Course - Scrimba", "type": "interactive", "url": "https://scrimba.com/learn/learnreact", "platform": "Scrimba", "difficulty": "beginner"},
                {"title": "React Official Tutorial", "type": "article", "url": "https://react.dev/learn", "platform": "React.dev", "difficulty": "beginner"},
                {"title": "Full React Course - FreeCodeCamp", "type": "video", "url": "https://www.youtube.com/watch?v=bMknfKXIFA8", "platform": "YouTube", "difficulty": "beginner"},
            ],
            "data science": [
                {"title": "Data Science Full Course", "type": "video", "url": "https://www.youtube.com/watch?v=ua-CiDNNj30", "platform": "YouTube", "difficulty": "beginner"},
                {"title": "Kaggle Learn", "type": "interactive", "url": "https://www.kaggle.com/learn", "platform": "Kaggle", "difficulty": "beginner"},
                {"title": "DataCamp Free Courses", "type": "interactive", "url": "https://www.datacamp.com/courses", "platform": "DataCamp", "difficulty": "beginner"},
            ],
            "machine learning": [
                {"title": "Machine Learning Course - Andrew Ng", "type": "course", "url": "https://www.coursera.org/learn/machine-learning", "platform": "Coursera", "difficulty": "intermediate"},
                {"title": "ML Crash Course - Google", "type": "interactive", "url": "https://developers.google.com/machine-learning/crash-course", "platform": "Google", "difficulty": "beginner"},
                {"title": "Fast.ai Practical Deep Learning", "type": "course", "url": "https://course.fast.ai/", "platform": "Fast.ai", "difficulty": "intermediate"},
            ],
        }
        
        # Find matching resources
        topic_lower = topic.lower()
        matching_resources = []
        
        for key, resources in resource_db.items():
            if key in topic_lower or topic_lower in key:
                matching_resources = resources
                break
        
        # If no match, return general search resources
        if not matching_resources:
            matching_resources = [
                {"title": f"YouTube: {topic}", "type": "video", "url": f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+tutorial", "platform": "YouTube", "difficulty": "all"},
                {"title": f"FreeCodeCamp", "type": "interactive", "url": "https://www.freecodecamp.org/learn", "platform": "freeCodeCamp", "difficulty": "beginner"},
            ]
        
        # Filter by learning style preference
        if learning_style == "Visual":
            # Prioritize videos
            matching_resources.sort(key=lambda x: 0 if x['type'] == 'video' else 1)
        elif learning_style == "Auditory":
            # Prioritize videos with good audio explanation
            matching_resources.sort(key=lambda x: 0 if x['type'] == 'video' else 1)
        elif learning_style == "Kinesthetic":
            # Prioritize interactive/practice
            matching_resources.sort(key=lambda x: 0 if x['type'] in ['interactive', 'practice'] else 1)
        elif learning_style == "Reading/Writing":
            # Prioritize articles
            matching_resources.sort(key=lambda x: 0 if x['type'] == 'article' else 1)
        
        return matching_resources[:5]  # Return top 5

    @staticmethod
    def get_smart_resources(topic, learning_style, resource_type="all", limit=5, context=None):
        from resources.models import Resource
        from django.db.models import Q
        from django.db import connection
        
        try:
            # Ensure fresh database connection
            connection.ensure_connection()
            
            # Step 1: Query database for existing resources
            query = Q(topic__icontains=topic)
            
            if resource_type != "all":
                query &= Q(resource_type=resource_type)
            
            # Get existing resources, ordered by LEAST recommended first (to diversify)
            existing_resources = list(Resource.objects.filter(query).order_by('times_recommended')[:limit * 2])
            
            # Step 2: If we have enough diverse resources, use them
            if len(existing_resources) >= limit:
                # Mix of least and most recommended for diversity
                selected_resources = []
                
                # Take some least recommended (new/underused resources)
                selected_resources.extend(existing_resources[:limit // 2])
                
                # Take some most recommended (proven valuable resources)
                selected_resources.extend(Resource.objects.filter(query).order_by('-times_recommended')[:limit - len(selected_resources)])
                
                # Increment recommendation counts
                for resource in selected_resources:
                    resource.increment_recommendation_count()
                
                # Convert to dict format
                return [
                    {
                        "title": r.title,
                        "type": r.resource_type,
                        "url": r.url,
                        "description": r.description,
                        "platform": r.platform,
                        "difficulty": r.difficulty,
                        "estimated_time": r.estimated_time,
                        "is_free": r.is_free
                    }
                    for r in selected_resources
                ]
            
            # Step 3: Not enough in database, generate NEW resources via AI
            needed_count = limit - len(existing_resources)
            
            # Get ALL URLs already in database to avoid duplicates (not just for this topic)
            existing_urls = set(Resource.objects.all().values_list('url', flat=True))
            
            # Generate new resources via AI with full context
            try:
                new_resources_data = LearningAIService.suggest_resources(
                    topic, 
                    learning_style, 
                    resource_type,
                    context=context  # Pass the rich context
                )
                
                # Step 4: Save new resources to database (excluding duplicates)
                new_resources = []
                for resource_data in new_resources_data[:needed_count * 2]:  # Get extra in case of duplicates
                    resource_url = resource_data.get('url', '')
                    
                    # Skip if URL already exists in database
                    if resource_url and resource_url not in existing_urls:
                        try:
                            # Detect category from topic
                            category = Resource.detect_category_from_topic(topic)
                            
                            # Create new resource in database
                            resource = Resource.objects.create(
                                topic=topic,
                                title=resource_data.get('title', 'Untitled'),
                                url=resource_url,
                                description=resource_data.get('description', ''),
                                resource_type=resource_data.get('type', 'article'),
                                category=category,
                                difficulty=resource_data.get('difficulty', 'all'),
                                platform=resource_data.get('platform', 'Web'),
                                learning_style=learning_style,
                                estimated_time=resource_data.get('estimated_time', 'Varies'),
                                is_free=resource_data.get('is_free', True),
                                times_recommended=1  # First recommendation
                            )
                            new_resources.append(resource)
                            existing_urls.add(resource_url)
                            
                            if len(new_resources) >= needed_count:
                                break
                        except Exception as e:
                            # Silently skip duplicates, only print other errors
                            if 'duplicate key' not in str(e).lower():
                                print(f"Error saving resource: {e}")
                            continue
                
                # Combine existing and new resources
                all_resources = existing_resources + new_resources
                
                # Increment counts for existing resources
                for resource in existing_resources:
                    resource.increment_recommendation_count()
                
                # Return combined list
                return [
                    {
                        "title": r.title,
                        "type": r.resource_type,
                        "url": r.url,
                        "description": r.description,
                        "platform": r.platform,
                        "difficulty": r.difficulty,
                        "estimated_time": r.estimated_time if hasattr(r, 'estimated_time') else 'Varies',
                        "is_free": r.is_free if hasattr(r, 'is_free') else True
                    }
                    for r in all_resources[:limit]
                ]
                
            except Exception as e:
                # Fallback to existing resources if we have any, otherwise use curated
                if existing_resources:
                    for resource in existing_resources:
                        resource.increment_recommendation_count()
                    
                    return [
                        {
                            "title": r.title,
                            "type": r.resource_type,
                            "url": r.url,
                            "description": r.description,
                            "platform": r.platform,
                            "difficulty": r.difficulty,
                            "estimated_time": r.estimated_time,
                            "is_free": r.is_free
                        }
                        for r in existing_resources
                    ]
                else:
                    # No existing resources, use curated fallback
                    return LearningAIService._get_curated_fallback_resources(topic, learning_style)
        
        except Exception as e:
            # Database connection error - use fallback curated resources
            return LearningAIService._get_curated_fallback_resources(topic, learning_style)