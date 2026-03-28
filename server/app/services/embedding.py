import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "models/text-embedding-004"


def embed_query(text: str) -> list[float]:
    result = genai.embed_content(model=EMBEDDING_MODEL, content=text)
    return result["embedding"]
