"""
Business logic for feedback processing:
- PII/inappropriate detection & redaction
- LLM-driven analysis, summarization, and parsing
"""
import json
import re
from typing import Any, Dict, List

from core.llm import send_with_retry
from core.config import settings
from utils.redaction import redact_pii

import groq

def analyze_feedback(text: str, client: groq.Groq) -> Dict[str, Any]:
    """
    Check for inappropriate content or PII via LLM, fallback to regex redaction.
    """
    prompt = (
        "You are an assistant. For the feedback below, output JSON with:\n"
        '1. "contains_inappropriate": true/false\n'
        '2. "contains_pii": true/false\n'
        '3. "cleaned_text": with PII redacted to "[REDACTED]"\n\n'
        f"Feedback:\n{text}"
    )
    def call(): return client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.0,
    )

    try:
        resp = send_with_retry(call)
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        return data
    except Exception:
        return {
            "contains_inappropriate": False,
            "contains_pii": False,
            "cleaned_text": redact_pii(text),
        }

def comprehensive_analysis(feedbacks: List[str], client: groq.Groq) -> Dict[str, Any]:
    """
    Use LLM to summarize and count sentiment across multiple feedback items.
    """
    if not feedbacks:
        return {"summary": "", "sentiment_analysis": {"positive": 0, "neutral": 0, "negative": 0}}

    joined = "\n".join(f"- {f}" for f in feedbacks)
    prompt = (
        "Analyze the following feedback and return JSON:\n"
        '1. "summary": overall themes\n'
        '2. "sentiment_analysis": {positive, neutral, negative}\n\n'
        f"{joined}"
    )

    def call(): return client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.0,
    )

    resp = send_with_retry(call)
    raw = resp.choices[0].message.content
    # strip markdown or code fences
    raw = re.sub(r"```json|```", "", raw, flags=re.IGNORECASE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback empty
        return {"summary": "", "sentiment_analysis": {"positive": 0, "neutral": 0, "negative": 0}}

def summarize_category(items: List[str], role_description: str, client: groq.Groq) -> str:
    """
    Summarize a list of feedback items into bullet points for action steps.
    """
    if not items:
        return ""
    joined = "\n".join(f"- {i}" for i in items)
    prompt = (
        f"You are an expert. {role_description}. Provide bullet-point suggestions.\n\n{joined}"
    )

    def call(): return client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.3,
    )

    resp = send_with_retry(call)
    return resp.choices[0].message.content.strip() if resp else ""

def parse_action_steps(text: str) -> List[str]:
    """
    Parse LLM-generated bullet text into a list of action strings.
    """
    lines = text.splitlines()
    actions: List[str] = []
    for ln in lines:
        ln = ln.strip()
        if ln.startswith(("-", "*", "•")):
            actions.append(ln[1:].strip())
    # fallback sentences
    if not actions and text:
        actions = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s]
    return actions
