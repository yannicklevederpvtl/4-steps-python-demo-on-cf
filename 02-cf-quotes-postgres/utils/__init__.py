"""
Utils - Service binding utilities for Cloud Foundry.

This package provides utilities for discovering and connecting to
Cloud Foundry services, including PostgreSQL databases.

Usage:
    from utils import CFPostgresService
    
    # Initialize PostgreSQL service
    db = CFPostgresService("vector-db")
    connection_uri = db.get_connection_uri()
"""

from .cfpostgres import CFPostgresService

__all__ = ["CFPostgresService"]
