from openai import OpenAI
import os
import json
import re
import random

def get_openrouter_client():
    """Initialize OpenRouter client for DeepSeek API"""
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OpenRouter API key not found in environment variables")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

class ResourceGenerationService:
    """Service for generating learning resources using DeepSeek AI via OpenRouter"""
    
    # Fun, creative loading messages to keep users engaged
    LOADING_MESSAGES = [
        "🔍 Scouring the internet for gems...",
        "📚 Flipping through digital libraries...",
        "🎯 Hunting down the perfect resources...",
        "✨ Summoning the learning wizards...",
        "🌟 Collecting knowledge treasures...",
        "🚀 Launching resource discovery mission...",
        "🎨 Painting your learning path...",
        "🔮 Consulting the wisdom archives...",
        "💎 Mining for educational diamonds...",
        "🌈 Weaving your learning journey...",
        "🎪 Setting up your knowledge carnival...",
        "🏆 Gathering championship resources...",
        "🎭 Curating your educational playlist...",
        "🌺 Blooming your learning garden...",
        "🎸 Tuning up your study symphony..."
    ]
    
    @staticmethod
    def get_loading_message():
        """Return a random fun loading message"""
        return random.choice(ResourceGenerationService.LOADING_MESSAGES)
    
    @staticmethod
    def generate_resources(topic, resource_type="all", context=None, topic_category=None, limit=7):
        """
        Generate learning resources using DeepSeek AI
        
        Args:
            topic: The topic to find resources for
            resource_type: Type of resources (all, video, article, etc.)
            context: Additional context about the study plan
            topic_category: Category of the topic for better recommendations
            limit: Number of resources to generate (default 7)
        
        Returns:
            List of resource dictionaries with title, url, type, description, etc.
        """
        # Show random fun loading message
        print(f"\n{ResourceGenerationService.get_loading_message()}")
        
        # Build category hint
        category_hint = ""
        if topic_category:
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
            category_hint = f"Category: {category_name}\n"
        
        # Build context information
        context_info = ""
        if context:
            context_info = f"""
STUDY PLAN CONTEXT:
- Description: {context.get('description', 'Not provided')}
- Learning Objective: {context.get('learning_objective', 'Not specified')}
- Preferred Resources: {context.get('preferred_resources', 'Any type')}
- Duration: {context.get('duration', 'Flexible')}
- Time Commitment: {context.get('hours_per_week', 'Flexible')}

IMPORTANT: Focus on resources that help achieve the learning objective above.
"""
        
        # Build the prompt
        prompt = f"""You are an expert learning resource curator. Find {limit} REAL, HIGH-QUALITY learning resources with SPECIFIC, WORKING URLs for this topic:

Topic: {topic}
{category_hint}Resource Type: {resource_type}
{context_info}

CRITICAL REQUIREMENTS:
1. Provide DIRECT URLs to specific resources (NOT search pages)
2. Each URL must be a real, working link to actual content
3. Good URL examples:
   - https://www.youtube.com/watch?v=VIDEO_ID (specific YouTube video)
   - https://www.khanacademy.org/subject/topic (specific Khan Academy lesson)
   - https://www.coursera.org/learn/course-name (specific Coursera course)
   - https://developer.mozilla.org/docs/Web/JavaScript (MDN documentation)
   - https://www.udemy.com/course/course-name (specific Udemy course)
   - https://www.w3schools.com/python/ (W3Schools tutorial)
4. NEVER use search URLs like "youtube.com/results" or "search?q="

IMPORTANT RULES:
- Provide resources for ANY topic (not just programming)
- Mix different resource types (videos, articles, interactive, courses)
- Include both beginner and intermediate level resources
- Ensure descriptions are helpful and specific
- All resources must be from reputable platforms

For non-programming topics, use appropriate platforms:
- Languages: Duolingo, Babbel, BBC Languages, FluentU
- Science: Khan Academy, Crash Course, MIT OpenCourseWare
- Arts: Skillshare, Domestika, YouTube tutorials
- Music: Musictheory.net, JustinGuitar, YouTube lessons
- Fitness: Nike Training Club, Yoga With Adriene, Fitness Blender
- Business: Coursera, edX, HarvardX

Return ONLY a valid JSON array (no markdown, no extra text):
[
    {{
        "title": "Exact resource title",
        "type": "video",
        "url": "https://direct-url.com",
        "description": "Clear description of what you'll learn",
        "estimated_time": "2 hours",
        "difficulty": "beginner",
        "platform": "YouTube",
        "is_free": true
    }}
]

Resource types: video, article, interactive, course, practice, documentation
Valid difficulty levels: beginner, intermediate, advanced, all

Generate {limit} diverse, high-quality resources now:"""

        try:
            client = get_openrouter_client()
            
            # Call DeepSeek API via OpenRouter
            print(f"🤖 Calling DeepSeek AI for resource generation...")
            response = client.chat.completions.create(
                model="openrouter/sherlock-think-alpha",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                extra_body={
                    "reasoning": {"enabled": True},
                    "provider": {
                        "sort": "throughput"
                    }
                }
            )
            
            # Extract the response
            result_text = response.choices[0].message.content.strip()
            print(f"✅ Received response from DeepSeek")
            
            # Clean up markdown formatting if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # Try to extract JSON array if it's embedded in text
            json_match = re.search(r'\[[\s\S]*\]', result_text)
            if json_match:
                result_text = json_match.group(0)
            
            # Parse JSON
            resources = json.loads(result_text)
            
            # Validate resources structure
            if not isinstance(resources, list):
                raise ValueError("Response is not a list")
            
            print(f"✅ Successfully generated {len(resources)} resources")
            return resources
            
        except Exception as e:
            print(f"❌ Error generating resources with DeepSeek: {e}")
            # Return fallback resources
            return ResourceGenerationService._get_fallback_resources(topic, limit)
    
    @staticmethod
    def _get_fallback_resources(topic, limit=7):
        """Generate fallback resources when AI fails"""
        import urllib.parse
        topic_encoded = urllib.parse.quote(topic)
        
        print(f"⚠️ Using fallback resources for: {topic}")
        
        fallback = [
            {
                "title": f"{topic} - YouTube Tutorials",
                "type": "video",
                "url": f"https://www.youtube.com/results?search_query={topic_encoded}+tutorial",
                "platform": "YouTube",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Video tutorials and courses on {topic}"
            },
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
                "type": "documentation",
                "url": f"https://developer.mozilla.org/en-US/search?q={topic_encoded}",
                "platform": "MDN",
                "difficulty": "intermediate",
                "estimated_time": "Reference",
                "is_free": True,
                "description": f"Comprehensive documentation and guides on {topic}"
            },
            {
                "title": f"{topic} Tutorial - W3Schools",
                "type": "interactive",
                "url": f"https://www.w3schools.com/",
                "platform": "W3Schools",
                "difficulty": "beginner",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Interactive tutorials and examples for {topic}"
            },
            {
                "title": f"{topic} - Udemy Courses",
                "type": "course",
                "url": f"https://www.udemy.com/courses/search/?q={topic_encoded}",
                "platform": "Udemy",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": False,
                "description": f"Professional courses on {topic}"
            },
            {
                "title": f"{topic} - edX Learning",
                "type": "course",
                "url": f"https://www.edx.org/search?q={topic_encoded}",
                "platform": "edX",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"University courses and programs on {topic}"
            }
        ]
        
        return fallback[:limit]
