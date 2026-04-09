import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.routes.ingest import router as ingest_router
from app.routes.query import router as query_router
from app.routes.auth import router as auth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
        allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()],
        allow_methods=[method.strip() for method in os.getenv("ALLOWED_METHODS", "*").split(",") if method.strip()],
        allow_headers=[header.strip() for header in os.getenv("ALLOWED_HEADERS", "*").split(",") if header.strip()],
        allow_credentials=os.getenv("ALLOWED_CREDENTIALS", "false").lower() in {"1", "true", "yes"},
    )

#Root Endpoint
@app.get("/")
async def root():
    return {"message": "Server is running"}
api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(ingest_router)
api_router.include_router(query_router, prefix="/query")
api_router.include_router(auth_router)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
