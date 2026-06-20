from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.services.ai_service import get_ai_response
from app.database import (
    save_chat,
    get_chat_history,
    create_session,
    update_session_name,
    get_all_sessions,
)
from app.utils.validation import is_study_question

router = APIRouter()


# ========== PYDANTIC MODELS ==========
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None
    history: Optional[List[dict]] = None
    is_first_message: Optional[bool] = False  # ← NEW: Track first message


class ChatResponse(BaseModel):
    status: str
    user_id: str
    session_id: str
    reply: str


# ========== CHAT ENDPOINT ==========
@router.post("/chat")
async def chat(request: ChatRequest):
    """Send a message and get AI response"""
    try:
        message = request.message.strip()
        user_id = request.user_id
        session_id = request.session_id
        history = request.history or []
        is_first_message = request.is_first_message

        # Validate inputs
        if not message:
            return {
                "status": "error",
                "message": "Message cannot be empty",
                "reply": "Please enter a valid question.",
                "user_id": user_id,
                "session_id": session_id
            }

        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
                "reply": "User identification required",
                "user_id": "unknown",
                "session_id": session_id
            }

        # Check if it's a study question
        if not is_study_question(message):
            return {
                "status": "warning",
                "message": "Non-study question detected",
                "reply": "I'm specifically designed to help with study questions. Please ask me something related to academics, subjects, or learning!",
                "user_id": user_id,
                "session_id": session_id
            }

        # Create session if not exists
        if not session_id:
            session_id = str(uuid.uuid4())
            create_session(user_id, session_id, user_name="New Chat")

        # Get AI response
        ai_response = get_ai_response(message, history)

        # Save to database with user_id
        save_chat(user_id, session_id, message, ai_response)

        # ========== FIX #1: UPDATE SESSION NAME WITH FIRST QUESTION ==========
        # If this is the first message, use it as the session name
        if is_first_message:
            # Truncate message to 50 characters for display
            session_name = message[:50] + ("..." if len(message) > 50 else "")
            update_session_name(user_id, session_id, session_name)
            print(f"✅ Updated session name to: {session_name}")

        return {
            "status": "success",
            "user_id": user_id,
            "session_id": session_id,
            "reply": ai_response
        }

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {
            "status": "error",
            "message": str(e),
            "reply": f"❌ Error: {str(e)}",
            "user_id": request.user_id or "unknown",
            "session_id": request.session_id or "unknown"
        }


# ========== NEW ENDPOINT: Get last session on page load ==========
@router.get("/last-session")
def get_last_session(user_id: str):
    """Get the last active session for a user (for page refresh)"""
    try:
        if not user_id:
            return {
                "status": "error",
                "session_id": None
            }
        
        sessions = get_all_sessions(user_id)
        
        if sessions and len(sessions) > 0:
            return {
                "status": "success",
                "session_id": sessions[0]["session_id"]
            }
        else:
            return {
                "status": "no_session",
                "session_id": None
            }
    except Exception as e:
        print(f"Error getting last session: {e}")
        return {
            "status": "error",
            "session_id": None
        }