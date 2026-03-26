import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.health import router as health_router

load_dotenv()

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