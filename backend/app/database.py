"""
MongoDB database configuration with user_id separation
"""
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")

if not MONGODB_URL:
    raise ValueError("MONGODB_URL not found in .env file")

try:
    # Create MongoDB client
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    
    # Get database
    db = client.get_database()
    
    print("✅ Connected to MongoDB successfully!")
    
except ServerSelectionTimeoutError:
    print("❌ Could not connect to MongoDB. Check your connection string.")
    db = None
except Exception as e:
    print(f"❌ MongoDB Error: {e}")
    db = None


# Collections
def get_chats_collection():
    """Get chats collection"""
    return db["chats"]


def get_pdfs_collection():
    """Get PDFs collection"""
    return db["pdfs"]


def get_users_collection():
    """Get users collection"""
    return db["users"]


# ========== DATABASE OPERATIONS WITH USER_ID ==========

def save_chat(user_id: str, session_id: str, user_message: str, bot_response: str):
    """Save chat message to database with user_id"""
    try:
        chats = get_chats_collection()
        chats.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": datetime.utcnow()
        })
        return True
    except Exception as e:
        print(f"Error saving chat: {e}")
        return False


def get_chat_history(user_id: str, session_id: str):
    """Get chat history for a session (filtered by user_id)"""
    try:
        chats = get_chats_collection()
        messages = list(chats.find({
            "user_id": user_id,
            "session_id": session_id
        }).sort("timestamp", 1))
        
        conversation = []
        for msg in messages:
            conversation.append({
                "role": "user",
                "content": msg["user_message"]
            })
            conversation.append({
                "role": "assistant",
                "content": msg["bot_response"]
            })
        
        return conversation
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []


def save_pdf(user_id: str, session_id: str, filename: str, file_path: str, text_preview: str):
    """Save PDF metadata to database (filtered by user_id)"""
    try:
        pdfs = get_pdfs_collection()
        pdfs.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "filename": filename,
            "file_path": file_path,
            "text_preview": text_preview[:500],
            "timestamp": datetime.utcnow()
        })
        return True
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return False


def get_session_pdfs(user_id: str, session_id: str):
    """Get PDFs for a session (filtered by user_id)"""
    try:
        pdfs = get_pdfs_collection()
        return list(pdfs.find({
            "user_id": user_id,
            "session_id": session_id
        }))
    except Exception as e:
        print(f"Error getting PDFs: {e}")
        return []


def delete_pdf(user_id: str, session_id: str, filename: str):
    """Delete a PDF from database (filtered by user_id)"""
    try:
        pdfs = get_pdfs_collection()
        pdfs.delete_one({
            "user_id": user_id,
            "session_id": session_id,
            "filename": filename
        })
        return True
    except Exception as e:
        print(f"Error deleting PDF: {e}")
        return False


def create_session(user_id: str, session_id: str, user_name: str = "New Chat"):
    """Create a new chat session (with user_id)"""
    try:
        users = get_users_collection()
        users.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "user_name": user_name,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        })
        return True
    except Exception as e:
        print(f"Error creating session: {e}")
        return False


def update_session_name(user_id: str, session_id: str, user_name: str):
    """Update session name (to use first question as name)"""
    try:
        users = get_users_collection()
        users.update_one(
            {"user_id": user_id, "session_id": session_id},
            {
                "$set": {
                    "user_name": user_name,
                    "last_updated": datetime.utcnow()
                }
            }
        )
        return True
    except Exception as e:
        print(f"Error updating session name: {e}")
        return False


def get_all_sessions(user_id: str):
    """Get all chat sessions for a user (filtered by user_id)"""
    try:
        users = get_users_collection()
        return list(users.find({"user_id": user_id}).sort("created_at", -1))
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return []


def delete_session(user_id: str, session_id: str):
    """Delete a session and all its chats (filtered by user_id)"""
    try:
        # Delete session from users collection
        users = get_users_collection()
        users.delete_one({
            "user_id": user_id,
            "session_id": session_id
        })
        
        # Delete all chats for this session
        chats = get_chats_collection()
        chats.delete_many({
            "user_id": user_id,
            "session_id": session_id
        })
        
        # Delete all PDFs for this session
        pdfs = get_pdfs_collection()
        pdfs.delete_many({
            "user_id": user_id,
            "session_id": session_id
        })
        
        print(f"✅ Session {session_id} deleted for user {user_id}")
        return True
    except Exception as e:
        print(f"Error deleting session: {e}")
        return False


def get_all_sessions_admin():
    """Get ALL sessions (admin only - no user_id filter)"""
    try:
        users = get_users_collection()
        return list(users.find().sort("created_at", -1))
    except Exception as e:
        print(f"Error getting all sessions: {e}")
        return []