from google import genai
from django.conf import settings
from django.core.cache import cache
from .prompt_loader import load_prompt
import json
import time
import logging

logger = logging.getLogger(__name__)
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Rate limiting configuration
MAX_REQUESTS_PER_MINUTE = 10
REQUEST_QUEUE_KEY = 'gemini_request_queue'
RATE_LIMIT_WINDOW = 60


def _get_request_queue():
    """Get and clean request queue from cache."""
    queue = cache.get(REQUEST_QUEUE_KEY, [])
    now = time.time()
    return [ts for ts in queue if now - ts < RATE_LIMIT_WINDOW]


def _wait_for_rate_limit():
    """Wait if we're at rate limit capacity."""
    queue = _get_request_queue()
    
    if len(queue) < MAX_REQUESTS_PER_MINUTE:
        queue.append(time.time())
        cache.set(REQUEST_QUEUE_KEY, queue, timeout=RATE_LIMIT_WINDOW + 10)
        return 0
    
    oldest_request = queue[0]
    wait_time = RATE_LIMIT_WINDOW - (time.time() - oldest_request) + 0.5
    
    if wait_time > 0:
        print(f"⏳ Rate limit: Waiting {wait_time:.1f}s...")
        time.sleep(wait_time)
    
    queue = _get_request_queue()
    queue.append(time.time())
    cache.set(REQUEST_QUEUE_KEY, queue, timeout=RATE_LIMIT_WINDOW + 10)
    return wait_time


def _call_ai_with_retry(model, prompt, max_retries=3, initial_wait=2):
    """Call Gemini AI with retry logic and rate limiting."""
    for attempt in range(max_retries):
        try:
            _wait_for_rate_limit()
            print(f"🤖 AI request attempt {attempt + 1}/{max_retries}")
            response = client.models.generate_content(model=model, contents=prompt)
            print(f"✅ AI request successful")
            return response.text
        except Exception as e:
            error_str = str(e)
            is_rate_limit = '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str
            is_last_attempt = attempt == max_retries - 1
            
            if is_rate_limit and not is_last_attempt:
                # Exponential backoff: 2s, 4s, 8s
                wait_time = initial_wait * (2 ** attempt)
                print(f"⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries})")
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue  # Continue to next iteration
            else:
                # Not a rate limit error, or last attempt - raise the exception
                print(f"❌ AI request failed: {error_str}")
                raise
    
    # If we get here, all retries failed
    raise Exception(f"All {max_retries} retry attempts failed")


