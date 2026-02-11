"""
FastMCP Server - Stage 4: MCP Protocol Integration

This module creates a standalone FastMCP server for the Quotes Demo.
FastMCP is a complete MCP server framework that replaces FastAPI for MCP applications.

================================================================================
FASTMCP STANDALONE SERVER ARCHITECTURE
================================================================================

FastMCP + FastAPI Integration:
-------------------------------
Stage 4 uses FastMCP integrated with FastAPI to provide both MCP protocol
endpoints and traditional REST endpoints (like /health). This provides:

1. **FastMCP HTTP/SSE Integration:**
   - FastMCP provides http_app() method that returns an ASGI application
   - Mount the MCP server to FastAPI using app.mount("/mcp", mcp_app)
   - MCP protocol endpoints available at /mcp/* (HTTP/SSE transport)
   - FastMCP handles all MCP protocol complexity automatically

2. **Automatic MCP Protocol Handling:**
   - JSON-RPC message parsing and formatting
   - HTTP/SSE transport setup
   - MCP protocol method routing (initialize, tools/list, tools/call)
   - Error handling in MCP-compliant format

3. **Simplified Tool Registration:**
   - Just use @mcp.tool decorator on functions
   - FastMCP automatically:
     * Generates tool schemas from Python type hints
     * Registers tools with MCP protocol
     * Routes tool calls to decorated functions
     * Formats responses as JSON-RPC messages

4. **Combined Server:**
   - FastAPI handles REST endpoints (/, /health)
   - FastMCP handles MCP protocol endpoints (/mcp/*)
   - Both run on the same port (from PORT environment variable)
   - Cloud Foundry can use port-based health checks

================================================================================
SERVER STRUCTURE
================================================================================

1. FastMCP Server Instance:
   - Created with: `mcp = FastMCP("Quotes Demo - Stage 4")`
   - Single instance handles all MCP protocol communication

2. Service Initialization:
   - initialize_services() function sets up embeddings and vector store
   - Called before mcp.run() to ensure services are ready
   - Global variables (vectorstore, embeddings) are used by tools

3. Tool Registration:
   - Tools are registered using @mcp.tool decorator
   - FastMCP automatically exposes them via MCP protocol
   - Tools can access global service instances

4. Server Execution:
   - Create MCP HTTP app with mcp.http_app(path='/mcp')
   - Create FastAPI app with mcp_app.lifespan (critical for MCP session management)
   - Mount MCP app to FastAPI with app.mount("/mcp", mcp_app)
   - Start combined server with uvicorn.run(app, ...)
   - Server listens on PORT environment variable (Cloud Foundry compatible)

================================================================================
MCP TOOLS EXPOSED
================================================================================

The server exposes 4 MCP tools for quote functionality:
- search_quotes: Semantic search for quotes by topic
- get_random_quote: Get a random quote
- get_all_quotes: Get all quotes
- compare_words: Compare word similarity

All tools are automatically available via MCP protocol over HTTP/SSE.

================================================================================
CLOUD FOUNDRY INTEGRATION
================================================================================

- Services are discovered via VCAP_SERVICES environment variable
- PORT environment variable is set automatically by Cloud Foundry
- Logs are captured by Cloud Foundry logging system
- Health checks via GET /health endpoint (REST)
- MCP protocol available at /mcp/* endpoints (HTTP/SSE)

================================================================================
ERROR HANDLING
================================================================================

FastMCP provides automatic error handling:
- Service initialization errors are logged but don't prevent server startup
- Tools handle errors gracefully and return MCP-compliant error responses
- FastMCP formats all errors as JSON-RPC error messages

================================================================================
"""
import os
import logging
import random
from typing import List, Dict, Any, Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

# Import our modules
from vector_store import initialize_store
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
# Using consistent format across all stages
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
# Tools will access these instances when called
vectorstore = None
embeddings = None

# ============================================================================
# FASTAPI APPLICATION INSTANCE
# ============================================================================
# FastAPI app will be created later with MCP lifespan
# This allows us to mount the MCP server properly
app = None  # Will be created in main() with mcp_app.lifespan

