import os
from time import perf_counter
from pinecone import Pinecone
from app.config import settings
from app.logging_utils import log_event

PINECONE_API_KEY = settings.PINECONE_API_KEY

def embed_text(user_query: str, input_type: str = "query") -> list[float]:
    """
    Embeds using Pinecone's inference API
    Can embed both the search query and document chunks using input_type
    Model used: llama-text-embed-v2 (to match our 768 dimension index)
    """
    if not user_query or not user_query.strip():
        raise ValueError("No user_query provided")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    cleaned_query = user_query.strip()

    start = perf_counter()
    try:
        result = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[cleaned_query],
            parameters={
                "input_type": input_type,
                "dimension": 768,
                "truncate": "END",
            },
        )

        embedding = result.data[0].values
        embed_ms = round((perf_counter() - start) * 1000, 2)

        log_event(
            "embed_text_success",
            embed_ms=embed_ms,
            query_length=len(cleaned_query),
            embedding_dimension=len(embedding),
            embedding_model="llama-text-embed-v2",
            input_type=input_type,
        )

        return embedding

    except Exception as e:
        embed_ms = round((perf_counter() - start) * 1000, 2)
        log_event(
            "embed_text_error",
            embed_ms=embed_ms,
            query_length=len(cleaned_query),
            embedding_model="llama-text-embed-v2",
            input_type=input_type,
            error=str(e),
        )
        raise RuntimeError(f"Error embedding text with Pinecone: {e}") from e
