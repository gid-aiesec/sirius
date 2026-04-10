"""Assemble system instruction and user contents for RAG generation."""

DEFAULT_RAG_SYSTEM_PROMPT = """
You are Sirius, a CV-aware assistant.

Answer the user's question using the retrieved context when it is relevant.
If the retrieved context is incomplete or does not support a claim, say so clearly.
Do not invent qualifications, dates, skills, achievements, or experience that are not grounded in the context.
When possible, prefer concise, direct answers that synthesize the evidence.
""".strip()


def _format_chat_history(chat_history: list[dict]) -> str:
    lines: list[str] = []
    for message in chat_history:
        content = str(message.get("content", "")).strip()
        if not content:
            continue

        role = str(message.get("role", "")).strip().lower()
        if role == "user":
            label = "User"
        elif role == "assistant":
            label = "Assistant"
        else:
            label = role.title() or "Message"

        lines.append(f"{label}: {content}")

    return "\n".join(lines)


def build_rag_prompt(
    system_prompt: str,
    sources: list[str],
    user_query: str,
    chat_history: list[dict] | None = None,
) -> tuple[str, str]:
    """Return (system_instruction, user_contents) for the Gemini API."""
    q = user_query.strip()
    chunks = [s.strip() for s in sources if s and s.strip()]
    history_block = _format_chat_history(chat_history or [])
    history_section = ""

    if history_block:
        history_section = (
            "Recent chat history (last 5 messages):\n"
            f"{history_block}\n\n"
        )

    if chunks:
        context_block = "\n\n".join(
            f"Source {index + 1}:\n{chunk}" for index, chunk in enumerate(chunks)
        )
        contents = (
            "Use the retrieved context below to answer the user.\n"
            "If the answer is not fully supported by the context, say what is missing.\n\n"
            f"{history_section}"
            f"Retrieved context:\n{context_block}\n\n"
            f"User question:\n{q}"
        )
    else:
        contents = (
            "No retrieved context was provided.\n"
            "Answer the user directly, and avoid making unsupported claims.\n\n"
            f"{history_section}"
            f"User question:\n{q}"
        )

    custom_system_prompt = system_prompt.strip()
    if custom_system_prompt:
        final_system_prompt = (
            f"{DEFAULT_RAG_SYSTEM_PROMPT}\n\n"
            f"Additional instructions:\n{custom_system_prompt}"
        )
    else:
        final_system_prompt = DEFAULT_RAG_SYSTEM_PROMPT

    return final_system_prompt, contents
