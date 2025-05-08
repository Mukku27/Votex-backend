"""
Entry point for the Professor Feedback Analysis API.
Initializes FastAPI app, middleware, and mounts routes.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.routes import root, report

app = FastAPI(
    title="Professor Feedback Analysis API",
    description="API for analyzing student feedback using LLMs",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(root.router)
app.include_router(report.router, prefix="")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
