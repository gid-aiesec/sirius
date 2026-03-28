from fastapi import APIRouter
from pydantic import BaseModel
from app.services.gemini_client import generate_response

router= APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message
    if not user_message:
        return {"error": "Message is required"}
    
    response = generate_response(user_message)
    return {"response": response}