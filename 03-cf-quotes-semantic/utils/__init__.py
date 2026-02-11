"""
Utils - Service binding utilities for Cloud Foundry.

This package provides utilities for discovering and connecting to
Cloud Foundry services, including GenAI services and PostgreSQL databases.

Usage:
    from utils import CFGenAIService, CFPostgresService
    
    # Initialize GenAI service
    genai = CFGenAIService("tanzu-nomic-embed-text")
    
    # Initialize PostgreSQL service
    db = CFPostgresService("vector-db")
    connection_uri = db.get_connection_uri()
"""

from .cfgenai import CFGenAIService
from .cfpostgres import CFPostgresService

__all__ = ["CFGenAIService", "CFPostgresService"]