class LearningAIService:
    
    @staticmethod
    def generate_study_recommendations(goals, topic=None):
        prompt = f"""
        You are an expert educational advisor. Create personalized study recommendations for a student with the following profile:
        
        Goals: {goals}
        {f'Current Topic: {topic}' if topic else ''}
        
        Please provide recommendations in the following JSON format:
        {{
            "study_techniques": ["technique1", "technique2", "technique3"],
            "recommended_resources": [
                {{"type": "video", "title": "resource name", "description": "why this resource helps"}},
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
        
        Include diverse resource types (videos, articles, interactive tools, practice exercises) to cater to different learning preferences.
        """
        
        try:
            # Use retry logic for AI API call
            result_text = _call_ai_with_retry(
                model='gemini-2.0-flash-exp',
                prompt=prompt,
                max_retries=3,
                initial_wait=2
            )
            result_text = result_text.strip()
            
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
                    "Use active learning methods",
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
                "tips": ["Focus on diverse learning methods", "Stay consistent", "Track your progress"],
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
            # Use retry logic for AI API call
            result_text = _call_ai_with_retry(
                model='gemini-2.0-flash-exp',
                prompt=prompt,
                max_retries=3,
                initial_wait=2
            )
            result_text = result_text.strip()
            
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
    def analyze_progress(quiz_results):
        prompt = f"""
        Analyze this student's quiz performance:
        
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
        
        Provide actionable recommendations with diverse learning approaches.
        """
        
        try:
            # Use retry logic for AI API call
            result_text = _call_ai_with_retry(
                model='gemini-2.0-flash-exp',
                prompt=prompt,
                max_retries=3,
                initial_wait=2
            )
            result_text = result_text.strip()
            
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
    def suggest_resources(topic, resource_type="all", context=None, topic_category=None):
        # ===== CACHING LAYER =====
        # Generate cache key to avoid redundant AI calls for same topic
        cache_key = f"ai_resources:{topic}:{resource_type}:{topic_category or 'none'}"
        cached_resources = cache.get(cache_key)
        
        if cached_resources:
            print(f"✅ Using cached resources for topic: {topic}")
            return cached_resources
        
        print(f"🔄 Fetching fresh resources for topic: {topic} (not in cache)")
        
        # Build enhanced prompt with full context
        context_info = ""
        category_hint = ""
        
        if topic_category:
            # Map category to human-readable name for better AI prompts
            category_names = {
                'programming': 'Programming & Software Development',
                'web': 'Web Development',
                'mobile': 'Mobile Development',
                'data_science': 'Data Science & AI',
                'devops': 'DevOps & Cloud Computing',
                'business': 'Business Management',
                'finance': 'Finance & Accounting',
                'marketing': 'Marketing & Advertising',
                'leadership': 'Leadership & Management',
                'communication': 'Communication & Public Speaking',
                'language_spanish': 'Spanish Language Learning',
                'language_french': 'French Language Learning',
                'language_german': 'German Language Learning',
                'language_other': 'Other Languages',
                'biology': 'Biology',
                'chemistry': 'Chemistry',
                'physics': 'Physics',
                'mathematics': 'Mathematics',
                'art': 'Art & Design',
                'music': 'Music',
                'writing': 'Writing & Literature',
                'photography': 'Photography',
                'fitness': 'Fitness & Nutrition',
                'psychology': 'Psychology',
                'mindfulness': 'Mindfulness & Meditation',
                'other': 'General Learning',
            }
            category_name = category_names.get(topic_category, topic_category)
            category_hint = f"Topic Category: {category_name}\n"
        
        if context:
            context_info = f"""
        
        STUDY PLAN DETAILS:
        - Study Plan Description: {context.get('description', 'Not provided')}
        - Learning Objective: {context.get('learning_objective', 'Not specified')}
        - Preferred Resource Types: {context.get('preferred_resources', 'Any type')}
        - Study Duration: {context.get('duration', 'Not specified')}
        - Time Commitment: {context.get('hours_per_week', 'Flexible')}
        
        IMPORTANT: Recommend resources that specifically help achieve the Learning Objective stated above.
        Focus on resources that match:
        1. The specific learning objective they want to achieve
        2. Their preferred resource formats
        3. Their study timeline and time commitment
        """
        
        prompt = f"""
        You are a learning resource curator. Find 7 REAL, SPECIFIC learning resources with DIRECT URLs for:
        
        Topic: {topic}
        {category_hint}Resource Type: {resource_type}
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
        
        Provide diverse resource types to accommodate different learning preferences:
        - Videos with clear explanations and demonstrations
        - Interactive coding platforms for hands-on practice
        - Articles and documentation for in-depth reading
        - Courses for structured learning paths
        
        IMPORTANT: You must provide resources for ANY topic, not just programming. Examples:
        - For "Spanish Language": Duolingo, Babbel, FluentU lessons
        - For "Biology": Khan Academy biology, Amoeba Sisters videos, Campbell Biology resources
        - For "Music": Music Theory tutorials, Udemy music courses, YouTube piano lessons
        - For "Psychology": APA resources, Psychology Today, Coursera psychology courses
        - For "Fitness": Fitness.gov, Nike Training Club, Peloton classes
        - For "Art": Skillshare, Domestika, YouTube art tutorials
        
        Return ONLY the JSON array, no markdown, no extra text.
        """
        
        try:
            result_text = _call_ai_with_retry(
                model='gemini-2.0-flash-exp',
                prompt=prompt,
                max_retries=3,
                initial_wait=2
            )
            
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
                # Cache the valid resources for 24 hours
                cache.set(cache_key, valid_resources, timeout=86400)
                print(f"✅ Cached {len(valid_resources)} resources for topic: {topic}")
                return valid_resources
            else:
                # If AI gave us search pages, use curated fallback
                print(f"AI returned search pages for topic: {topic}, using fallback")
                fallback = LearningAIService._get_curated_fallback_resources(topic)
                # Cache fallback too
                cache.set(cache_key, fallback, timeout=86400)
                return fallback
                
        except Exception as e:
            # Use curated fallback resources
            print(f"Error generating AI resources for {topic}: {str(e)}")
            print(f"Falling back to curated resources for topic: {topic}")
            fallback = LearningAIService._get_curated_fallback_resources(topic)
            # Cache fallback too
            cache.set(cache_key, fallback, timeout=86400)
            return fallback
    
    @staticmethod
    def _get_curated_fallback_resources(topic):
        """
        Generate fallback resources dynamically based on topic.
        No hardcoded lists - just return structured search URLs and known platforms.
        """
        topic_encoded = topic.replace(' ', '+')
        
        return [
            {
                "title": f"{topic} - Khan Academy",
                "type": "video",
                "url": f"https://www.khanacademy.org/search?page_search_query={topic_encoded}",
                "platform": "Khan Academy",
                "difficulty": "beginner",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Free educational videos and exercises on {topic}"
            },
            {
                "title": f"{topic} Tutorial - freeCodeCamp",
                "type": "interactive",
                "url": "https://www.freecodecamp.org/news/search/?query=" + topic_encoded,
                "platform": "freeCodeCamp",
                "difficulty": "beginner",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Interactive coding tutorials on {topic}"
            },
            {
                "title": f"{topic} Course - Coursera",
                "type": "course",
                "url": f"https://www.coursera.org/search?query={topic_encoded}",
                "platform": "Coursera",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"University-level courses on {topic}"
            },
            {
                "title": f"{topic} Documentation - MDN Web Docs",
                "type": "article",
                "url": f"https://developer.mozilla.org/en-US/search?q={topic_encoded}",
                "platform": "MDN",
                "difficulty": "intermediate",
                "estimated_time": "Self-paced",
                "is_free": True,
                "description": f"Technical documentation on {topic}"
            },
            {
                "title": f"{topic} - MIT OpenCourseWare",
                "type": "course",
                "url": f"https://ocw.mit.edu/search/?q={topic_encoded}",
                "platform": "MIT",
                "difficulty": "advanced",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"MIT course materials on {topic}"
            }
        ]

    @staticmethod
    def get_smart_resources(topic, resource_type="all", limit=5, context=None, topic_category=None):
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
            
            # Generate new resources via AI with full context and topic category
            try:
                new_resources_data = LearningAIService.suggest_resources(
                    topic, 
                    resource_type,
                    context=context,  # Pass the rich context
                    topic_category=topic_category  # Pass the topic category
                )
                
                print(f"AI generated {len(new_resources_data)} resources for topic: {topic}")
                
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
                                estimated_time=resource_data.get('estimated_time', 'Varies'),
                                is_free=resource_data.get('is_free', True),
                                times_recommended=1  # First recommendation
                            )
                            new_resources.append(resource)
                            existing_urls.add(resource_url)
                            print(f"Saved new resource: {resource.title}")
                            
                            if len(new_resources) >= needed_count:
                                break
                        except Exception as e:
                            # Silently skip duplicates, only print other errors
                            if 'duplicate key' not in str(e).lower():
                                print(f"Error saving resource '{resource_data.get('title')}': {e}")
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
                print(f"Error in AI resource generation for {topic}: {str(e)}")
                if existing_resources:
                    print(f"Using {len(existing_resources)} existing resources from database")
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
                    print(f"No existing resources found, using curated fallback for topic: {topic}")
                    return LearningAIService._get_curated_fallback_resources(topic)
        
        except Exception as e:
            # Database connection error - use fallback curated resources
            print(f"Database error in get_smart_resources for {topic}: {str(e)}")
            return LearningAIService._get_curated_fallback_resources(topic)