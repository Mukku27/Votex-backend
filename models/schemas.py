"""
Pydantic schemas for request validation and response models.
"""
from typing import List
from pydantic import BaseModel, Field, validator

class FeedbackRequest(BaseModel):
    feedback: List[str] = Field(..., min_items=1, description="Feedback strings to analyze")

    @validator("feedback", each_item=True)
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Feedback items must not be empty.")
        return v

class SentimentAnalysis(BaseModel):
    positive: int
    neutral: int
    negative: int

class FeedbackResponse(BaseModel):
    summary: str
    sentiment: SentimentAnalysis
    actions: List[str]
    raw_feedback_count: int = Field(..., description="Original number of feedback items")
    clean_feedback_count: int = Field(..., description="Count after PII/inappropriate filtering")
