from openai import OpenAI
import os
import json
import re
import random
import urllib.parse

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
        "🎸 Tuning up your study symphony...",
    ]

    # Hard cap so we don't fight Render's 30s rule
    AI_TIMEOUT_SECONDS = float(os.getenv("RESOURCE_AI_TIMEOUT", "12"))  # ✅ fail fast

    @staticmethod
    def get_loading_message():
        """Return a random fun loading message"""
        return random.choice(ResourceGenerationService.LOADING_MESSAGES)

    @staticmethod
    def generate_resources(topic, resource_type="all", context=None, topic_category=None, limit=5):
        """
        Generate learning resources using DeepSeek AI
        
        Args:
            topic: The topic to find resources for
            resource_type: Type of resources (all, video, article, etc.)
            context: Additional context about the study plan
            topic_category: Category of the topic for better recommendations
            limit: Number of resources to generate (min: 3, max: 6, default: 5)
        
        Returns:
            List of resource dictionaries with title, url, type, description, etc.
        """
        # Clamp limit between 3 and 6
        limit = max(3, min(6, int(limit or 5)))

        # Optional: you might keep these prints in dev, remove in prod
        print(f"\n{ResourceGenerationService.get_loading_message()}")
        print(f"📊 Generating {limit} resources for '{topic}'...")

        # Build category hint (kept but light)
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

        # Build a compact prompt (less tokens = faster)
        context_info = ""
        if context:
            context_info = (
                f"Context: {context.get('description', '')} "
                f"Goal: {context.get('learning_objective', '')} "
                f"Preferred: {context.get('preferred_resources', 'Any')} "
                f"Duration: {context.get('duration', 'Flexible')} "
                f"Hours/Week: {context.get('hours_per_week', 'Flexible')}\n"
            )

        prompt = f"""Find {limit} real learning resources for: {topic}
{category_hint}{context_info}
Requirements:
- DIRECT URLs only (no search results pages)
- Mix of videos, articles, courses if possible
- Platforms like YouTube, Khan Academy, Coursera, etc.
- Short, accurate descriptions

Return ONLY a valid JSON array (no text before or after), e.g.:

[
  {{
    "title": "Resource title",
    "type": "video",
    "url": "https://direct-url.com",
    "description": "What you'll learn",
    "estimated_time": "2 hours",
    "difficulty": "beginner",
    "platform": "YouTube",
    "is_free": true
  }}
]

Types: video, article, interactive, course, practice, documentation.
Difficulty: beginner, intermediate, advanced, all.
"""

        try:
            client = get_openrouter_client()

            print("🤖 Calling AI for resource generation...")

            response = client.chat.completions.create(
                model="openrouter/sherlock-think-alpha",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a fast resource curator. "
                            "Output ONLY a valid JSON array with resource objects. "
                            "No explanation, no markdown."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=700,            # ✅ smaller = faster
                timeout=ResourceGenerationService.AI_TIMEOUT_SECONDS,  # ✅ fail fast
                extra_body={
                    "reasoning": {"enabled": False},
                    "provider": {"sort": "throughput"},
                },
            )

            result_text = (response.choices[0].message.content or "").strip()
            print("✅ Received response from AI")

            # Clean up possible markdown fencing just in case
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            # Extract JSON array safely
            json_match = re.search(r"\[[\s\S]*\]", result_text)
            if json_match:
                result_text = json_match.group(0)

            try:
                resources = json.loads(result_text)
            except json.JSONDecodeError as je:
                print(f"❌ JSON parse error: {je}")
                raise ValueError("Failed to parse AI JSON")

            if not isinstance(resources, list):
                raise ValueError("AI response is not a JSON list")

            # Optional: sanity filter
            cleaned = []
            for r in resources:
                if not isinstance(r, dict):
                    continue
                if "title" not in r or "url" not in r:
                    continue
                cleaned.append(r)

            if not cleaned:
                raise ValueError("No valid resources after cleaning")

            print(f"✅ Successfully generated {len(cleaned)} resources")
            # Enforce requested limit
            return cleaned[:limit]

        except Exception as e:
            # Any error → immediate fallback (fast, safe)
            print(f"❌ Error generating resources with DeepSeek: {e}")
            return ResourceGenerationService._get_fallback_resources(topic, limit)

    @staticmethod
    def _get_fallback_resources(topic, limit=7):
        """Generate fallback resources when AI fails quickly"""
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
                "description": f"Video tutorials and courses on {topic}",
            },
            {
                "title": f"{topic} - Khan Academy",
                "type": "video",
                "url": f"https://www.khanacademy.org/search?page_search_query={topic_encoded}",
                "platform": "Khan Academy",
                "difficulty": "beginner",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Free educational videos and exercises on {topic}",
            },
            {
                "title": f"{topic} Course - Coursera",
                "type": "course",
                "url": f"https://www.coursera.org/search?query={topic_encoded}",
                "platform": "Coursera",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"University-level courses on {topic}",
            },
            {
                "title": f"{topic} Documentation - MDN Web Docs",
                "type": "documentation",
                "url": f"https://developer.mozilla.org/en-US/search?q={topic_encoded}",
                "platform": "MDN",
                "difficulty": "intermediate",
                "estimated_time": "Reference",
                "is_free": True,
                "description": f"Comprehensive documentation and guides on {topic}",
            },
            {
                "title": f"{topic} Tutorial - W3Schools",
                "type": "interactive",
                "url": "https://www.w3schools.com/",
                "platform": "W3Schools",
                "difficulty": "beginner",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Interactive tutorials and examples for {topic}",
            },
            {
                "title": f"{topic} - Udemy Courses",
                "type": "course",
                "url": f"https://www.udemy.com/courses/search/?q={topic_encoded}",
                "platform": "Udemy",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": False,
                "description": f"Professional courses on {topic}",
            },
            {
                "title": f"{topic} - edX Learning",
                "type": "course",
                "url": f"https://www.edx.org/search?q={topic_encoded}",
                "platform": "edX",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"University courses and programs on {topic}",
            },
        ]

        return fallback[:limit]
