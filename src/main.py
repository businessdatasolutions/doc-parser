"""
FastAPI application entry point for Document Search & Retrieval System.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.utils.logging import setup_logging, get_logger, set_request_id


# Set up logging
setup_logging(log_level=settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Document Search & Retrieval System")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"PDF Storage Path: {settings.pdf_storage_path}")
    yield
    # Shutdown
    logger.info("Shutting down Document Search & Retrieval System")


# Initialize FastAPI application
app = FastAPI(
    title="Document Search & Retrieval System",
    description="AI-powered document search system for sales department",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Middleware to add request ID to each request for tracking.
    """
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status and version information
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Document Search & Retrieval System"
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Serve the search UI HTML page.

    Returns:
        FileResponse: HTML search interface
    """
    static_dir = Path(__file__).parent.parent / "static"
    index_path = static_dir / "index.html"

    if index_path.exists():
        return FileResponse(index_path)

    # Fallback to API info if HTML not found
    return {
        "service": "Document Search & Retrieval System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api_version": "/api/v1"
    }


@app.get("/pitch.html", tags=["Root"])
async def pitch():
    """
    Serve the pitch presentation HTML page.

    Returns:
        FileResponse: Pitch presentation with personalization support
    """
    static_dir = Path(__file__).parent.parent / "static"
    pitch_path = static_dir / "pitch.html"

    if pitch_path.exists():
        return FileResponse(pitch_path)

    return {"error": "Pitch page not found"}


# Mount static files directory
static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# API v1 routers
from src.api.search import router as search_router
from src.api.documents import router as documents_router
from src.api.feedback import router as feedback_router

app.include_router(search_router)
app.include_router(documents_router)
app.include_router(feedback_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
