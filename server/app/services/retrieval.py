from typing import Any

from app.database import vector_index
from app.services.embedding import embed_text


def _get_match_metadata(match: Any) -> dict:
    metadata = getattr(match, "metadata", None)
    if metadata is not None:
        return metadata
    if isinstance(match, dict):
        return match.get("metadata", {}) or {}
    return {}


def retrieve_sources(query_text: str, user_id: str, top_k: int = 5) -> list[str]:
    query = query_text.strip()
    normalized_user_id = user_id.strip()
    if not query or not normalized_user_id:
        return []

    embedding = embed_text(query, input_type="query")
    result = vector_index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        filter={"user_id": {"$eq": normalized_user_id}},
    )

    matches = getattr(result, "matches", None)
    if matches is None and isinstance(result, dict):
        matches = result.get("matches", [])

    sources: list[str] = []
    for match in matches or []:
        metadata = _get_match_metadata(match)
        match_user_id = str(metadata.get("user_id", "")).strip()
        if match_user_id != normalized_user_id:
            continue
        text = str(metadata.get("text", "")).strip()
        section = str(metadata.get("section", "")).strip()
        if not text:
            continue

        source = f"{section}:\n{text}" if section else text
        if source not in sources:
            sources.append(source)

    return sources
