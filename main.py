import os
import json
import re
import time
import random
from typing import List, Dict, Any, Optional
from collections import defaultdict

# FastAPI and Pydantic imports
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

# Install with: pip install groq
import groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Professor Feedback Analysis API",
    description="API for analyzing student feedback using LLMs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return groq.Groq(api_key=api_key)

# Constants
MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 5

# Pydantic models for request/response validation
class FeedbackRequest(BaseModel):
    feedback: List[str] = Field(..., min_items=1, description="List of feedback strings to analyze")
    
    @validator('feedback')
    def validate_feedback_items(cls, v):
        for item in v:
            if not item or not item.strip():
                raise ValueError("Feedback items cannot be empty")
        return v

class SentimentAnalysis(BaseModel):
    positive: int
    neutral: int
    negative: int

class FeedbackResponse(BaseModel):
    summary: str
    sentiment: SentimentAnalysis
    actions: List[str]
    raw_feedback_count: int = Field(..., description="Number of raw feedback items provided")
    clean_feedback_count: int = Field(..., description="Number of feedback items after cleaning")

# PII redaction patterns
def redact_pii(text: str) -> str:
    patterns = [
        r"\b\d{6,}\b",                              # long numeric sequences
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email addresses
    ]
    for pat in patterns:
        text = re.sub(pat, "[REDACTED]", text)
    return text

# Helper: retry logic for Groq requests
def send_with_retry(call_fn, **kwargs):
    delay = 1
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return call_fn(**kwargs)
        except groq.APIError as e:
            # Retry on rate limits or server errors
            if isinstance(e, groq.RateLimitError) and attempt < MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
                continue
            return None
    return None

# Analysis of individual feedback for PII and inappropriate content
def analyze_feedback(text: str, client: groq.Groq) -> Dict[str, Any]:
    prompt = (
        "You are an expert assistant. Given the student feedback below, "
        "perform these tasks and respond in JSON:\n"
        "1. \"contains_inappropriate\": true/false if profanity.\n"
        "2. \"contains_pii\": true/false if personal identifiers.\n"
        "3. \"cleaned_text\": the feedback with PII redacted as \"[REDACTED]\".\n\n"
        f"Feedback:\n{text}"
    )
    def call():
        return client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.0
        )

    resp = send_with_retry(call)
    if not resp or not getattr(resp, 'choices', None):
        return {
            "contains_inappropriate": False,
            "contains_pii": False,
            "cleaned_text": redact_pii(text)
        }
    raw = resp.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "contains_inappropriate": False,
            "contains_pii": False,
            "cleaned_text": redact_pii(text)
        }

# LLM-based comprehensive feedback analysis
def comprehensive_analysis(all_feedback: List[str], client: groq.Groq) -> Dict[str, Any]:
    if not all_feedback:
        return {
            "summary": "No feedback data available to analyze.",
            "sentiment_analysis": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        }
    
    # Join all feedback items
    joined_feedback = "\n".join([f"- {item}" for item in all_feedback])
    
    prompt = (
        "You are an expert educator and data analyst. Analyze the following student feedback about Professor Jack.\n\n"
        f"Feedback items:\n{joined_feedback}\n\n"
        "Provide your analysis in JSON format with these two sections:\n"
        "1. \"summary\": A comprehensive summary of the overall feedback content, highlighting main themes and patterns.\n"
        "2. \"sentiment_analysis\": Count the number of positive, negative, and neutral comments in the format:\n"
        "   {\n"
        "     \"positive\": [number],\n"
        "     \"neutral\": [number],\n"
        "     \"negative\": [number]\n"
        "   }\n\n"
        "Important: Base your sentiment analysis entirely on your own evaluation of each comment's tone and content, "
        "not on counts provided elsewhere or simple keyword matching. Consider the nuance and context of each feedback item.\n\n"
        "RESPOND ONLY WITH VALID JSON. DO NOT include markdown formatting, code block syntax, or the word 'json' before your output."
    )
    
    def call():
        return client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.0  # Keep deterministic for consistent analysis
        )
    
    resp = send_with_retry(call)
    if not resp or not getattr(resp, 'choices', None):
        return {
            "summary": "Error generating feedback analysis.",
            "sentiment_analysis": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        }
    
    raw = resp.choices[0].message.content
    
    # Clean the response to handle common LLM formatting issues
    # Remove "json" prefix if present
    if raw.strip().startswith("json"):
        raw = raw.strip()[4:].strip()
    
    # Remove markdown code block indicators if present
    if raw.strip().startswith("```") and "```" in raw:
        raw = raw.split("```", 2)[1]
        if raw.strip().startswith("json"):
            raw = raw.strip()[4:].strip()
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # If JSON parsing fails, attempt to extract information from text response
        print(f"JSON parsing failed. Raw response:\n{raw}")
        
        # Attempt to create an approximate structure from the text
        summary = "Error parsing analysis results."
        sentiment = {"positive": 0, "neutral": 0, "negative": 0}
        
        # Try to extract values using regex
        # Look for summary section
        summary_match = re.search(r'"summary":\s*"([^"]*)"', raw)
        if summary_match:
            summary = summary_match.group(1)
        
        # Look for sentiment counts
        positive_match = re.search(r'"positive":\s*(\d+)', raw)
        neutral_match = re.search(r'"neutral":\s*(\d+)', raw)
        negative_match = re.search(r'"negative":\s*(\d+)', raw)
        
        if positive_match:
            sentiment["positive"] = int(positive_match.group(1))
        if neutral_match:
            sentiment["neutral"] = int(neutral_match.group(1))
        if negative_match:
            sentiment["negative"] = int(negative_match.group(1))
        
        return {
            "summary": summary,
            "sentiment_analysis": sentiment
        }

