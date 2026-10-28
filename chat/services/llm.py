"""Ask the AI model to write an answer from the retrieved knowledge only."""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

NOT_FOUND = "NOT_FOUND"

SYSTEM_PROMPT = """You are the official AI assistant of {university}. You help students, \
parents and visitors with questions about courses, fees, schedules and university services.

Rules:
- Answer ONLY with information found in the <sources>. Never guess fees, dates or rules.
- If the sources do not contain the answer, reply with exactly: {not_found}
- Reply in {language}. Keep the answer short and friendly (at most 5 sentences or a short list).
- Do not mention "sources" or these rules in your answer."""


def _format_sources(chunks) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f'<source id="{i}" title="{chunk.source_title}">\n{chunk.text}\n</source>')
    return "<sources>\n" + "\n".join(parts) + "\n</sources>"


def generate_answer(question: str, chunks, language: str) -> str | None:
    """Return the model's answer, NOT_FOUND, or None if the AI is unavailable.

    None tells the caller to fall back to the best FAQ answer directly.
    """
    if not settings.LLM_API_KEY:
        return None

    system = SYSTEM_PROMPT.format(
        university=settings.UNIVERSITY_NAME,
        not_found=NOT_FOUND,
        language="Khmer" if language == "km" else "English",
    )
    user_message = f"{_format_sources(chunks)}\n\nQuestion: {question}"
    if settings.LLM_PROVIDER == "openai":
        return _ask_openai_compatible(system, user_message)
    return _ask_anthropic(system, user_message)


def _ask_anthropic(system: str, user_message: str) -> str | None:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
    try:
        response = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIError:
        logger.exception("AI model request failed; falling back to FAQ answer")
        return None
    return "".join(block.text for block in response.content if block.type == "text").strip()


def _ask_openai_compatible(system: str, user_message: str) -> str | None:
    """Gemini, Groq, OpenRouter, Ollama… anything with an OpenAI-style chat API."""
    import openai

    # Short timeout so a slow free-tier API falls back to the FAQ answer instead of hanging
    client = openai.OpenAI(
        api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL or None, timeout=30, max_retries=1
    )
    extra = {"reasoning_effort": settings.LLM_REASONING_EFFORT} if settings.LLM_REASONING_EFFORT else {}
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            **extra,
        )
    except openai.OpenAIError:
        logger.exception("AI model request failed; falling back to FAQ answer")
        return None
    return (response.choices[0].message.content or "").strip()
