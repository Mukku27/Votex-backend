"""
Groq LLM client initialization and retry logic.
"""
import time
from typing import Any, Callable, Optional

import groq
from groq import APIError, RateLimitError

from core.config import settings

def get_groq_client() -> groq.Groq:
    """
    Initialize and return a Groq client.
    Raises ValueError if API key is missing.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    return groq.Groq(api_key=settings.GROQ_API_KEY)

def send_with_retry(call_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[Any]:
    """
    Retry Groq API calls up to MAX_RETRIES on RateLimitError.
    """
    delay = 1.0
    for attempt in range(1, settings.MAX_RETRIES + 1):
        try:
            return call_fn(*args, **kwargs)
        except RateLimitError:
            if attempt < settings.MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except APIError:
            # Non-retryable or final failure
            raise
    return None