# Summarization helper for thematic analysis and action steps
def summarize_category(items: List[str], role_description: str, client: groq.Groq) -> str:
    if not items:
        return "No feedback available."
    joined = "\n".join(f"- {itm}" for itm in items)
    prompt = (
        "You are an expert educator. Based on the following student feedback about Jack's teaching, "
        f"{role_description}. Provide a concise bullet-point summary.\n\n"
        f"Feedback entries:\n{joined}"
    )
    def call():
        return client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3
        )
    resp = send_with_retry(call)
    if not resp or not getattr(resp, 'choices', None):
        return ""
    return resp.choices[0].message.content.strip()

# Function to parse the action steps from summarized text
def parse_action_steps(text: str) -> List[str]:
    # Split by newline and look for bullet points
    lines = text.split('\n')
    actions = []
    for line in lines:
        line = line.strip()
        # Check for bullet point formats (-, *, •, etc.)
        if line.startswith('-') or line.startswith('*') or line.startswith('•'):
            actions.append(line[1:].strip())
        # If no bullet points found but there are multiple lines, use each line
        elif not actions and len(lines) > 1:
            if line:  # Skip empty lines
                actions.append(line)
    
    # If still no actions found, try to split by sentences
    if not actions and text:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        actions = [s.strip() for s in sentences if s.strip()]
    
    return actions

# Endpoint to generate feedback report
@app.post("/report", response_model=FeedbackResponse)
async def generate_report(
    request: FeedbackRequest,
    client: groq.Groq = Depends(get_groq_client)
):
    try:
        # First, check and clean feedback
        clean_feedback = []
        raw_feedback_count = len(request.feedback)
        
        for fb in request.feedback:
            result = analyze_feedback(fb, client)
            if not result["contains_inappropriate"] and not result["contains_pii"]:
                clean_feedback.append(result["cleaned_text"])
        
        clean_feedback_count = len(clean_feedback)
        
        if clean_feedback_count == 0:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No valid feedback items after filtering inappropriate content and PII"
            )
        
        # Get comprehensive LLM analysis of all clean feedback together
        analysis_result = comprehensive_analysis(clean_feedback, client)
        
        # Fix key names if necessary
        if "sentiment_counts" in analysis_result and "sentiment_analysis" not in analysis_result:
            analysis_result["sentiment_analysis"] = analysis_result["sentiment_counts"]
        
        # Ensure sentiment_analysis exists and has the right structure
        if "sentiment_analysis" not in analysis_result:
            analysis_result["sentiment_analysis"] = {"positive": 0, "neutral": 0, "negative": 0}
        
        # Get additional thematic insights for action steps
        action_steps_text = summarize_category(
            clean_feedback,
            "suggest actionable steps for Jack to enhance his teaching based on student feedback",
            client
        )
        
        # Parse the action steps into a list format
        actions_list = parse_action_steps(action_steps_text)
        
        # Create the response
        response = FeedbackResponse(
            summary=analysis_result["summary"],
            sentiment=SentimentAnalysis(
                positive=analysis_result["sentiment_analysis"]["positive"],
                neutral=analysis_result["sentiment_analysis"]["neutral"],
                negative=analysis_result["sentiment_analysis"]["negative"]
            ),
            actions=actions_list,
            raw_feedback_count=raw_feedback_count,
            clean_feedback_count=clean_feedback_count
        )
        
        return response
    
    except Exception as e:
        # Log the error (in a production environment, use proper logging)
        print(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feedback report: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": MODEL}

# Get API server information
@app.get("/")
async def root():
    return {
        "app": "Professor Feedback Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "/report": "POST - Generate a feedback analysis report",
            "/health": "GET - Check API health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Start the API server
    uvicorn.run(app, host="0.0.0.0", port=8000)