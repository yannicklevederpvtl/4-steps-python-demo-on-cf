"""
FastAPI Application - Random Quotes (In-Memory)

This is the main FastAPI application.
It demonstrates basic Cloud Foundry deployment concepts:
- cf push: Deploying applications to Cloud Foundry
- cf logs: Viewing application logs
- cf routes: Managing application routes
- Health checks: Application health monitoring

This stage uses in-memory data (no database or services required).

Cloud Foundry Basics:
- cf push: Deploys the application to Cloud Foundry
  Example: cf push -f manifest-pip.yml
- cf logs: Streams application logs in real-time
  Example: cf logs cf-quotes-random-01 --recent
- cf routes: Shows all routes (URLs) for the application
  Example: cf routes
- Health checks: Cloud Foundry monitors the /health endpoint
  to ensure the application is running correctly
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict

# Import our quotes module
from quotes import get_random_quote, get_all_quotes

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Configure logging for Cloud Foundry
# Cloud Foundry captures stdout/stderr, so logging to console is appropriate
# Using consistent format across all stages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - Startup: Log application start (no services to initialize in this in-memory application)
    - Shutdown: Log application shutdown
    
    This replaces the deprecated @app.on_event("startup") pattern.
    For consistency across stages, we use the same pattern even though
    It doesn't require service initialization.
    """
    # Startup
    logger.info("=" * 70)
    logger.info("Random Quotes Demo (In-memory): Starting Application")
    logger.info("=" * 70)
    logger.info("In-Memory Quotes (No services required)")
    logger.info("=" * 70)
    logger.info("Application startup complete - Ready to serve requests")
    logger.info("=" * 70)
    
    yield  # App runs here - handles requests
    
    # Shutdown
    logger.info("=" * 70)
    logger.info("Application shutting down...")
    logger.info("=" * 70)

# ============================================================================
# FASTAPI APPLICATION INSTANCE
# ============================================================================
app = FastAPI(
    title="Random Quotes Demo (In-memory)",
    description="Cloud Foundry demo with Python: In-Memory Random Quotes",
    version="1.0.0",
    lifespan=lifespan  # Use lifespan context manager for startup/shutdown
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================
# Configure CORS (if needed for frontend access)
# For demo purposes, allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ERROR HANDLING MIDDLEWARE
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    
    Catches all exceptions, logs them with full context, and returns
    a user-friendly error response. This ensures errors are properly
    logged in Cloud Foundry logs.
    
    Consistent error format across all stages.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An error occurred"
        }
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================
@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        dict: API information and available endpoints
    """
    return {
        "name": "Random Quotes Demo",
        "description": "Cloud Foundry demo with Python: In-Memory Random Quotes",
        "version": "1.0.0",
        "stage": 1,
        "features": [
            "In-memory quotes storage",
            "No database required",
            "No service bindings required"
        ],
        "endpoints": {
            "root": "/",
            "health": "/health",
            "random_quote": "/quote",
            "all_quotes": "/quotes"
        }
    }


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Foundry.
    
    Cloud Foundry uses this endpoint to monitor application health.
    Returns a simple healthy status since it has no services to check.
    
    Returns:
        dict: Health status with "status": "healthy"
    
    Note: Consistent format with Stage 3, but without services object
    since it has no service bindings.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy"
        }
    )


# ============================================================================
# QUOTE ENDPOINTS
# ============================================================================
@app.get("/quote")
async def get_random_quote_endpoint():
    """
    Get a random quote from the in-memory quotes array.
    
    This endpoint demonstrates simple in-memory data access.
    No database or services required - purely in-memory operation.
    
    Returns:
        dict: A random quote with 'text' and 'category' keys
    
    Example Response:
        {
            "text": "Education is the most powerful weapon...",
            "category": "Importance of Education"
        }
    """
    try:
        quote = get_random_quote()
        logger.info(f"Returning random quote from category: {quote['category']}")
        return quote
    except Exception as e:
        logger.error(f"Error getting random quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve random quote: {str(e)}"
        )


@app.get("/quotes")
async def get_all_quotes_endpoint():
    """
    Get all quotes from the in-memory quotes array.
    
    Returns all 24 inspirational quotes organized in 5 categories.
    This endpoint demonstrates retrieving all data from memory.
    
    Returns:
        List[dict]: List of all quotes, each with 'text' and 'category' keys
    
    Example Response:
        [
            {
                "text": "Education is the most powerful weapon...",
                "category": "Importance of Education"
            },
            ...
        ]
    """
    try:
        quotes = get_all_quotes()
        logger.info(f"Returning all {len(quotes)} quotes")
        return quotes
    except Exception as e:
        logger.error(f"Error getting all quotes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve quotes: {str(e)}"
        )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    # For local development
    # In Cloud Foundry, the PORT environment variable is set automatically
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
