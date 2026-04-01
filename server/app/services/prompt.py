"""Assemble system instruction and user contents for RAG generation."""


def build_rag_prompt(
    system_prompt: str,
    sources: list[str],
    user_query: str,
) -> tuple[str | None, str]:
    """Return (system_instruction or None, user contents) for the Gemini API."""
    q = user_query.strip()
    chunks = [s.strip() for s in sources if s and s.strip()]
    if chunks:
        ctx = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(chunks))
        contents = f"Retrieved sources:\n{ctx}\n\nUser query:\n{q}"
    else:
        contents = q
    sys_inst = system_prompt.strip() or None
    return sys_inst, contents
