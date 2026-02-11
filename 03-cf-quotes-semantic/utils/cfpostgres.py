"""
CFPostgresService - Utility to load PostgreSQL service credentials from Cloud Foundry environment.

This module provides a utility class to discover and connect to PostgreSQL services
(like vector-db with pgvector) bound to Cloud Foundry applications via VCAP_SERVICES.

Cloud Foundry Service Binding:
-----------------------------
When a PostgreSQL service is bound to a Cloud Foundry application, Cloud Foundry
automatically injects service credentials into the VCAP_SERVICES environment variable.

Example VCAP_SERVICES structure for PostgreSQL:
{
  "user-provided": [
    {
      "name": "vector-db",
      "credentials": {
        "uri": "postgresql://user:password@host:port/database",
        "host": "postgres-host.sys.tas.labs.com",
        "port": 5432,
        "database": "postgres",
        "username": "user",
        "password": "password"
      }
    }
  ]
}

The connection URI provided by Cloud Foundry is already SQLAlchemy-compatible,
so it can be used directly with SQLAlchemy engines and LangChain's PGVector.
"""
from cfenv import AppEnv


class CFPostgresService:
    """
    Utility to load PostgreSQL service credentials from Cloud Foundry environment (VCAP_SERVICES)
    and extract connection URI.
    
    This class discovers PostgreSQL services (like vector-db) that are bound
    to the Cloud Foundry application and provides access to their connection URI.
    
    The connection URI from Cloud Foundry is already SQLAlchemy-compatible,
    so it can be used directly with:
    - SQLAlchemy: create_engine(connection_uri)
    - LangChain PGVector: PGVector(connection=connection_uri, ...)
    
    Usage:
        # Initialize with service name (default: "vector-db")
        db_service = CFPostgresService("vector-db")
        
        # Get SQLAlchemy-compatible connection URI
        connection_uri = db_service.get_connection_uri()
        
        # Use with SQLAlchemy
        from sqlalchemy import create_engine
        engine = create_engine(connection_uri)
        
        # Use with LangChain PGVector
        from langchain_postgres import PGVector
        vectorstore = PGVector(connection=connection_uri, ...)
    """

    def __init__(self, service_name: str = "vector-db"):
        """
        Initialize the service by discovering it from VCAP_SERVICES.
        
        Args:
            service_name: The name of the PostgreSQL service as it appears in VCAP_SERVICES
                         (default: "vector-db")
        
        Raises:
            ValueError: If the service is not found in VCAP_SERVICES
            ValueError: If the connection URI is not found in service credentials
        """
        # Cloud Foundry automatically injects VCAP_SERVICES environment variable
        # when services are bound to the application
        env = AppEnv()
        
        # Discover the service by name from VCAP_SERVICES
        self.service = env.get_service(name=service_name)
        if not self.service:
            raise ValueError(
                f"Service '{service_name}' not found in VCAP_SERVICES. "
                f"Make sure the service is bound to the application."
            )

        # Extract credentials from the service binding
        # Cloud Foundry service credentials contain connection information
        self.credentials = self.service.credentials
        
        # PostgreSQL services provide a 'uri' field that contains the complete
        # connection string in SQLAlchemy-compatible format
        # Format: postgresql://username:password@host:port/database
        self.connection_uri = self.credentials.get("uri")
        
        if not self.connection_uri:
            raise ValueError(
                f"Connection URI not found in service '{service_name}' credentials. "
                f"Expected 'uri' field in credentials."
            )
        
        # Store individual components for reference (optional, not always needed)
        self.host = self.credentials.get("host")
        self.port = self.credentials.get("port")
        self.database = self.credentials.get("database")
        self.username = self.credentials.get("username")
        self.password = self.credentials.get("password")

    def get_connection_uri(self) -> str:
        """
        Get the SQLAlchemy-compatible connection URI.
        
        The URI from Cloud Foundry is already in the correct format:
        postgresql://username:password@host:port/database
        
        This URI can be used directly with:
        - SQLAlchemy's create_engine()
        - LangChain's PGVector connection parameter
        - psycopg2 connection strings
        
        Returns:
            str: SQLAlchemy-compatible PostgreSQL connection URI
        
        Raises:
            ValueError: If connection URI is not available
        """
        if not self.connection_uri:
            raise ValueError("Connection URI is not available")
        return self.connection_uri

    def get_credentials(self) -> dict:
        """
        Get all service credentials as a dictionary.
        
        Returns:
            dict: Complete credentials dictionary from the service binding
        """
        return self.credentials

    def __repr__(self):
        """String representation of the service for debugging."""
        # Don't expose sensitive information like passwords
        uri_safe = self.connection_uri
        if uri_safe and "@" in uri_safe:
            # Mask password in URI for safe display
            parts = uri_safe.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split("://")[1] if "://" in parts[0] else parts[0]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    uri_safe = f"{parts[0].split('://')[0]}://{user}:***@{parts[1]}"
        
        return f"<CFPostgresService service_name={self.service.name} uri={uri_safe}>"


# Example usage (for testing/debugging)
if __name__ == "__main__":
    # Example: Initialize with vector-db service
    service_name = "vector-db"
    try:
        db_service = CFPostgresService(service_name)
        
        print("Service loaded:", db_service)
        
        # Get connection URI
        connection_uri = db_service.get_connection_uri()
        print(f"Connection URI: {connection_uri.split('@')[0]}@***")  # Mask password
        
        # Example: Use with SQLAlchemy
        try:
            from sqlalchemy import create_engine, text
            
            engine = create_engine(connection_uri)
            with engine.connect() as conn:
                version = conn.execute(text("SELECT version();")).fetchone()
                print(f"Connected to: {version[0]}")
        except ImportError:
            print("SQLAlchemy not available for testing")
        except Exception as e:
            print(f"Connection test failed: {e}")
            
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure the service is bound to the application in Cloud Foundry.")
