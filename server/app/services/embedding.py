import os
from google import genai

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBEDDING_MODEL = "models/text-embedding-004"


def embed_query(text: str) -> list[float]:
    result = _client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return result.embeddings[0].values
