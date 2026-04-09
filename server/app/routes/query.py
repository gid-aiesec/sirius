from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.embedding import embed_text

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    embedding: list[float]


@router.post("/embed", response_model=QueryResponse)
async def embed_user_query(body: QueryRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    embedding = embed_text(body.query, input_type="query")
    return QueryResponse(embedding=embedding)