# ============================================================================
# FASTMCP SERVER INSTANCE
# ============================================================================
# Initialize FastMCP and integrate with FastAPI
# 
# FastMCP handles all MCP protocol complexity automatically:
# - JSON-RPC message format (parsing and formatting)
# - initialize method (MCP handshake)
# - tools/list method (tool discovery)
# - tools/call method routing (tool execution)
# - HTTP/SSE transport (via FastAPI integration)
# - Error handling (MCP-compliant error responses)
#
# FastMCP integrates with FastAPI to provide:
# - MCP protocol endpoints (HTTP/SSE)
# - Traditional REST endpoints (like /health)
# - All on the same HTTP server
mcp = FastMCP("Quotes Demo - Stage 4")


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================
def initialize_services():
    """
    Initialize Cloud Foundry services (embeddings and vector store).
    
    This function initializes the embedding service and vector store,
    and optionally loads quotes if the collection is empty.
    
    This is called before starting the FastMCP server to ensure services
    are ready when tools are called.
    
    Raises:
        ValueError: If services are not bound or unavailable
        Exception: If initialization fails
    """
    global vectorstore, embeddings
    
    logger.info("=" * 70)
    logger.info("Semantic Quotes MCP Server - Stage 4: Starting Application")
    logger.info("=" * 70)
    logger.info("Stage 4: MCP Protocol Integration with FastMCP")
    logger.info("=" * 70)
    
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
        logger.info("Checking if quotes need to be loaded...")
        result = initialize_quotes(vectorstore=vectorstore)
        
        if result["status"] == "success":
            logger.info(f"✅ {result['count']} quotes loaded into vector store")
        elif result["status"] == "skipped":
            logger.info("✅ Quotes already loaded, skipping initialization")
        else:
            logger.warning(f"⚠️ Quote initialization returned: {result}")
        
        logger.info("=" * 70)
        logger.info("Services initialized - FastMCP server ready to start")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services during startup: {e}", exc_info=True)
        logger.error("⚠️ Server will start but tools may fail until services are available")
        logger.error("⚠️ MCP clients can still connect and discover tools")
        logger.error("⚠️ Tools will attempt to reinitialize services when called")
        # Don't raise - let the server start and handle errors in tools
        # This allows MCP clients to connect and see available tools
        # Tools will handle service errors when called and attempt reinitialization


# ============================================================================
# MCP TOOLS
# ============================================================================
# Tools are registered using @mcp.tool decorator
# FastMCP automatically:
# - Generates tool schemas from type hints
# - Handles tool registration with MCP protocol
# - Routes tool calls to the decorated functions
# - Formats responses as MCP-compliant JSON-RPC messages
#
# All tools use the global vectorstore and embeddings instances
# initialized during startup. FastMCP handles all protocol complexity.


