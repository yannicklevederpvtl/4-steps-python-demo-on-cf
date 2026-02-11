"""
FastAPI Application - RAG Quotes Demo Main Entry Point

This module creates the main FastAPI application for the RAG Quotes Demo.
It initializes services (embedding model and vector store) on startup and
provides REST API endpoints for similarity search.

Architecture:
1. Service Initialization - Embedding service and vector store setup
2. Quote Loading - Lazy loading of quotes if collection is empty
3. API Endpoints - REST endpoints for similarity search
4. Error Handling - Comprehensive error handling and logging
5. Health Checks - Service availability verification

Cloud Foundry Integration:
- Services are discovered via VCAP_SERVICES environment variable
- PORT environment variable is set automatically by Cloud Foundry
- Logs are captured by Cloud Foundry logging system
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

# Import our modules
from vector_store import initialize_store, clean_store
from embeddings import CustomEmbeddings
from quotes import initialize_quotes
from similarity import search_similar_quotes, search_word_similarity
from utils import CFGenAIService, CFPostgresService

# ============================================================================
# SERVICE CONFIGURATION (Environment Variables with Defaults)
# ============================================================================
# Service names can be configured via environment variables to support
# different service binding names. Defaults match the standard demo setup.
EMBEDDING_SERVICE_NAME = os.getenv("EMBEDDING_SERVICE_NAME", "tanzu-nomic-embed-text")
VECTOR_DB_SERVICE_NAME = os.getenv("VECTOR_DB_SERVICE_NAME", "vector-db")

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Configure logging for Cloud Foundry
# Cloud Foundry captures stdout/stderr, so logging to console is appropriate
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL SERVICE INSTANCES
# ============================================================================
# These will be initialized on application startup
# Global variables are acceptable for this demo application
vectorstore = None
embeddings = None


# ============================================================================
# STARTUP AND SHUTDOWN EVENTS
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - Startup: Initialize services and optionally load quotes
    - Shutdown: Cleanup (if needed)
    
    This replaces the deprecated @app.on_event("startup") pattern.
    """
    # Startup
    logger.info("=" * 70)
    logger.info("Semantic Quotes Demo - Stage 3: Starting Application")
    logger.info("=" * 70)
    logger.info("Stage 3: Semantic Search with Vector Embeddings")
    logger.info("=" * 70)
    
    global vectorstore, embeddings
    
    try:
        # Step 1: Initialize embedding service
        # This verifies that the embedding service is bound and accessible
        logger.info(f"Initializing embedding service: {EMBEDDING_SERVICE_NAME}...")
        embeddings = CustomEmbeddings(EMBEDDING_SERVICE_NAME)
        logger.info("✅ Embedding service initialized successfully")
        
        # Step 2: Initialize vector store
        # This verifies that the vector database service is bound and accessible
        # It also creates the pgvector extension if it doesn't exist
        logger.info(f"Initializing vector store: {VECTOR_DB_SERVICE_NAME}...")
        vectorstore = initialize_store(
            db_service_name=VECTOR_DB_SERVICE_NAME,
            embedding_service_name=EMBEDDING_SERVICE_NAME
        )
        logger.info("✅ Vector store initialized successfully")
        
        # Step 3: Lazy loading of quotes (matching Java example pattern)
        # Check if collection is empty, and if so, load quotes
        # This is done lazily to avoid slow startup times
        # The Java example uses synchronized blocks for thread safety
        logger.info("Checking if quotes need to be loaded...")
        result = initialize_quotes(vectorstore=vectorstore)
        
        if result["status"] == "success":
            logger.info(f"✅ {result['count']} quotes loaded into vector store")
        elif result["status"] == "skipped":
            logger.info("✅ Quotes already loaded, skipping initialization")
        else:
            logger.warning(f"⚠️ Quote initialization returned: {result}")
        
        logger.info("=" * 70)
        logger.info("Application startup complete - Ready to serve requests")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services during startup: {e}", exc_info=True)
        # Don't raise - let the app start and handle errors in endpoints
        # This allows health check to report service status
    
    yield  # Application runs here
    
    # Shutdown (if needed)
    logger.info("Application shutting down...")


