from time import perf_counter

from google import genai
from google.genai import types

from app.config import settings
from app.logging_utils import log_event

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = settings.GEMINI_MODEL


def _extract_response_text(response) -> str:
    """Avoid response.text raising on blocked/empty or multi-part replies (google-genai)."""
    try:
        t = response.text
        if t is not None:
            return t
    except Exception:
        pass
    parts: list[str] = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", None) or []:
            txt = getattr(part, "text", None)
            if txt:
                parts.append(txt)
    return "".join(parts)


def generate_response(
    contents: str,
    system_instruction: str | None = None,
    *,
    operation_id: str | None = None,
    user_id: str | None = None,
) -> dict:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing; set it in server .env")

    kwargs: dict = {"model": MODEL_NAME, "contents": contents}
    if system_instruction:
        kwargs["config"] = types.GenerateContentConfig(
            system_instruction=system_instruction
        )

    start = perf_counter()
    try:
        response = client.models.generate_content(**kwargs)
    except Exception as exc:
        log_event(
            "gemini_response_error",
            operation_id=operation_id,
            user_id=user_id,
            model=MODEL_NAME,
            error=str(exc),
        )
        raise
    gemini_response_ms = round((perf_counter() - start) * 1000, 2)

    usage = getattr(response, "usage_metadata", None)
    text_out = _extract_response_text(response)
    if not text_out.strip():
        pf = getattr(response, "prompt_feedback", None)
        block = getattr(pf, "block_reason", None) if pf else None
        log_event(
            "gemini_empty_response",
            operation_id=operation_id,
            user_id=user_id,
            model=MODEL_NAME,
            block_reason=str(block) if block is not None else None,
        )

    result = {
        "response": text_out,
        "usage": {
            "prompt_token_count": getattr(usage, "prompt_token_count", None),
            "candidates_token_count": getattr(
                usage, "candidates_token_count", None
            ),
            "total_token_count": getattr(usage, "total_token_count", None),
        },
    }
    log_event(
        "gemini_response",
        operation_id=operation_id,
        user_id=user_id,
        model=MODEL_NAME,
        gemini_response_ms=gemini_response_ms,
        prompt_chars=len(contents),
        system_instruction_chars=len(system_instruction or ""),
        usage=result["usage"],
        response_text=result["response"],
    )
    return result
