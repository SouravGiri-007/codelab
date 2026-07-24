"""
AI Service — Groq integration for chat and news summarization.
Uses the OpenAI-compatible API format via Groq's endpoint.
"""
import logging
from flask import current_app
from openai import OpenAI

logger = logging.getLogger(__name__)


def get_openai_client():
    """Get an OpenAI client configured for Groq."""
    api_key = current_app.config.get('GROQ_API_KEY', '')
    base_url = current_app.config.get('GROQ_BASE_URL', 'https://api.groq.com/openai/v1')
    return OpenAI(api_key=api_key, base_url=base_url)


def chat_completion(messages, model=None, stream=False, max_tokens=2048):
    """
    Send a chat completion request to Groq.

    Args:
        messages: List of dicts with 'role' and 'content'.
        model: Model ID (defaults to DEFAULT_CHAT_MODEL).
        stream: Whether to stream the response.
        max_tokens: Maximum tokens in the response.

    Returns:
        If stream=False: The assistant's reply text.
        If stream=True: A generator yielding text chunks.
    """
    if not model:
        model = current_app.config.get(
            'DEFAULT_CHAT_MODEL',
            'llama-3.1-8b-instant'
        )

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=stream,
        )

        if stream:
            def text_stream():
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
            return text_stream()

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise


def chat_completion_stream(messages, model=None, max_tokens=2048):
    """Alias for streaming chat completion."""
    return chat_completion(messages, model=model, stream=True, max_tokens=max_tokens)


def summarize_news(title, content, model=None):
    """
    Summarize a news article for the CodeLab news feed.

    Args:
        title: Article title.
        content: Article body text.
        model: Model to use (defaults to NEWS_MODEL).

    Returns:
        A 2-3 sentence summary string.
    """
    if not model:
        model = current_app.config.get('NEWS_MODEL', 'llama-3.1-8b-instant')

    # Don't call the LLM with empty content — it produces placeholder/garbage text
    if not content or not content.strip():
        return ''

    messages = [
        {
            'role': 'system',
            'content': 'You are a tech news summarizer. Write a concise 2-3 sentence summary '
                       'of the given tech/coding news article. Focus on what developers need to know. '
                       'Be factual and neutral. Do not add opinions.'
        },
        {
            'role': 'user',
            'content': f'Title: {title}\n\nContent:\n{content[:3000]}'
        }
    ]

    try:
        summary = chat_completion(messages, model=model, max_tokens=300)
        return summary.strip()
    except Exception as e:
        logger.error(f"Failed to summarize news '{title[:50]}': {e}")
        return ''


def get_available_models():
    """Return the list of available chat models from config."""
    return current_app.config.get('CHAT_MODELS', [])