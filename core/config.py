"""
Configuration loader for environment variables and constants.
"""
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()
