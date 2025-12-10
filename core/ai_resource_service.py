from openai import OpenAI
import os
import json
import re
import urllib.parse

def get_openrouter_client():
    """Initialize OpenRouter client"""
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OpenRouter API key not found in environment variables")
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

class ResourceGenerationService:
    """Service for generating learning resources using AI via OpenRouter"""
    
    AI_TIMEOUT_SECONDS = float(os.getenv("RESOURCE_AI_TIMEOUT", "12"))

    @staticmethod
    def generate_resources(topic, resource_type="all", context=None, topic_category=None, limit=5):
        """Generate learning resources using AI"""
        limit = max(3, min(6, int(limit or 5)))

        prompt = f"""Generate {limit} learning resources about "{topic}".
Return ONLY valid JSON array, no markdown or extra text.

Format:
[
  {{"title":"Intro to {topic}","type":"video","url":"https://youtube.com/watch?v=x","description":"Learn {topic}","estimated_time":"15min","difficulty":"beginner","platform":"YouTube","is_free":true}}
]

Types: video, article, course, tutorial
Difficulty: beginner, intermediate, advanced
Generate {limit} resources:"""

        try:
            client = get_openrouter_client()

            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[
                    {"role": "system", "content": "Output ONLY valid JSON array, no extra text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1200,
                timeout=20.0
            )

            result_text = (response.choices[0].message.content or "").strip()

            # Clean markdown
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            # Extract JSON array
            json_match = re.search(r"\[[\s\S]*\]", result_text)
            if json_match:
                result_text = json_match.group(0)

            resources = json.loads(result_text)

            if not isinstance(resources, list):
                raise ValueError("AI response is not a JSON list")

            # Quick validation - just check required fields
            cleaned = []
            for r in resources:
                if isinstance(r, dict) and "title" in r and "url" in r:
                    cleaned.append(r)

            if not cleaned:
                raise ValueError("No valid resources after cleaning")

            return cleaned[:limit]

        except Exception as e:
            return ResourceGenerationService._get_fallback_resources(topic, limit)

    @staticmethod
    def _get_fallback_resources(topic, limit=5):
        """Generate fallback resources when AI fails"""
        topic_encoded = urllib.parse.quote(topic)

        fallback = [
            {
                "title": f"{topic} - YouTube Tutorials",
                "type": "video",
                "url": f"https://www.youtube.com/results?search_query={topic_encoded}+tutorial",
                "platform": "YouTube",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Video tutorials on {topic}",
            },
            {
                "title": f"{topic} - Khan Academy",
                "type": "video",
                "url": f"https://www.khanacademy.org/search?page_search_query={topic_encoded}",
                "platform": "Khan Academy",
                "difficulty": "beginner",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Free educational videos on {topic}",
            },
            {
                "title": f"{topic} - Coursera",
                "type": "course",
                "url": f"https://www.coursera.org/search?query={topic_encoded}",
                "platform": "Coursera",
                "difficulty": "all",
                "estimated_time": "Varies",
                "is_free": True,
                "description": f"Online courses on {topic}",
            },
        ]

        return fallback[:limit]
