import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.routes.ingest import router as ingest_router
from app.routes.query import router as query_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS")],
    allow_methods=[os.getenv("ALLOWED_METHODS")],
    allow_headers=[os.getenv("ALLOWED_HEADERS")],
    allow_credentials=os.getenv("ALLOWED_CREDENTIALS"),
    )

#Root Endpoint
@app.get("/")
async def root():
    return {"message": "Server is running"}

app.include_router(health_router,prefix="/api")
app.include_router(chat_router,prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(query_router, prefix="/api/query")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
