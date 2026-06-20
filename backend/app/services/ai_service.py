import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are an expert AI Study Assistant. Your role is to:

1. Explain concepts clearly and simply
2. Use real-world examples
3. Ask follow-up questions to encourage learning
4. Break down complex topics into digestible parts
5. Adapt your explanation based on student confusion
6. Be encouraging and supportive

Remember: You're tutoring a student, not just answering questions."""


def get_ai_response(message: str, conversation_history: list = None):
    """
    Get response from Groq API with conversation history
    
    Args:
        message: Current user message
        conversation_history: List of previous messages for context
        
    Returns:
        str: AI response or error message
    """
    
    if not API_KEY:
        return "Error: GROQ_API_KEY not found in .env file"

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build messages array with history
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current message
    messages.append({
        "role": "user",
        "content": message
    })
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            return f"API Error ({response.status_code}): {error_message}"

        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        
        return "Error: No response from API"

    except requests.exceptions.Timeout:
        return "Error: Request timed out"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Groq. Check your internet."
    except Exception as e:
        return f"Error: {str(e)}"