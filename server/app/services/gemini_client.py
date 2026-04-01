from google import genai
from google.genai import types

from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_response(contents: str, system_instruction: str | None = None) -> str:
    kwargs: dict = {"model": "gemini-2.5-flash", "contents": contents}
    if system_instruction:
        kwargs["config"] = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    response = client.models.generate_content(**kwargs)
    return response.text