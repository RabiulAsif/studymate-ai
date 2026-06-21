"""
Chat routes for StudyMate AI
"""
from fastapi import APIRouter, Query
from app.services.ai_service import get_ai_response
from app.database import (
    save_chat,
    get_chat_history,
    update_session_name,
)
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Validation keywords for study questions
STUDY_KEYWORDS = [
    "what is", "what are", "explain", "how do", "how to",
    "why is", "define", "tell me", "teach me", "help",
    "solve", "calculate", "formula", "equation", "concept",
    "theory", "example", "difference", "compare", "analyze",
    "homework", "assignment", "project", "exam", "test", "quiz"
]

POLITE_MESSAGES = [
    "thanks", "thank you", "ok", "okay", "sure", "yes", "no",
    "hello", "hi", "hey", "goodbye", "bye", "help", "please"
]


def is_study_question(message: str) -> bool:
    """Check if message is study-related"""
    message_lower = message.lower().strip()
    
    # Allow polite messages
    for phrase in POLITE_MESSAGES:
        if message_lower == phrase or message_lower.startswith(phrase):
            return True
    
    # Allow study keywords
    for keyword in STUDY_KEYWORDS:
        if keyword in message_lower:
            return True
    
    # Allow questions (with ?)
    if "?" in message:
        return True
    
    # Allow short messages
    if len(message.split()) <= 3:
        return True
    
    return True  # Default allow


@router.post("/chat")
async def chat(data: dict):
    """Send message to AI and get response"""
    try:
        message = data.get("message", "").strip()
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        history = data.get("history", [])
        is_first_message = data.get("is_first_message", False)

        if not message or not user_id or not session_id:
            return {
                "status": "error",
                "message": "Missing required fields",
                "reply": "❌ Error: Missing message, user_id, or session_id"
            }

        # Validate question
        if not is_study_question(message):
            return {
                "status": "error",
                "reply": "I'm specifically designed to help with study questions. Please ask me something related to academics, subjects, or learning!"
            }

        # Get AI response - FIXED: Only pass message and history
        ai_response = get_ai_response(message, history)

        # Save chat to database
        save_chat(user_id, session_id, message, ai_response)

        # Update session name with first message
        if is_first_message:
            session_name = message[:50]  # First 50 chars
            update_session_name(user_id, session_id, session_name)

        return {
            "status": "success",
            "reply": ai_response,
            "session_id": session_id,
            "user_id": user_id
        }

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {
            "status": "error",
            "reply": f"❌ Error: {str(e)}"
        }