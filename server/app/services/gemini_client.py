from time import perf_counter

from google import genai
from google.genai import types

from app.config import settings
from app.logging_utils import log_event

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"


def generate_response(
    contents: str,
    system_instruction: str | None = None,
    *,
    operation_id: str | None = None,
    user_id: str | None = None,
) -> dict:
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
    result = {
        "response": response.text or "",
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
