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

        prompt = f"""Find {limit} learning resources for: {topic}

Return ONLY JSON array:
[
  {{
    "title": "Resource title",
    "type": "video",
    "url": "https://direct-url.com",
    "description": "Brief description",
    "estimated_time": "2h",
    "difficulty": "beginner",
    "platform": "YouTube",
    "is_free": true
  }}
]

Requirements:
- Direct URLs only (no search pages)
- Mix types: video, article, course
- Popular platforms
- Resources must be about {topic}"""

        try:
            client = get_openrouter_client()

            response = client.chat.completions.create(
                model="openrouter/sherlock-dash-alpha",
                messages=[
                    {"role": "system", "content": "Output only valid JSON array. No text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400,
                timeout=ResourceGenerationService.AI_TIMEOUT_SECONDS,
                extra_body={
                    "reasoning": {"enabled": False},
                    "provider": {"sort": "throughput"}
                }
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

            # Filter valid resources
            cleaned = [r for r in resources if isinstance(r, dict) and "title" in r and "url" in r]

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
