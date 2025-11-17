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

        prompt = f"""Generate EXACTLY {limit} learning resources ONLY about "{topic}".

CRITICAL: All resources MUST be directly related to: {topic}
Do NOT include resources about other topics.

Return ONLY JSON array:
[
  {{
    "title": "Resource about {topic}",
    "type": "video",
    "url": "https://direct-url.com",
    "description": "Learn {topic}",
    "estimated_time": "2h",
    "difficulty": "beginner",
    "platform": "YouTube",
    "is_free": true
  }}
]

Requirements:
- Direct URLs only
- Mix types: video, article, course
- Topic: {topic} ONLY"""

        try:
            client = get_openrouter_client()

            response = client.chat.completions.create(
                model="openrouter/sherlock-dash-alpha",
                messages=[
                    {"role": "system", "content": f"Generate learning resources ONLY about {topic}. Output valid JSON array only."},
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

            # Filter valid resources and check if they match the topic
            cleaned = []
            topic_lower = topic.lower()
            for r in resources:
                if not isinstance(r, dict) or "title" not in r or "url" not in r:
                    continue
                # Basic topic validation - check if topic keywords appear in title or description
                title_lower = r.get("title", "").lower()
                desc_lower = r.get("description", "").lower()
                # Skip if resource seems unrelated to the topic
                if topic_lower not in title_lower and topic_lower not in desc_lower:
                    # Check for major keywords from topic
                    topic_words = set(topic_lower.split())
                    title_words = set(title_lower.split())
                    # If no overlap in main words, skip
                    if not topic_words.intersection(title_words):
                        continue
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
