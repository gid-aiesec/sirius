from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from time import perf_counter
from uuid import uuid4

from app.logging_utils import log_event
from app.services.embedding import embed_text
from app.services.gemini_client import generate_response
from app.services.prompt import build_rag_prompt
from app.services.retrieval import retrieve_sources

from app.services.supabase_client import save_chat_message, get_chat_history

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


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    operation_id = uuid4().hex
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    sources = request.sources
    normalized_user_id = (request.user_id or "").strip()
    
    if normalized_user_id:
        save_chat_message(user_id=normalized_user_id, role="user", content=request.message)

    try:
        if not sources and normalized_user_id:
            retrieval_start = perf_counter()
            sources = retrieve_sources(
                request.message,
                normalized_user_id,
                request.top_k,
            )
            retrieval_ms = round((perf_counter() - retrieval_start) * 1000, 2)
        else:
            retrieval_ms = 0.0

        prompt_start = perf_counter()
        system, contents = build_rag_prompt(
            request.system_prompt or "",
            sources,
            request.message,
        )
        prompt_assembly_ms = round((perf_counter() - prompt_start) * 1000, 2)

        rag_retrieval_and_prompt_assembly_ms = round(
            retrieval_ms + prompt_assembly_ms,
            2,
        )

        response = generate_response(
            contents,
            system,
            operation_id=operation_id,
            user_id=normalized_user_id or None,
        )

        if normalized_user_id:
            save_chat_message(user_id=normalized_user_id, role="assistant", content=response["response"])

        log_event(
            "rag_chat_pipeline",
            operation_id=operation_id,
            user_id=normalized_user_id or None,
            top_k=request.top_k,
            source_count=len(sources),
            retrieval_ms=retrieval_ms,
            prompt_assembly_ms=prompt_assembly_ms,
            rag_retrieval_and_prompt_assembly_ms=rag_retrieval_and_prompt_assembly_ms,
            query_text=request.message,
        )
        return response
    except Exception as exc:
        log_event(
            "rag_chat_error",
            operation_id=operation_id,
            user_id=normalized_user_id or None,
            top_k=request.top_k,
            query_text=request.message,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Chat request failed: {exc}") from exc


@router.get("/history/{user_id}")
async def fetch_chat_history(user_id: str):
    normalized_id = user_id.strip()
    if not normalized_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    try:
        history = get_chat_history(normalized_id)
        return {"status": "success", "data": history}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {exc}")


@router.post("/embed", response_model=EmbedResponse)
async def embed_message(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return EmbedResponse(embedding=embed_text(request.message, input_type="query"))