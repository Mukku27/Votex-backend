"""
Root route for basic API info.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def read_root() -> dict:
    """
    Returns a list of available endpoints and basic metadata.
    """
    return {
        "app": "Professor Feedback Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "/report": "POST - Generate a feedback analysis report",
            "/health": "GET - Check API health",
        },
    }
