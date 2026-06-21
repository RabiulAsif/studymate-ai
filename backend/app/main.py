from fastapi import FastAPI, UploadFile, File, Query
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
import os

from app.routes.chat import router as chat_router
from app.database import (
    get_all_sessions,
    get_chats_collection,
    get_session_pdfs,
    delete_pdf,
    create_session,
    delete_session as db_delete_session,
)

app = FastAPI()

# CORS configuration - Allow frontend and local development
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://studymate-ai-xi.vercel.app",
    "https://studymate-ai-frontend.vercel.app",
    "https://studymate-ai-frontend-mu.vercel.app",
    "https://*.vercel.app",
    "https://*.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat_router)

# Create uploads directory - Use /tmp on Vercel, local folder otherwise
if os.environ.get("VERCEL"):
    UPLOADS_DIR = "/tmp/uploads"
else:
    UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

os.makedirs(UPLOADS_DIR, exist_ok=True)


# ========== UTILITY FUNCTIONS ==========
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = serialize_doc(value)
        return result
    
    return doc


# ========== HEALTH CHECK ==========
@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.4.0"
    }


# ========== GET ALL SESSIONS (FILTERED BY USER_ID) ==========
@app.get("/sessions")
def get_sessions(user_id: str = Query(...)):
    """Get all chat sessions for a specific user"""
    try:
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
                "sessions": []
            }
        
        sessions = get_all_sessions(user_id)
        serialized_sessions = serialize_doc(sessions)
        
        return {
            "status": "success",
            "sessions": serialized_sessions,
            "count": len(serialized_sessions)
        }
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return {
            "status": "error",
            "message": str(e),
            "sessions": []
        }


# ========== CREATE NEW SESSION ==========
@app.post("/new-session")
def new_session(data: dict):
    """Create a new chat session"""
    try:
        user_id = data.get("user_id")
        
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required"
            }
        
        session_id = str(uuid.uuid4())
        create_session(user_id, session_id, user_name="New Chat")
        
        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id
        }
    except Exception as e:
        print(f"Error creating session: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ========== GET SESSION HISTORY (FILTERED BY USER_ID) ==========
@app.get("/session/{session_id}/history")
def get_session_history(session_id: str, user_id: str = Query(...)):
    """Get chat history for a session (filtered by user_id)"""
    try:
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
                "history": []
            }
        
        chats = get_chats_collection()
        messages = list(chats.find({
            "user_id": user_id,
            "session_id": session_id
        }).sort("timestamp", 1))
        
        serialized_messages = serialize_doc(messages)
        
        history = []
        for msg in serialized_messages:
            history.append({
                "role": "user",
                "content": msg.get("user_message", "")
            })
            history.append({
                "role": "assistant",
                "content": msg.get("bot_response", "")
            })
        
        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "history": history
        }
    except Exception as e:
        print(f"Error getting history: {e}")
        return {
            "status": "error",
            "message": str(e),
            "history": []
        }


# ========== GET LAST SESSION ==========
@app.get("/last-session")
def get_last_session(user_id: str = Query(...)):
    """Get the last active session for a user"""
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


# ========== DELETE SESSION ==========
@app.delete("/session/{session_id}")
def delete_session(session_id: str, user_id: str = Query(...)):
    """Delete a chat session (filtered by user_id)"""
    try:
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required"
            }
        
        success = db_delete_session(user_id, session_id)
        
        if success:
            return {
                "status": "success",
                "message": "Session deleted successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to delete session"
            }
    except Exception as e:
        print(f"Error deleting session: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ========== UPLOAD PDF ==========
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), session_id: str = None, user_id: str = None):
    """Upload a PDF file"""
    try:
        import pdfplumber
        from app.database import save_pdf
        
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required"
            }
        
        if not file.filename.endswith(".pdf"):
            return {
                "status": "error",
                "message": "Only PDF files are allowed"
            }
        
        # Save file
        file_path = os.path.join(UPLOADS_DIR, file.filename)
        contents = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Extract text
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                pages = len(pdf.pages)
        except:
            text = ""
            pages = 0
        
        # Save to database with user_id
        if session_id:
            save_pdf(user_id, session_id, file.filename, file_path, text)
        
        return {
            "status": "success",
            "success": True,
            "filename": file.filename,
            "pages": pages,
            "message": f"PDF uploaded successfully! ({pages} pages)"
        }
    
    except Exception as e:
        print(f"Error uploading PDF: {e}")
        return {
            "status": "error",
            "success": False,
            "message": f"Error uploading PDF: {str(e)}"
        }


# ========== GET SESSION PDFS (FILTERED BY USER_ID) ==========
@app.get("/session/{session_id}/pdfs")
def get_pdfs(session_id: str, user_id: str = Query(...)):
    """Get PDFs for a session (filtered by user_id)"""
    try:
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
                "pdfs": []
            }
        
        pdfs = get_session_pdfs(user_id, session_id)
        serialized_pdfs = serialize_doc(pdfs)
        
        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "pdfs": serialized_pdfs
        }
    except Exception as e:
        print(f"Error getting PDFs: {e}")
        return {
            "status": "error",
            "message": str(e),
            "pdfs": []
        }


# ========== DELETE PDF (FILTERED BY USER_ID) ==========
@app.delete("/session/{session_id}/pdfs/{filename}")
def remove_pdf(session_id: str, filename: str, user_id: str = Query(...)):
    """Delete a PDF (filtered by user_id)"""
    try:
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required"
            }
        
        delete_pdf(user_id, session_id, filename)
        
        # Also delete file from disk
        file_path = os.path.join(UPLOADS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "success",
            "message": f"PDF deleted: {filename}"
        }
    except Exception as e:
        print(f"Error deleting PDF: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ========== ROOT ==========
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    """Root endpoint"""
    return {
        "message": "StudyMate AI API",
        "status": "running",
        "version": "3.4.0",
        "note": "All endpoints require user_id for data separation"
    }