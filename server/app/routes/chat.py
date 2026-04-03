from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.embedding import embed_query
from app.services.gemini_client import generate_response
from app.services.prompt import build_rag_prompt
from app.services.retrieval import retrieve_sources

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str | None = None
    system_prompt: str | None = None
    top_k: int = Field(default=5, ge=1, le=10)
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

    sources = request.sources
    normalized_user_id = (request.user_id or "").strip()
    if not sources and normalized_user_id:
        sources = retrieve_sources(
            request.message,
            normalized_user_id,
            request.top_k,
        )

    system, contents = build_rag_prompt(
        request.system_prompt or "",
        sources,
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