@mcp.tool
def search_quotes(topic: str, k: int = 10) -> List[Dict[str, Any]]:
    """
    Search for inspirational quotes by topic using semantic similarity.
    
    This tool uses vector embeddings to find quotes that are semantically
    similar to the given topic. Results are sorted by similarity score
    (highest first), showing how closely each quote matches the topic.
    
    Args:
        topic: The topic or query text to search for (e.g., "education", "kindness", "hard work")
        k: Number of quotes to return (default: 10, max: 24)
    
    Returns:
        List of quote dictionaries, each containing:
        - text: The quote text
        - similarity: Similarity score (0.0 to 1.0, higher = more similar)
        - category: Quote category (e.g., "Importance of Education")
    
    Example:
        search_quotes(topic="learning", k=5)
        # Returns top 5 quotes most similar to "learning"
    """
    global vectorstore
    
    # Validate inputs
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")
    
    if k < 1:
        raise ValueError("k must be at least 1")
    
    if k > 24:
        k = 24  # Limit to available quotes
        logger.warning(f"k value limited to 24 (total quotes available)")
    
    # Ensure vectorstore is initialized
    if vectorstore is None:
        logger.warning("Vector store not initialized, attempting to initialize...")
        try:
            vectorstore = initialize_store(
                db_service_name=VECTOR_DB_SERVICE_NAME,
                embedding_service_name=EMBEDDING_SERVICE_NAME
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
            raise Exception(f"Vector store not available: {str(e)}") from e
    
    try:
        # Use the existing search_similar_quotes function
        # It handles vector similarity search and converts distance to similarity
        results = search_similar_quotes(
            query=topic,
            vectorstore=vectorstore,
            k=k
        )
        
        logger.info(f"Found {len(results)} quotes for topic: '{topic}'")
        return results
        
    except Exception as e:
        logger.error(f"Error searching quotes: {e}", exc_info=True)
        raise Exception(f"Failed to search quotes: {str(e)}") from e


@mcp.tool
def get_random_quote() -> Dict[str, Any]:
    """
    Get a random inspirational quote from the database.
    
    This tool retrieves a single random quote from the vector store.
    The quote is selected randomly from all available quotes.
    
    Returns:
        Dictionary containing:
        - text: The quote text
        - category: Quote category (e.g., "Importance of Education")
    
    Example:
        get_random_quote()
        # Returns a random quote like:
        # {"text": "Education is the most powerful weapon...", "category": "Importance of Education"}
    """
    global vectorstore
    
    # Ensure vectorstore is initialized
    if vectorstore is None:
        logger.warning("Vector store not initialized, attempting to initialize...")
        try:
            vectorstore = initialize_store(
                db_service_name=VECTOR_DB_SERVICE_NAME,
                embedding_service_name=EMBEDDING_SERVICE_NAME
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
            raise Exception(f"Vector store not available: {str(e)}") from e
    
    try:
        # Get all quotes and pick one randomly
        # Using similarity_search with empty query and k=24 to get all quotes
        results = vectorstore.similarity_search("", k=24)
        
        if not results:
            raise ValueError("No quotes found in database. Please initialize quotes first.")
        
        # Pick a random quote
        random_doc = random.choice(results)
        
        quote = {
            "text": random_doc.page_content,
            "category": random_doc.metadata.get("category", "Unknown")
        }
        
        logger.info(f"Returned random quote from category: {quote['category']}")
        return quote
        
    except Exception as e:
        logger.error(f"Error getting random quote: {e}", exc_info=True)
        raise Exception(f"Failed to get random quote: {str(e)}") from e


@mcp.tool
def get_all_quotes() -> List[Dict[str, Any]]:
    """
    Get all inspirational quotes from the database.
    
    This tool retrieves all quotes stored in the vector store.
    Quotes are returned without similarity scores since no search query is provided.
    
    Returns:
        List of quote dictionaries, each containing:
        - text: The quote text
        - category: Quote category (e.g., "Importance of Education")
    
    Example:
        get_all_quotes()
        # Returns all 24 quotes from the database
    """
    global vectorstore
    
    # Ensure vectorstore is initialized
    if vectorstore is None:
        logger.warning("Vector store not initialized, attempting to initialize...")
        try:
            vectorstore = initialize_store(
                db_service_name=VECTOR_DB_SERVICE_NAME,
                embedding_service_name=EMBEDDING_SERVICE_NAME
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
            raise Exception(f"Vector store not available: {str(e)}") from e
    
    try:
        # Get all quotes using similarity_search with empty query
        # This retrieves all documents without calculating similarity
        results = vectorstore.similarity_search("", k=24)
        
        if not results:
            logger.warning("No quotes found in database")
            return []
        
        # Convert to list of dictionaries (without similarity scores)
        quotes = []
        for doc in results:
            quotes.append({
                "text": doc.page_content,
                "category": doc.metadata.get("category", "Unknown")
            })
        
        logger.info(f"Returned {len(quotes)} quotes")
        return quotes
        
    except Exception as e:
        logger.error(f"Error getting all quotes: {e}", exc_info=True)
        raise Exception(f"Failed to get all quotes: {str(e)}") from e


@mcp.tool
def compare_words(word1: str, word2: str) -> Dict[str, Any]:
    """
    Compare two words for semantic similarity using embeddings.
    
    This tool generates embeddings for two words and calculates their
    cosine similarity. The similarity score indicates how semantically
    related the words are (0.0 = unrelated, 1.0 = identical meaning).
    
    This is useful for understanding how embeddings capture semantic
    relationships between words, such as:
    - Synonyms (happy/joyful) have high similarity
    - Antonyms (happy/sad) have lower similarity
    - Unrelated words (banana/car) have very low similarity
    - Same word (man/man) has perfect similarity (1.0)
    
    Args:
        word1: First word to compare
        word2: Second word to compare
    
    Returns:
        Dictionary containing:
        - word1: First word
        - word2: Second word
        - similarity: Similarity score (0.0 to 1.0, higher = more similar)
    
    Example:
        compare_words(word1="king", word2="queen")
        # Returns: {"word1": "king", "word2": "queen", "similarity": 0.85}
    """
    global embeddings
    
    # Validate inputs
    if not word1 or not word1.strip():
        raise ValueError("word1 cannot be empty")
    
    if not word2 or not word2.strip():
        raise ValueError("word2 cannot be empty")
    
    # Ensure embeddings is initialized
    if embeddings is None:
        logger.warning("Embeddings not initialized, attempting to initialize...")
        try:
            embeddings = CustomEmbeddings(EMBEDDING_SERVICE_NAME)
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}", exc_info=True)
            raise Exception(f"Embedding service not available: {str(e)}") from e
    
    try:
        # Use the existing search_word_similarity function with a single pair
        # It handles embedding generation and similarity calculation
        results = search_word_similarity(word_pairs=[(word1, word2)])
        
        if not results:
            raise ValueError("Failed to compute word similarity")
        
        # Return the first (and only) result
        result = results[0]
        
        logger.info(f"Compared '{word1}' and '{word2}': similarity = {result['similarity']:.4f}")
        return result
        
    except Exception as e:
        logger.error(f"Error comparing words: {e}", exc_info=True)
        raise Exception(f"Failed to compare words: {str(e)}") from e


# ============================================================================
# REST API ENDPOINTS
# ============================================================================
# Traditional REST endpoints for Cloud Foundry health checks and API info
# These work alongside MCP protocol endpoints

# Root and health endpoints will be added to app in main()
# They need to be defined as functions that can be registered after app creation
def register_rest_endpoints(app_instance):
    """
    Register REST endpoints on the FastAPI app instance.
    This is called after the app is created with MCP lifespan.
    """
    @app_instance.get("/")
    async def root():
        """
        Root endpoint providing API information.
        
        Returns:
            dict: API information and available endpoints
        """
        logger.info("Root endpoint requested")
        return {
            "name": "Quotes Demo - Stage 4",
            "description": "Cloud Foundry demo with Python: Semantic Quotes MCP Server",
            "version": "1.0.0",
            "stage": 4,
            "features": [
                "MCP Protocol (HTTP/SSE)",
                "AI Embedding Service integration",
                "Vector database (PostgreSQL + pgvector)",
                "Semantic similarity search"
            ],
            "endpoints": {
                "root": "/",
                "health": "/health",
                "mcp": "/mcp/* (MCP protocol endpoints)"
            },
            "mcp_tools": [
                "search_quotes",
                "get_random_quote",
                "get_all_quotes",
                "compare_words"
            ]
        }
    
    @app_instance.get("/health")
    async def health_check():
        """
        Health check endpoint for Cloud Foundry.
        
        Verifies that required services are bound and accessible:
        - Embedding service (configurable via EMBEDDING_SERVICE_NAME env var)
        - Vector database (configurable via VECTOR_DB_SERVICE_NAME env var)
        
        Returns:
            JSONResponse: Health status with service availability
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
# HTTP/SSE TRANSPORT VERIFICATION
# ============================================================================
def verify_transport_configuration():
    """
    Verify FastMCP HTTP/SSE transport configuration.
    
    FastMCP automatically handles HTTP/SSE transport when mcp.run() is called.
    This function verifies the configuration is correct for Cloud Foundry deployment.
    
    FastMCP automatically:
    - Creates HTTP server using uvicorn internally
    - Handles PORT environment variable (Cloud Foundry sets this automatically)
    - Creates MCP protocol endpoints for client communication
    - Formats responses as Server-Sent Events (SSE) with single event per request
    - Handles JSON-RPC message format automatically
    
    Returns:
        dict: Configuration verification status
    """
    port = os.getenv("PORT", "8080")  # Default port if not set (for local testing)
    
    logger.info("=" * 70)
    logger.info("Verifying FastMCP HTTP/SSE Transport Configuration")
    logger.info("=" * 70)
    logger.info(f"PORT environment variable: {port}")
    logger.info("FastMCP will use this port for HTTP/SSE server")
    logger.info("=" * 70)
    logger.info("HTTP/SSE Transport Features (automatic):")
    logger.info("  ✓ HTTP server (uvicorn-based)")
    logger.info("  ✓ Server-Sent Events (SSE) support")
    logger.info("  ✓ Single event per request (stateless)")
    logger.info("  ✓ JSON-RPC message handling")
    logger.info("  ✓ MCP protocol endpoints")
    logger.info("  ✓ Tool routing and execution")
    logger.info("=" * 70)
    
    return {
        "port": port,
        "transport": "HTTP/SSE",
        "status": "configured",
        "features": {
            "http_server": True,
            "sse_support": True,
            "single_event_per_request": True,
            "jsonrpc_handling": True,
            "mcp_endpoints": True
        }
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    """
    Main entry point for the FastMCP + FastAPI combined server.
    
    Initializes services first, then creates and mounts FastMCP to FastAPI.
    The combined server provides both REST endpoints and MCP protocol endpoints.
    
    FastMCP + FastAPI Integration:
    ------------------------------
    Using FastMCP v2's http_app() method:
    
    1. Create MCP HTTP App:
       - mcp.http_app(path='/mcp') returns an ASGI application
       - This app handles all MCP protocol endpoints at /mcp/*
       - Includes HTTP/SSE transport, JSON-RPC handling, tool routing
    
    2. Mount to FastAPI:
       - Create FastAPI app with mcp_app.lifespan (critical for MCP sessions)
       - Mount MCP app: app.mount("/mcp", mcp_app)
       - Add REST endpoints (/, /health) to FastAPI app
    
    3. Combined Server:
       - Both REST and MCP endpoints run on same port
       - Cloud Foundry can use port-based health checks
       - uvicorn.run(app, ...) serves both FastAPI and MCP
    
    FastMCP automatically handles:
    - HTTP/SSE transport for MCP protocol
    - JSON-RPC message parsing and formatting
    - Tool discovery and execution
    - MCP protocol method routing (initialize, tools/list, tools/call)
    """
    # Step 1: Initialize services (embeddings, vector store, quotes)
    logger.info("Step 1: Initializing services...")
    initialize_services()
    
    # Step 2: Verify HTTP/SSE transport configuration
    logger.info("Step 2: Verifying HTTP/SSE transport configuration...")
    transport_config = verify_transport_configuration()
    
    # Step 3: Log available MCP tools
    logger.info("=" * 70)
    logger.info("Step 3: MCP Tools Available:")
    logger.info("=" * 70)
    logger.info("Available MCP Tools:")
    logger.info("  - search_quotes: Search quotes by topic using semantic similarity")
    logger.info("  - get_random_quote: Get a random inspirational quote")
    logger.info("  - get_all_quotes: Get all quotes from the database")
    logger.info("  - compare_words: Compare two words for semantic similarity")
    logger.info("=" * 70)
    
    # Step 4: Create MCP HTTP app and mount to FastAPI
    # FastMCP v2 provides http_app() method that returns an ASGI app
    # This can be mounted to FastAPI to serve both REST and MCP endpoints
    logger.info("Step 4: Creating MCP HTTP app and mounting to FastAPI...")
    logger.info("=" * 70)
    
    # Create the MCP HTTP app (ASGI application)
    # Use path='/' so MCP endpoints are at the root of the mounted app
    # When mounted at /mcp, endpoints will be at /mcp/* (clean URL)
    mcp_app = mcp.http_app(path='/')
    
    # Create FastAPI app with MCP lifespan
    # IMPORTANT: Pass mcp_app.lifespan to ensure MCP session manager initializes
    # Note: No 'global' needed here - we're at module level, not inside a function
    app = FastAPI(
        title="Quotes Demo - Stage 4",
        description="Cloud Foundry demo with Python: Semantic Quotes MCP Server",
        version="1.0.0",
        lifespan=mcp_app.lifespan  # Critical: MCP needs this for session management
    )
    
    # Mount the MCP server to FastAPI
    # MCP endpoints will be available at /mcp/*
    app.mount("/mcp", mcp_app)
    
    # Register REST endpoints (root and health)
    register_rest_endpoints(app)
    
    logger.info("✅ FastMCP HTTP app created and mounted to FastAPI")
    logger.info("=" * 70)
    logger.info("Server ready:")
    logger.info("  - REST endpoints: GET /, GET /health")
    logger.info("  - MCP protocol: /mcp/* (HTTP/SSE endpoints)")
    logger.info("=" * 70)
    
    # Step 5: Start the combined FastAPI server with uvicorn
    # This serves both REST endpoints and MCP protocol endpoints
    logger.info("Starting combined FastAPI + FastMCP server...")
    logger.info(f"Server will listen on port: {transport_config['port']}")
    logger.info("=" * 70)
    
    try:
        import uvicorn
        port = int(transport_config['port'])
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        logger.info("=" * 70)
        logger.info("Server shutdown requested (KeyboardInterrupt)")
        logger.info("=" * 70)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server stopped")
