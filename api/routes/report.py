"""
Routes for generating feedback reports and health checks.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

from core.llm import get_groq_client
from models.schemas import FeedbackRequest, FeedbackResponse, SentimentAnalysis
from services.feedback import (
    analyze_feedback,
    comprehensive_analysis,
    summarize_category,
    parse_action_steps,
)

router = APIRouter()

@router.post("/report", response_model=FeedbackResponse)
async def generate_report(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
    client = Depends(get_groq_client),
) -> FeedbackResponse:
    """
    Generate a full feedback report:
    - Redact and filter PII/inappropriate feedback
    - Summarize overall sentiment
    - Provide action steps
    """
    raw_count = len(request.feedback)
    clean_items: List[str] = []

    # Clean and filter
    for text in request.feedback:
        result = analyze_feedback(text, client)
        if not result["contains_inappropriate"] and not result["contains_pii"]:
            clean_items.append(result["cleaned_text"])

    clean_count = len(clean_items)
    if clean_count == 0:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid feedback after filtering.",
        )

    # Comprehensive analysis
    analysis = comprehensive_analysis(clean_items, client)
    summary = analysis.get("summary", "")
    sentiment_counts = analysis.get("sentiment_analysis", {"positive": 0, "neutral": 0, "negative": 0})

    # Action steps
    action_text = summarize_category(
        clean_items,
        "suggest actionable steps for the professor based on feedback",
        client,
    )
    actions = parse_action_steps(action_text)

    return FeedbackResponse(
        summary=summary,
        sentiment=SentimentAnalysis(**sentiment_counts),
        actions=actions,
        raw_feedback_count=raw_count,
        clean_feedback_count=clean_count,
    )

@router.get("/health")
async def health_check() -> dict:
    """
    Simple health check endpoint returning status and model info.
    """
    return {"status": "healthy", "model": settings.MODEL_NAME}
