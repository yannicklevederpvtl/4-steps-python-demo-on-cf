"""
Database Module - Stage 2: PostgreSQL Integration

This module handles PostgreSQL database operations for storing and retrieving quotes.
It uses CFPostgresService (from utils) to discover and connect to the bound
PostgreSQL service via VCAP_SERVICES.

Cloud Foundry Service Binding:
-----------------------------
When a PostgreSQL service is bound to a Cloud Foundry application, Cloud Foundry
automatically injects service credentials into the VCAP_SERVICES environment variable.

CFPostgresService handles the service discovery and provides a connection URI
that can be used directly with psycopg2.

Key Features:
- Service discovery via VCAP_SERVICES (using CFPostgresService)
- Database connection management with psycopg2
- Table creation and initialization
- CRUD operations for quotes
"""
import os
import logging
import psycopg2
from psycopg2.extensions import connection  # Import connection type for type annotations
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from utils import CFPostgresService

# Configure logging
logger = logging.getLogger(__name__)

# Environment variable for service name with default
DEFAULT_VECTOR_DB_SERVICE_NAME = os.getenv("VECTOR_DB_SERVICE_NAME", "vector-db")


def get_db_connection(service_name: Optional[str] = None) -> connection:
    """
    Get a PostgreSQL database connection using Cloud Foundry service binding.
    
    This function uses CFPostgresService to discover the PostgreSQL service
    from VCAP_SERVICES and establishes a connection using psycopg2.
    
    Args:
        service_name: Name of the PostgreSQL service in VCAP_SERVICES
                     (default: from VECTOR_DB_SERVICE_NAME env var or "vector-db")
    
    Returns:
        connection: Active database connection (psycopg2.extensions.connection)
    
    Raises:
        ValueError: If the service is not found in VCAP_SERVICES
        psycopg2.Error: If database connection fails
    """
    # Use default service name if not provided
    if service_name is None:
        service_name = DEFAULT_VECTOR_DB_SERVICE_NAME
    
    logger.info(f"Discovering PostgreSQL service: {service_name}")
    
    try:
        # Step 1: Use CFPostgresService to discover service from VCAP_SERVICES
        # This handles all the service binding discovery logic
        db_service = CFPostgresService(service_name)
        connection_uri = db_service.get_connection_uri()
        logger.info("Service discovered successfully, connecting to database...")
        
        # Step 2: Connect to PostgreSQL using psycopg2
        # psycopg2 accepts connection URIs directly
        conn = psycopg2.connect(connection_uri)
        logger.info("Database connection established successfully")
        
        return conn
        
    except ValueError as e:
        logger.error(f"Service discovery failed: {e}")
        raise ValueError(
            f"PostgreSQL service '{service_name}' not available. "
            f"Make sure the service is bound to the application."
        ) from e
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


def initialize_quotes_table(service_name: Optional[str] = None) -> None:
    """
    Create the quotes table if it doesn't exist.
    
    Table Schema:
    - id: SERIAL PRIMARY KEY (auto-incrementing integer)
    - text: TEXT (quote text)
    - category: VARCHAR(100) (quote category)
    - created_at: TIMESTAMP (automatically set on insert)
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Raises:
        ValueError: If service is not found
        psycopg2.Error: If table creation fails
    """
    logger.info("Initializing quotes table...")
    
    conn = None
    try:
        conn = get_db_connection(service_name)
        cur = conn.cursor()
        
        # Create quotes table if it doesn't exist
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS quotes (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            category VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cur.execute(create_table_sql)
        conn.commit()
        
        logger.info("Quotes table initialized successfully")
        
        # Verify table was created
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'quotes'
        """)
        table_exists = cur.fetchone()[0] > 0
        
        if table_exists:
            logger.info("Quotes table verified: exists")
        else:
            logger.warning("Quotes table verification: table not found after creation")
        
        cur.close()
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to initialize quotes table: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def clean_quotes_table(service_name: Optional[str] = None) -> None:
    """
    Delete all quotes from the database.
    
    This function removes all records from the quotes table, effectively
    resetting the database. Useful for demo purposes or reinitialization.
    
    Note: This does NOT drop the table, only deletes all rows.
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Raises:
        ValueError: If service is not found
        psycopg2.Error: If deletion fails
    """
    logger.info("Cleaning quotes table (deleting all quotes)...")
    
    conn = None
    try:
        conn = get_db_connection(service_name)
        cur = conn.cursor()
        
        # Delete all quotes
        cur.execute("DELETE FROM quotes")
        deleted_count = cur.rowcount
        conn.commit()
        
        logger.info(f"Deleted {deleted_count} quote(s) from database")
        
        cur.close()
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to clean quotes table: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def insert_quote(text: str, category: str, service_name: Optional[str] = None) -> int:
    """
    Insert a single quote into the database.
    
    Args:
        text: The quote text
        category: The quote category
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Returns:
        int: The ID of the inserted quote
    
    Raises:
        ValueError: If service is not found
        psycopg2.Error: If insertion fails
    """
    conn = None
    try:
        conn = get_db_connection(service_name)
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO quotes (text, category) VALUES (%s, %s) RETURNING id",
            (text, category)
        )
        quote_id = cur.fetchone()[0]
        conn.commit()
        
        logger.debug(f"Inserted quote with ID: {quote_id}")
        
        cur.close()
        return quote_id
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Failed to insert quote: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def get_all_quotes(service_name: Optional[str] = None) -> List[Dict[str, any]]:
    """
    Retrieve all quotes from the database.
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Returns:
        List[Dict]: List of quote dictionaries with keys: id, text, category, created_at
    
    Raises:
        ValueError: If service is not found
        psycopg2.Error: If query fails
    """
    conn = None
    try:
        conn = get_db_connection(service_name)
        # Use RealDictCursor to return results as dictionaries
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, text, category, created_at FROM quotes ORDER BY id")
        quotes = cur.fetchall()
        
        # Convert RealDictRow objects to regular dictionaries
        result = [dict(quote) for quote in quotes]
        
        logger.debug(f"Retrieved {len(result)} quote(s) from database")
        
        cur.close()
        return result
        
    except psycopg2.Error as e:
        logger.error(f"Failed to retrieve quotes: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def get_random_quote(service_name: Optional[str] = None) -> Optional[Dict[str, any]]:
    """
    Retrieve a random quote from the database.
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Returns:
        Dict: A random quote dictionary with keys: id, text, category, created_at
              Returns None if no quotes exist
    
    Raises:
        ValueError: If service is not found
        psycopg2.Error: If query fails
    """
    conn = None
    try:
        conn = get_db_connection(service_name)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, text, category, created_at FROM quotes ORDER BY RANDOM() LIMIT 1")
        quote = cur.fetchone()
        
        if quote:
            result = dict(quote)
            logger.debug(f"Retrieved random quote with ID: {result['id']}")
        else:
            result = None
            logger.debug("No quotes found in database")
        
        cur.close()
        return result
        
    except psycopg2.Error as e:
        logger.error(f"Failed to retrieve random quote: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def get_quotes_count(service_name: Optional[str] = None) -> int:
    """
    Get the total number of quotes in the database.
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Returns:
        int: Number of quotes in the database
    
    Raises:
        ValueError: If service is not found
        psycopg2.Error: If query fails
    """
    conn = None
    try:
        conn = get_db_connection(service_name)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM quotes")
        count = cur.fetchone()[0]
        
        cur.close()
        return count
        
    except psycopg2.Error as e:
        logger.error(f"Failed to get quotes count: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()
