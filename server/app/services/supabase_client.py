import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize client
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️ WARNING: Supabase URL or Key is missing from .env!")

def save_chat_message(user_id: str, role: str, content: str):
    """Saves a chat message to Supabase using the official SDK."""
    if not supabase:
        return None
    try:
        data = {"user_id": user_id, "role": role, "content": content}
        response = supabase.table("chat_history").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error saving to Supabase: {e}")
        return None

def get_chat_history(user_id: str):
    """Fetches the entire chat history for a user using the official SDK."""
    if not supabase:
        return []
    try:
        response = supabase.table("chat_history").select("*").eq("user_id", user_id).order("created_at").execute()
        return response.data
    except Exception as e:
        print(f"❌ Error fetching from Supabase: {e}")
        return []