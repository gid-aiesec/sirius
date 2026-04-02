from google import genai
from google.genai import types

from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"


def generate_response(contents: str, system_instruction: str | None = None) -> dict:
    kwargs: dict = {"model": MODEL_NAME, "contents": contents}
    if system_instruction:
        kwargs["config"] = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    response = client.models.generate_content(**kwargs)

    usage = getattr(response, "usage_metadata", None)
    return {
        "response": response.text or "",
        "usage": {
            "prompt_token_count": getattr(usage, "prompt_token_count", None),
            "candidates_token_count": getattr(
                usage, "candidates_token_count", None
            ),
            "total_token_count": getattr(usage, "total_token_count", None),
        },
    }
