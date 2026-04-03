from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.embedding import embed_query
from app.services.gemini_client import generate_response
from app.services.prompt import build_rag_prompt

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None
    sources: list[str] = Field(default_factory=list)


class EmbedResponse(BaseModel):
    embedding: list[float]


class TokenUsageResponse(BaseModel):
    prompt_token_count: int | None = None
    candidates_token_count: int | None = None
    total_token_count: int | None = None


class ChatResponse(BaseModel):
    response: str
    usage: TokenUsageResponse


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    system, contents = build_rag_prompt(
        request.system_prompt or "",
        request.sources,
        request.message,
    )

    response = generate_response(contents, system)

    print("Generated Response:", response["response"], "Token: " , response["usage"]   )
    
    return response 

@router.post("/chat/embed", response_model=EmbedResponse)
async def embed_message(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return EmbedResponse(embedding=embed_query(request.message))
