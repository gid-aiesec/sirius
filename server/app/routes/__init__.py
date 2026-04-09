from fastapi import APIRouter
from .health import router as health_check
from .auth import router as auth_router
from .chat import router as chat_router
from .ingest import router as upsert_router
from .query import router as query_router

main_router = APIRouter()

main_router.include_router(health_check)
main_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
main_router.include_router(chat_router, prefix="/chat", tags=["chats"])
main_router.include_router(upsert_router, prefix="/rag", tags=["rag pipeline"])
main_router.include_router(query_router, prefix="/rag", tags=["rag pipeline"])
