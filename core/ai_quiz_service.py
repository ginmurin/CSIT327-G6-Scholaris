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
                "content": (
                    "You are an AI that must output ONLY valid JSON. "
                    "Never include explanations, comments, markdown, or additional text. "
                    "Generate educational quiz questions based on the given topic."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Create {num_questions} educational multiple choice questions about '{topic}' "
                    f"at {difficulty} difficulty level.\n\n"
                    f"Topic: {topic}\n"
                    f"Difficulty: {difficulty}\n"
                    f"Number of questions: {num_questions}\n\n"
                    "IMPORTANT RULES:\n"
                    "1. Questions MUST be about the actual topic, not generic placeholders\n"
                    "2. Test real understanding and knowledge of the subject\n"
                    "3. Each question must have 4 distinct options (a, b, c, d)\n"
                    "4. Only ONE option should be correct\n"
                    "5. The answer field must be a single lowercase letter: a, b, c, or d\n"
                    "6. Make options challenging but fair\n"
                    "7. Return ONLY valid JSON, no markdown or explanations\n\n"
                    "Example format (but create REAL questions about the topic):\n"
                    "{\n"
                    "  \"questions\": [\n"
                    "    {\n"
                    "      \"question\": \"What is the main function of mitochondria?\",\n"
                    "      \"a\": \"Protein synthesis\",\n"
                    "      \"b\": \"Energy production (ATP)\",\n"
                    "      \"c\": \"DNA replication\",\n"
                    "      \"d\": \"Cell division\",\n"
                    "      \"answer\": \"b\"\n"
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    f"Now create {num_questions} REAL questions about {topic}:"
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
                model="meta-llama/llama-3.2-3b-instruct:free",
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
                timeout=60.0,  # 60 second timeout for API call
                extra_body={
                    "reasoning": {"enabled": True},
                    "provider": {
                        "sort": "throughput"
                    }
                }
            )
            
            print("📥 Receiving quiz data...")
            
            content = response.choices[0].message.content
            
            # Extract JSON if there's extra text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            # Parse the JSON
            parsed = json.loads(content)
            
            # Validate the structure
            if "questions" not in parsed:
                raise ValueError("Response missing 'questions' field")
            
            if len(parsed["questions"]) != num_questions:
                print(f"⚠️ Warning: Expected {num_questions} questions, got {len(parsed['questions'])}")
            
            print(f"✅ Quiz generated successfully! Created {len(parsed['questions'])} questions.\n")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"📄 Raw response: {content[:200]}...")
            return _get_fallback_quiz(topic, num_questions)
            
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            return _get_fallback_quiz(topic, num_questions)
            
        except Exception as e:
            print(f"❌ Error calling OpenRouter API: {e}")
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

