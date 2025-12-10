from openai import OpenAI
from django.conf import settings
import json
import os
import re
import time
import random

# Initialize OpenRouter client for quiz generation
def get_openrouter_client():
    """Get OpenRouter client with API key from environment"""
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OpenRouter API key not found. Make sure KEY is set in your .env file.")
    
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )


class QuizGenerationService:
    """Service for generating quizzes using AI via OpenRouter"""
    
    # Fun loading messages
    LOADING_MESSAGES = [
        "🧠 Thinking of clever questions...",
        "📚 Reading through study materials...",
        "🎯 Creating challenging questions...",
        "✨ Sprinkling some educational magic...",
        "🤔 Making sure these aren't too easy...",
        "📝 Crafting the perfect quiz...",
        "🎲 Rolling the question dice...",
        "🔬 Analyzing the topic deeply...",
        "🎨 Designing engaging questions...",
        "⚡ Charging up the AI brain..."
    ]
    
    @staticmethod
    def generate_quiz(topic, difficulty="medium", num_questions=3):
        """Generate quiz using OpenRouter API"""
        
        # Show fun loading message
        loading_msg = random.choice(QuizGenerationService.LOADING_MESSAGES)
        print(f"\n{loading_msg}")
        print(f"📊 Generating {num_questions} {difficulty} questions about '{topic}'...\n")
        
        messages = [
            {
                "role": "system",
                "content": "Output ONLY valid JSON. No markdown, no explanations."
            },
            {
                "role": "user",
                "content": (
                    f"Create {num_questions} {difficulty} quiz questions about '{topic}'.\n"
                    f"Return ONLY this JSON format:\n"
                    f'{{"questions":[{{"question":"text","a":"opt1","b":"opt2","c":"opt3","d":"opt4","answer":"a"}}]}}\n'
                    f"Rules: Real questions about {topic}, 4 options each, one correct answer (a/b/c/d)."
                )
            }
        ]
        
        try:
            # Get OpenRouter client
            client = get_openrouter_client()
            
            # Animate loading
            print("⏳ Contacting AI server...")
            
            # Make API call with timeout
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=messages,
                temperature=0.2,
                max_tokens=1200,
                timeout=20.0
            )
            
            print("📥 Receiving quiz data...")
            
            content = response.choices[0].message.content
            
            # Extract JSON if there's extra text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            # Parse the JSON
            parsed = json.loads(content)
            
            # Simple validation
            if "questions" not in parsed:
                raise ValueError("Response missing 'questions' field")
            
            print(f"✅ Quiz generated! Created {len(parsed['questions'])} questions.\n")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON error: {e}")
            return _get_fallback_quiz(topic, num_questions)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return _get_fallback_quiz(topic, num_questions)


def _get_fallback_quiz(topic, num_questions):
    """Return a fallback quiz if AI generation fails"""
    print("⚠️ Using fallback quiz. Please check your API configuration.")
    return {
        "questions": [
            {
                "question": f"Sample question {i+1} about {topic}?",
                "a": "Option A",
                "b": "Option B",
                "c": "Option C",
                "d": "Option D",
                "answer": "a"
            }
            for i in range(num_questions)
        ],
        "error": "API call failed, using fallback quiz"
    }

