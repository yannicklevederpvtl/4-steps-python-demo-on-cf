"""
CustomEmbeddings - LangChain-compatible embedding class for tanzu-nomic-embed-text API.

This module provides a CustomEmbeddings class that wraps the tanzu-nomic-embed-text
embedding service API and implements LangChain's Embeddings interface. This allows
LangChain components (like PGVector) to use the Cloud Foundry-bound embedding service.

The embedding service is accessed via the tanzu-nomic-embed-text service bound to
the Cloud Foundry application. The service provides an OpenAI-compatible API endpoint
for generating embeddings.

API Endpoint Format:
-------------------
- Base URL: api_base from CFGenAIService
- Endpoint: api_base + "/openai/v1/embeddings"
- Request: {"model": model_name, "input": text}
- Response: {"data": [{"embedding": [float, ...]}]}
"""
import requests
import logging
from typing import List, Union
from utils import CFGenAIService

# Configure logging
logger = logging.getLogger(__name__)


class CustomEmbeddings:
    """
    LangChain-compatible embedding class that wraps tanzu-nomic-embed-text API.
    
    This class implements the embedding interface expected by LangChain components
    like PGVector. It uses CFGenAIService to discover the embedding service from
    Cloud Foundry service bindings.
    
    Usage:
        # Initialize with service name (default: "tanzu-nomic-embed-text")
        embeddings = CustomEmbeddings("tanzu-nomic-embed-text")
        
        # Embed a single query
        query_embedding = embeddings.embed_query("What is the meaning of life?")
        
        # Embed multiple documents
        doc_embeddings = embeddings.embed_documents(["Text 1", "Text 2", "Text 3"])
    """
    
    def __init__(self, service_name: str = "tanzu-nomic-embed-text"):
        """
        Initialize the embedding service.
        
        Discovers the embedding service from Cloud Foundry service bindings,
        retrieves API credentials, and sets up the embedding endpoint.
        
        Args:
            service_name: Name of the embedding service in VCAP_SERVICES
                        (default: "tanzu-nomic-embed-text")
        
        Raises:
            ValueError: If service is not found or credentials are invalid
            ValueError: If no models are available
        """
        # Discover the embedding service from Cloud Foundry service bindings
        # CFGenAIService uses cfenv to extract credentials from VCAP_SERVICES
        logger.info(f"Initializing embedding service: {service_name}")
        
        try:
            self.genai_service = CFGenAIService(service_name)
        except ValueError as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
        
        # Get API credentials from the service
        self.api_base = self.genai_service.api_base
        self.api_key = self.genai_service.api_key
        
        # Construct the embeddings endpoint URL
        # The API follows OpenAI-compatible format
        self.embeddings_url = f"{self.api_base}/openai/v1/embeddings"
        
        # Get the model name from available models
        # The service advertises available models via the config endpoint
        try:
            models = self.genai_service.list_models(insecure=True)
            if not models:
                raise ValueError("No models available from embedding service")
            
            # Use the first available model (typically the embedding model)
            self.model_name = models[0]["name"]
            logger.info(f"Using embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to get model name: {e}")
            raise ValueError(f"Could not retrieve model name from service: {e}")
        
        # Prepare headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        This is the core embedding method that makes the API call to the
        embedding service and returns the embedding vector.
        
        Args:
            text: Text string to embed
        
        Returns:
            List[float]: Embedding vector as a list of floats
        
        Raises:
            requests.RequestException: If API call fails
            ValueError: If response parsing fails
        """
        # Prepare the API request payload
        # Format: {"model": model_name, "input": text}
        payload = {
            "model": self.model_name,
            "input": text
        }
        
        try:
            # Make API call to embeddings endpoint
            # verify=False is used for self-signed certificates in demo environments
            # In production, proper certificate validation should be used
            logger.debug(f"Generating embedding for text (length: {len(text)})")
            response = requests.post(
                self.embeddings_url,
                headers=self.headers,
                json=payload,
                verify=False  # Self-signed cert handling for demo environment
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            # Format: {"data": [{"embedding": [float, ...]}]}
            data = response.json()
            
            if not data.get("data") or len(data["data"]) == 0:
                raise ValueError("No embedding data in API response")
            
            embedding = data["data"][0]["embedding"]
            logger.debug(f"Generated embedding (dimensions: {len(embedding)})")
            
            return embedding
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Failed to parse embedding response: {e}")
            raise ValueError(f"Invalid response format from embedding API: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        This method embeds a list of text documents and returns a list of
        embedding vectors. Each document is embedded separately (can be
        optimized for batch processing in the future).
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List[List[float]]: List of embedding vectors, one per input text
        
        Raises:
            requests.RequestException: If API call fails
            ValueError: If response parsing fails
        """
        logger.info(f"Embedding {len(texts)} documents")
        
        # Embed each document individually
        # Note: The API may support batch requests, but for simplicity and
        # compatibility, we embed one at a time
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
                logger.debug(f"Embedded document {i+1}/{len(texts)}")
            except Exception as e:
                logger.error(f"Failed to embed document {i+1}: {e}")
                raise
        
        logger.info(f"Successfully embedded {len(embeddings)} documents")
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query string.
        
        This method is used by LangChain for query embeddings. For this
        implementation, it's the same as embed_text() since the API treats
        queries and documents the same way.
        
        Args:
            text: Query text to embed
        
        Returns:
            List[float]: Embedding vector as a list of floats
        
        Raises:
            requests.RequestException: If API call fails
            ValueError: If response parsing fails
        """
        logger.debug(f"Embedding query (length: {len(text)})")
        # For this API, queries and documents are embedded the same way
        return self.embed_text(text)
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<CustomEmbeddings model={self.model_name} url={self.embeddings_url}>"


# Example usage (for testing/debugging)
if __name__ == "__main__":
    # Configure logging for example
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize embeddings
        embeddings = CustomEmbeddings("tanzu-nomic-embed-text")
        print("Embeddings initialized:", embeddings)
        
        # Test single embedding
        test_text = "This is a test sentence."
        embedding = embeddings.embed_query(test_text)
        print(f"Test embedding dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        
        # Test multiple embeddings
        test_docs = ["First document", "Second document", "Third document"]
        doc_embeddings = embeddings.embed_documents(test_docs)
        print(f"Embedded {len(doc_embeddings)} documents")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the tanzu-nomic-embed-text service is bound to the application.")