# ============================================================================
# FASTAPI APPLICATION INSTANCE
# ============================================================================
app = FastAPI(
    title="Semantic Quotes Demo",
    description="Cloud Foundry demo with Python: Semantic Quotes with PostgreSQL",
    version="1.0.0",
    lifespan=lifespan  # Use lifespan context manager for startup/shutdown
)

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
# HEALTH CHECK ENDPOINT
# ============================================================================
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Foundry.
    
    Verifies that required services are bound and accessible:
    - Embedding service (configurable via EMBEDDING_SERVICE_NAME env var)
    - Vector database (configurable via VECTOR_DB_SERVICE_NAME env var)
    
    Returns:
        dict: Health status with service availability
    """
    logger.debug("Health check requested")
    
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check embedding service
    try:
        embedding_service = CFGenAIService(EMBEDDING_SERVICE_NAME)
        health_status["services"]["embedding"] = "ok"
        logger.debug(f"Embedding service ({EMBEDDING_SERVICE_NAME}): OK")
    except Exception as e:
        health_status["services"]["embedding"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        logger.warning(f"Embedding service check failed: {e}")
    
    # Check database service
    try:
        db_service = CFPostgresService(VECTOR_DB_SERVICE_NAME)
        # Try to get connection URI (validates service is available)
        _ = db_service.get_connection_uri()
        health_status["services"]["database"] = "ok"
        logger.debug("Database service: OK")
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        logger.warning(f"Database service check failed: {e}")
    
    # Check if services are initialized
    if vectorstore is None:
        health_status["services"]["vectorstore"] = "not initialized"
        health_status["status"] = "unhealthy"
    else:
        health_status["services"]["vectorstore"] = "initialized"
    
    if embeddings is None:
        health_status["services"]["embeddings"] = "not initialized"
        health_status["status"] = "unhealthy"
    else:
        health_status["services"]["embeddings"] = "initialized"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
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
        "name": "Semantic Quotes Demo - Stage 3",
        "description": "Cloud Foundry demo with Python: Semantic Quotes with PostgreSQL",
        "version": "1.0.0",
        "stage": 3,
        "features": [
            "Vector similarity search",
            "AI embedding models",
            "PostgreSQL with pgvector",
            "Semantic search capabilities"
        ],
        "endpoints": {
            "root": "/",
            "health": "/health",
            "quotes": "/quotes?topic=<query>",
            "words": "/words",
            "init": "POST /quotes/init",
            "clean": "POST /quotes/clean"
        }
    }


# ============================================================================
# QUOTE SEARCH ENDPOINTS
# ============================================================================
@app.get("/quotes")
async def search_quotes(topic: Optional[str] = None):
    """
    Search for quotes similar to the given topic, or return all quotes.
    
    This endpoint uses vector similarity search to find inspirational quotes
    whose embeddings are most similar to the topic embedding. Results are
    sorted by similarity score (highest first).
    
    Query Parameters:
        topic: Topic or query text to search for similar quotes (optional)
               - If provided: Returns quotes with similarity scores, sorted by relevance
               - If not provided: Returns all quotes without similarity scores
    
    Returns:
        List of quote dictionaries:
            - If topic provided: Each contains text, similarity (0.0 to 1.0), and category
            - If topic not provided: Each contains text and category only
    
    Example Requests:
        GET /quotes                                    # All quotes (no scores)
        GET /quotes?topic=kindness                    # Quotes similar to "kindness"
        GET /quotes?topic=donate%20to%20the%20cancer%20foundation
        GET /quotes?topic=my%20kid%20failed%20his%20math%20class
        GET /quotes?topic=congratulations%20on%20getting%20a%20learning%20AI
        GET /quotes?topic=Inspire%20angry%20customers%20to%20be%20patient
    
    Raises:
        HTTPException: 400 if query is invalid, 503 if services unavailable, 500 for other errors
    """
    # Reinitialize vectorstore if it's None (e.g., after cleanup)
    global vectorstore
    if vectorstore is None:
        logger.info("Vector store not initialized, reinitializing...")
        try:
            vectorstore = initialize_store(
                db_service_name=VECTOR_DB_SERVICE_NAME,
                embedding_service_name=EMBEDDING_SERVICE_NAME
            )
            logger.info("Vector store reinitialized successfully")
        except Exception as e:
            logger.error(f"Failed to reinitialize vector store: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Vector store not available: {str(e)}"
            )
    
    # If no topic provided, return all quotes without similarity scores
    if not topic or not topic.strip():
        logger.info("No topic provided, returning all quotes without similarity scores")
        try:
            # Get all quotes from the vector store using a generic query
            # This retrieves all documents without calculating similarity
            results = vectorstore.similarity_search("", k=24)
            
            # Return quotes without similarity scores
            quotes = []
            for doc in results:
                quotes.append({
                    "text": doc.page_content,
                    "category": doc.metadata.get("category", "Unknown")
                })
            
            logger.info(f"Returned {len(quotes)} quotes (no similarity scores)")
            return quotes
            
        except Exception as e:
            logger.error(f"Error retrieving all quotes: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve quotes: {str(e)}"
            )
    
    # Topic provided - perform similarity search with scores
    logger.info(f"Quote search requested for topic: '{topic}'")
    
    try:
        # Perform similarity search using the global vectorstore
        # This uses the vectorstore initialized on startup for efficiency
        results = search_similar_quotes(
            query=topic,
            vectorstore=vectorstore,
            k=24  # Return all quotes (we have 24 total)
        )
        
        if not results:
            logger.warning(f"No quotes found for topic: '{topic}'. Collection may be empty.")
            # Return empty list rather than error - allows client to handle gracefully
            return []
        
        logger.info(f"Found {len(results)} similar quotes for topic: '{topic}'")
        return results
        
    except ValueError as e:
        logger.error(f"Validation error in quote search: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching quotes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search quotes: {str(e)}"
        )


@app.post("/quotes/init")
async def init_quotes_endpoint(force: bool = False):
    """
    Initialize/load quotes into the database.
    
    This endpoint loads all 24 inspirational quotes into the vector store
    if the collection is empty. If the collection already has quotes and
    force=False, the operation is skipped.
    
    Query Parameters:
        force: If True, reload quotes even if collection has data (default: False)
    
    Returns:
        dict: Status dictionary with:
            - status: "success", "skipped", or "error"
            - message: Human-readable message
            - count: Number of quotes loaded (0 if skipped)
    
    Example Response (success):
        {
            "status": "success",
            "message": "24 quotes loaded",
            "count": 24
        }
    
    Example Response (skipped):
        {
            "status": "skipped",
            "message": "Quotes already loaded",
            "count": 0
        }
    
    Raises:
        HTTPException: 503 if services unavailable, 500 for other errors
    """
    logger.info(f"Quote initialization requested (force={force})")
    
    # Reinitialize vectorstore if it's None (e.g., after cleanup)
    global vectorstore
    if vectorstore is None:
        logger.info("Vector store not initialized, reinitializing...")
        try:
            vectorstore = initialize_store(
                db_service_name=VECTOR_DB_SERVICE_NAME,
                embedding_service_name=EMBEDDING_SERVICE_NAME
            )
            logger.info("Vector store reinitialized successfully")
        except Exception as e:
            logger.error(f"Failed to reinitialize vector store: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Vector store not available: {str(e)}"
            )
    
    try:
        # Initialize quotes using the global vectorstore
        result = initialize_quotes(
            vectorstore=vectorstore,
            force_reload=force
        )
        
        logger.info(f"Quote initialization completed: {result['status']}")
        return result
        
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
    
    This endpoint removes all quotes and embeddings from the collection,
    effectively resetting the database. Useful for demo purposes or
    reinitializing with fresh data.
    
    Returns:
        dict: Status dictionary with:
            - status: "success" or "error"
            - message: Human-readable message
    
    Example Response:
        {
            "status": "success",
            "message": "Database cleaned"
        }
    
    Raises:
        HTTPException: 503 if services unavailable, 500 for other errors
    """
    logger.info("Database clean requested")
    
    try:
        # Clean the vector store collection
        # This removes all documents and embeddings
        clean_store(
            db_service_name=VECTOR_DB_SERVICE_NAME,
            embedding_service_name=EMBEDDING_SERVICE_NAME
        )
        
        # Reinitialize the vectorstore after cleaning
        # This ensures it's ready for immediate use
        global vectorstore
        logger.info("Reinitializing vector store after cleanup...")
        vectorstore = initialize_store(
            db_service_name=VECTOR_DB_SERVICE_NAME,
            embedding_service_name=EMBEDDING_SERVICE_NAME
        )
        
        logger.info("Database cleaned and vector store reinitialized successfully")
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
# WORD SIMILARITY ENDPOINT
# ============================================================================
@app.get("/words")
async def word_similarity():
    """
    Compare predefined word pairs for similarity using embeddings.
    
    This endpoint demonstrates how embeddings capture semantic relationships
    between words. It compares 9 predefined word pairs and returns similarity
    scores calculated using cosine similarity between their embeddings.
    
    The word pairs demonstrate various semantic relationships:
    - Same word (man/man): Perfect similarity (1.0)
    - Related words (man/woman, king/queen): High similarity
    - Synonyms (happy/joyful): High similarity
    - Antonyms (happy/sad): Lower similarity than synonyms
    - Unrelated words (banana/car): Low similarity
    - Cross-language (queen/reine, queen/ملكة): Shows multilingual understanding
    
    Word Pairs:
        1. man vs man (same word)
        2. man vs woman (related)
        3. man vs dirt (unrelated)
        4. king vs queen (related)
        5. queen vs reine (French translation)
        6. queen vs ملكة (Arabic translation)
        7. banana vs car (unrelated)
        8. happy vs joyful (synonyms)
        9. happy vs sad (antonyms)
    
    Returns:
        List of dictionaries, each containing:
            - word1: First word in the pair
            - word2: Second word in the pair
            - similarity: Similarity score (0.0 to 1.0, higher = more similar)
        Results are sorted by similarity (descending - most similar first)
    
    Example Response:
        [
            {
                "word1": "man",
                "word2": "man",
                "similarity": 1.0
            },
            {
                "word1": "happy",
                "word2": "joyful",
                "similarity": 0.85
            },
            {
                "word1": "king",
                "word2": "queen",
                "similarity": 0.78
            },
            ...
        ]
    
    Raises:
        HTTPException: 503 if embedding service unavailable, 500 for other errors
    """
    logger.info("Word similarity comparison requested")
    
    # Validate embeddings service is initialized
    if embeddings is None:
        logger.error("Embeddings service not initialized")
        raise HTTPException(
            status_code=503,
            detail="Embeddings service not available. Service may still be initializing."
        )
    
    try:
        # Use the search_word_similarity function from similarity.py
        # This function uses the predefined word pairs matching the Java example
        # It generates embeddings for each word and calculates cosine similarity
        results = search_word_similarity()
        
        logger.info(f"Computed similarity for {len(results)} word pairs")
        
        # Results are already sorted by similarity (descending) from the function
        return results
        
    except Exception as e:
        logger.error(f"Error computing word similarity: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute word similarity: {str(e)}"
        )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """
    Main entry point for running the FastAPI application.
    
    This is used when running the app directly (e.g., for local testing).
    In Cloud Foundry, uvicorn is called directly via the manifest.
    """
    import uvicorn
    
    # Get port from environment (Cloud Foundry sets this automatically)
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
