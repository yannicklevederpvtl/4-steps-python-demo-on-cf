"""
FastAPI Application: Random Quotes with PostgreSQL

This is the main FastAPI application for Stage 2 of the demo.
It demonstrates Cloud Foundry service marketplace and binding concepts:
- cf marketplace: Browse available services
- cf create-service: Create service instances
- cf bind-service: Bind services to applications
- VCAP_SERVICES: Access service credentials
- cfenv: Python library for service discovery

This stage uses PostgreSQL database for quote storage (service binding required).

Cloud Foundry Service Binding:
- Services are discovered via VCAP_SERVICES environment variable
- CFPostgresService (from utils) handles service discovery
- Database connection is established using service credentials
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional

# Import our modules
from quotes import (
    get_random_quote_from_db,
    get_all_quotes_from_db,
    load_quotes_to_db
)
from database import initialize_quotes_table, clean_quotes_table
from utils import CFPostgresService

# ============================================================================
# SERVICE CONFIGURATION (Environment Variables with Defaults)
# ============================================================================
# Service name can be configured via environment variable to support
# different service binding names. Default matches the standard demo setup.
VECTOR_DB_SERVICE_NAME = os.getenv("VECTOR_DB_SERVICE_NAME", "vector-db")

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
    - Startup: Initialize database connection and table
    - Shutdown: Log application shutdown
    
    This replaces the deprecated @app.on_event("startup") pattern.
    """
    # Startup
    logger.info("=" * 70)
    logger.info("Random Quotes Demo: Starting Application")
    logger.info("=" * 70)
    logger.info("PostgreSQL Database Integration")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize database table
        # This verifies that the PostgreSQL service is bound and accessible
        logger.info(f"Initializing database connection: {VECTOR_DB_SERVICE_NAME}...")
        initialize_quotes_table(VECTOR_DB_SERVICE_NAME)
        logger.info("✅ Database table initialized successfully")
        
        # Step 2: Optionally load quotes if database is empty
        # This is lazy loading - quotes will be loaded on first request or via /quotes/init
        logger.info("Database ready - Quotes will be loaded on demand or via /quotes/init")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        logger.warning("Application will start, but database operations may fail")
        logger.warning("Make sure PostgreSQL service is bound to the application")
    
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
    title="Random Quotes Demo",
    description="Cloud Foundry demo with Python: Random Quotes with PostgreSQL",
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
        "description": "Cloud Foundry demo with Python: Random Quotes with PostgreSQL",
        "version": "1.0.0",
        "stage": 2,
        "features": [
            "PostgreSQL database storage",
            "Cloud Foundry service binding",
            "Service marketplace integration"
        ],
        "endpoints": {
            "root": "/",
            "health": "/health",
            "random_quote": "/quote",
            "all_quotes": "/quotes",
            "init_quotes": "POST /quotes/init",
            "clean_quotes": "POST /quotes/clean"
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
    Verifies that the PostgreSQL service is bound and accessible.
    
    Returns:
        dict: Health status with "status": "healthy" and services status
    
    Note: Consistent format with Stage 3, including services object
    for database service verification.
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check database service
    try:
        db_service = CFPostgresService(VECTOR_DB_SERVICE_NAME)
        # Try to get connection URI (validates service is available)
        _ = db_service.get_connection_uri()
        health_status["services"]["database"] = "ok"
        logger.debug("Database service: OK")
    except ValueError as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        logger.warning(f"Database service check failed: {e}")
    
    return JSONResponse(
        status_code=200,
        content=health_status
    )


# ============================================================================
# QUOTE ENDPOINTS
# ============================================================================
@app.get("/quote")
async def get_random_quote_endpoint():
    """
    Get a random quote from PostgreSQL database.
    
    This endpoint retrieves a random quote from the database.
    If the database is empty, returns a 404 error.
    
    Returns:
        dict: A random quote with 'text' and 'category' keys
    
    Example Response:
        {
            "text": "Education is the most powerful weapon...",
            "category": "Importance of Education"
        }
    """
    try:
        quote = get_random_quote_from_db(VECTOR_DB_SERVICE_NAME)
        if quote is None:
            raise HTTPException(
                status_code=404,
                detail="No quotes found in database. Please initialize quotes using POST /quotes/init"
            )
        logger.info(f"Returning random quote from category: {quote['category']}")
        return quote
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve random quote: {str(e)}"
        )


@app.get("/quotes")
async def get_all_quotes_endpoint():
    """
    Get all quotes from PostgreSQL database.
    
    Returns all quotes stored in the database.
    If the database is empty, returns an empty list.
    
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
        quotes = get_all_quotes_from_db(VECTOR_DB_SERVICE_NAME)
        logger.info(f"Returning all {len(quotes)} quotes from database")
        return quotes
    except Exception as e:
        logger.error(f"Error getting all quotes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve quotes: {str(e)}"
        )


# ============================================================================
# DATABASE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/quotes/init")
async def init_quotes_endpoint(force: bool = False):
    """
    Initialize/load quotes into the database.
    
    This endpoint loads all 24 quotes from the in-memory dataset into
    the PostgreSQL database. If quotes already exist and force=False,
    the operation is skipped.
    
    Args:
        force: If True, reloads quotes even if they already exist (default: False)
    
    Returns:
        dict: Success message with count of loaded quotes
    
    Example Request:
        POST /quotes/init?force=false
    
    Example Response:
        {
            "status": "success",
            "message": "Quotes loaded successfully",
            "count": 24
        }
    """
    logger.info(f"Quote initialization requested (force={force})")
    
    try:
        count = load_quotes_to_db(VECTOR_DB_SERVICE_NAME, force=force)
        logger.info(f"Successfully initialized {count} quote(s) in database")
        return {
            "status": "success",
            "message": "Quotes loaded successfully",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error initializing quotes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize quotes: {str(e)}"
        )


@app.post("/quotes/clean")
async def clean_quotes_endpoint():
    """
    Clean/reset the quotes database.
    
    This endpoint deletes all quotes from the database, effectively
    resetting the database. Useful for demo purposes or reinitialization.
    
    Returns:
        dict: Success message
    
    Example Response:
        {
            "status": "success",
            "message": "Database cleaned"
        }
    """
    logger.info("Database clean requested")
    
    try:
        clean_quotes_table(VECTOR_DB_SERVICE_NAME)
        logger.info("Database cleaned successfully")
        return {
            "status": "success",
            "message": "Database cleaned"
        }
    except Exception as e:
        logger.error(f"Error cleaning database: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clean database: {str(e)}"
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
