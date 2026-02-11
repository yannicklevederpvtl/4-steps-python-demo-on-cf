"""
Vector Store - PGVector initialization and management for LangChain.

This module provides functions to initialize and manage a PGVector store using
LangChain's PostgreSQL integration with the pgvector extension. The vector store
is used to store and search inspirational quotes using vector similarity.

PGVector Overview:
-----------------
PGVector is a PostgreSQL extension that adds vector similarity search capabilities.
LangChain's PGVector integration uses this extension to store document embeddings
and perform similarity searches.

Collection-based Storage:
------------------------
LangChain organizes documents into collections. Each collection has:
- Collection metadata in `langchain_pg_collection` table
- Document embeddings in `langchain_pg_embedding` table

The pgvector extension enables efficient similarity search using cosine similarity
or other distance metrics.
"""
import os
import logging
from langchain_postgres import PGVector
from utils import CFPostgresService
from embeddings import CustomEmbeddings

# Configure logging
logger = logging.getLogger(__name__)

# Service name defaults (can be overridden via environment variables)
DEFAULT_EMBEDDING_SERVICE_NAME = os.getenv("EMBEDDING_SERVICE_NAME", "tanzu-nomic-embed-text")
DEFAULT_VECTOR_DB_SERVICE_NAME = os.getenv("VECTOR_DB_SERVICE_NAME", "vector-db")


def initialize_store(
    collection_name: str = "inspirational_quotes",
    db_service_name: str = None,
    embedding_service_name: str = None
) -> PGVector:
    """
    Initialize and return a PGVector store instance.
    
    This function creates a PGVector store that connects to the PostgreSQL database
    (with pgvector extension) and uses the custom embedding service for generating
    embeddings. The store is configured for collection-based storage of documents.
    
    Args:
        collection_name: Name of the collection to use (default: "inspirational_quotes")
        db_service_name: Name of the PostgreSQL service in VCAP_SERVICES
                        (default: from VECTOR_DB_SERVICE_NAME env var or "vector-db")
        embedding_service_name: Name of the embedding service in VCAP_SERVICES
                               (default: from EMBEDDING_SERVICE_NAME env var or "tanzu-nomic-embed-text")
    
    Returns:
        PGVector: Initialized PGVector store instance ready for use
    
    Raises:
        ValueError: If database service is not found
        ValueError: If embedding service is not found
        Exception: If database connection fails or pgvector extension cannot be created
    """
    # Use defaults from environment variables if not provided
    if db_service_name is None:
        db_service_name = DEFAULT_VECTOR_DB_SERVICE_NAME
    if embedding_service_name is None:
        embedding_service_name = DEFAULT_EMBEDDING_SERVICE_NAME
    
    logger.info("Initializing PGVector store...")
    
    try:
        # Step 1: Get database connection URI from Cloud Foundry service binding
        # CFPostgresService discovers the database service from VCAP_SERVICES
        # and extracts the SQLAlchemy-compatible connection URI
        logger.info(f"Connecting to database service: {db_service_name}")
        db_service = CFPostgresService(db_service_name)
        connection_uri = db_service.get_connection_uri()
        logger.info("Database connection URI retrieved successfully")
        
    except ValueError as e:
        logger.error(f"Failed to get database connection: {e}")
        raise ValueError(
            f"Database service '{db_service_name}' not available. "
            f"Make sure the service is bound to the application."
        ) from e
    
    try:
        # Step 2: Initialize the custom embedding service
        # CustomEmbeddings wraps the tanzu-nomic-embed-text API and provides
        # LangChain-compatible embedding interface
        logger.info(f"Initializing embedding service: {embedding_service_name}")
        embeddings = CustomEmbeddings(embedding_service_name)
        logger.info("Embedding service initialized successfully")
        
    except ValueError as e:
        logger.error(f"Failed to initialize embedding service: {e}")
        raise ValueError(
            f"Embedding service '{embedding_service_name}' not available. "
            f"Make sure the service is bound to the application."
        ) from e
    
    try:
        # Step 3: Initialize PGVector store
        # PGVector uses the connection URI and embeddings to create a vector store
        # that can store documents with their embeddings and perform similarity search
        logger.info(f"Creating PGVector store with collection: {collection_name}")
        
        vectorstore = PGVector(
            embeddings=embeddings,              # Custom embedding model
            connection=connection_uri,            # PostgreSQL connection string
            collection_name=collection_name,      # Collection name for organizing documents
            use_jsonb=True,                      # Use JSONB for metadata storage (efficient)
            create_extension=True,                # Automatically create pgvector extension if not exists
            pre_delete_collection=False,         # Don't auto-delete collection on startup
        )
        
        logger.info("PGVector store initialized successfully")
        logger.info(f"Collection '{collection_name}' is ready for use")
        
        return vectorstore
        
    except Exception as e:
        logger.error(f"Failed to initialize PGVector store: {e}")
        raise Exception(
            f"Could not initialize vector store. "
            f"Check database connection and pgvector extension availability."
        ) from e


def clean_store(
    collection_name: str = "inspirational_quotes",
    db_service_name: str = None,
    embedding_service_name: str = None
) -> None:
    """
    Clean/reset the vector store by deleting the collection.
    
    This function removes all documents and embeddings from the specified collection.
    Useful for resetting the database or reinitializing with fresh data.
    
    Args:
        collection_name: Name of the collection to clean (default: "inspirational_quotes")
        db_service_name: Name of the PostgreSQL service in VCAP_SERVICES
                        (default: from VECTOR_DB_SERVICE_NAME env var or "vector-db")
        embedding_service_name: Name of the embedding service in VCAP_SERVICES (unused, kept for compatibility)
                               (default: from EMBEDDING_SERVICE_NAME env var or "tanzu-nomic-embed-text")
    
    Raises:
        Exception: If cleanup fails
    """
    # Use defaults from environment variables if not provided
    if db_service_name is None:
        db_service_name = DEFAULT_VECTOR_DB_SERVICE_NAME
    
    logger.info(f"Cleaning vector store collection: {collection_name}")
    
    try:
        import psycopg2
        from utils import CFPostgresService
        
        # Get database connection URI
        db_service = CFPostgresService(db_service_name)
        connection_uri = db_service.get_connection_uri()
        
        # Connect using psycopg2 (accepts connection URI directly)
        logger.info("Connecting to database...")
        conn = psycopg2.connect(connection_uri)
        conn.autocommit = True  # Enable autocommit for DDL operations
        cur = conn.cursor()
        
        # Delete the collection (CASCADE will automatically delete all embeddings)
        logger.info(f"Deleting collection '{collection_name}'...")
        cur.execute("""
            DELETE FROM langchain_pg_collection 
            WHERE name = %s
        """, (collection_name,))
        
        deleted_count = cur.rowcount
        logger.info(f"Deleted {deleted_count} collection(s) from database")
        
        cur.close()
        conn.close()
        
        logger.info(f"Collection '{collection_name}' cleaned successfully")
        
    except Exception as e:
        logger.error(f"Failed to clean vector store: {e}")
        raise Exception(f"Could not clean collection '{collection_name}': {e}") from e


# Example usage (for testing/debugging)
if __name__ == "__main__":
    # Configure logging for example
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize the vector store
        vectorstore = initialize_store()
        print("Vector store initialized:", vectorstore)
        print(f"Collection name: inspirational_quotes")
        
        # Test: Check if collection exists (this would require querying the database)
        # For now, just verify the store was created
        print("✅ Vector store is ready for use")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure both vector-db and tanzu-nomic-embed-text services are bound to the application.")
