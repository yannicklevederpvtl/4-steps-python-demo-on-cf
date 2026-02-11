"""
Similarity Search - Vector similarity search operations for quotes and words.

This module provides functions for similarity search using vector embeddings.
It implements quote similarity search (finding quotes similar to a topic) and
word-to-word similarity comparisons, matching the Java Spring AI example.

Cosine Similarity:
-----------------
Similarity search uses cosine similarity to measure how similar two vectors are.
Cosine similarity measures the angle between two vectors in high-dimensional space:
- Range: -1.0 to 1.0 (typically 0.0 to 1.0 for normalized embeddings)
- 1.0 = Identical vectors (perfect similarity)
- 0.0 = Orthogonal vectors (no similarity)
- Higher values indicate more semantic similarity

Note: PGVector's similarity_search_with_score returns cosine DISTANCE (lower = more similar),
which we convert to similarity using: similarity = 1 - distance

The pgvector extension in PostgreSQL uses cosine similarity for efficient
vector similarity search, allowing us to find quotes with similar meanings
even if they use different words.
"""
import logging
from typing import List, Dict, Tuple, Optional, Any
from vector_store import initialize_store
from embeddings import CustomEmbeddings

# Configure logging
logger = logging.getLogger(__name__)


def search_similar_quotes(
    query: str,
    vectorstore=None,
    k: int = 10,
    collection_name: str = "inspirational_quotes"
) -> List[Dict[str, Any]]:
    """
    Search for quotes similar to the given query topic.
    
    This function uses vector similarity search to find quotes whose embeddings
    are most similar to the query embedding. The search uses cosine similarity
    to measure semantic similarity between the query and stored quotes.
    
    Args:
        query: Topic or query text to search for similar quotes
        vectorstore: Optional PGVector store instance. If None, initializes a new one.
        k: Number of similar quotes to return (default: 10)
        collection_name: Name of the collection to search (default: "inspirational_quotes")
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries, each containing:
            - text: The quote text
            - similarity: Similarity score (0.0 to 1.0, higher = more similar)
            - category: Quote category from metadata
    
    Raises:
        ValueError: If query is empty or collection is empty
        Exception: If search operation fails
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    logger.info(f"Searching for quotes similar to: '{query}'")
    
    try:
        # Initialize vector store if not provided
        if vectorstore is None:
            logger.info("Initializing vector store...")
            vectorstore = initialize_store(collection_name=collection_name)
        
        # Perform similarity search with scores
        # similarity_search_with_score returns list of tuples: (Document, score)
        # IMPORTANT: PGVector returns cosine DISTANCE (lower = more similar), not similarity
        # We need to convert distance to similarity: similarity = 1 - distance
        logger.debug(f"Performing similarity search (k={k})...")
        results = vectorstore.similarity_search_with_score(query, k=k)
        
        if not results:
            logger.warning("No results found. Collection may be empty.")
            return []
        
        # Convert results to list of dictionaries
        # Results are sorted by distance (ascending) from pgvector, so most similar first
        similar_quotes = []
        for doc, distance in results:
            # Convert cosine distance to cosine similarity
            # Distance: 0.0 = identical, 1.0 = orthogonal, 2.0 = opposite
            # Similarity: 1.0 = identical, 0.0 = orthogonal, -1.0 = opposite
            similarity = 1.0 - float(distance)
            
            # Extract quote text and metadata
            quote_dict = {
                "text": doc.page_content,
                "similarity": similarity,  # Now correctly showing similarity (higher = more similar)
                "category": doc.metadata.get("category", "Unknown")
            }
            similar_quotes.append(quote_dict)
        
        logger.info(f"Found {len(similar_quotes)} similar quotes")
        logger.debug(f"Similarity scores range: {similar_quotes[0]['similarity']:.4f} to {similar_quotes[-1]['similarity']:.4f}")
        
        return similar_quotes
        
    except Exception as e:
        logger.error(f"Failed to search similar quotes: {e}", exc_info=True)
        raise Exception(f"Could not perform similarity search: {e}") from e


def search_word_similarity(
    word_pairs: Optional[List[Tuple[str, str]]] = None
) -> List[Dict[str, Any]]:
    """
    Compare word pairs for similarity using embeddings.
    
    This function demonstrates word-to-word similarity by generating embeddings
    for word pairs and calculating cosine similarity between them. It matches
    the Java Spring AI example with predefined word pairs.
    
    The word pairs demonstrate how embeddings capture semantic relationships:
    - Related words (man/woman, king/queen) have high similarity
    - Unrelated words (banana/car) have low similarity
    - Same word (man/man) has perfect similarity (1.0)
    - Opposite words (happy/sad) have lower similarity than synonyms (happy/joyful)
    - Cross-language similarity (queen/reine, queen/ملكة) shows multilingual understanding
    
    Args:
        word_pairs: Optional list of (word1, word2) tuples. If None, uses default pairs.
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries, each containing:
            - word1: First word
            - word2: Second word
            - similarity: Similarity score (0.0 to 1.0, higher = more similar)
        Results are sorted by similarity (descending)
    
    Raises:
        Exception: If embedding generation fails
    """
    # Default word pairs matching the Java Spring AI example
    if word_pairs is None:
        word_pairs = [
            ("man", "man"),
            ("man", "woman"),
            ("man", "dirt"),
            ("king", "queen"),
            ("queen", "reine"),  # queen in French
            ("queen", "ملكة"),  # queen in Arabic
            ("banana", "car"),
            ("happy", "joyful"),
            ("happy", "sad"),
        ]
    
    logger.info(f"Computing word similarity for {len(word_pairs)} word pairs...")
    
    try:
        # Initialize embeddings (use environment variable or default)
        import os
        embedding_service_name = os.getenv("EMBEDDING_SERVICE_NAME", "tanzu-nomic-embed-text")
        embeddings = CustomEmbeddings(embedding_service_name)
        
        # Calculate similarity for each word pair
        similarities = []
        for word1, word2 in word_pairs:
            try:
                # Generate embeddings for both words
                embedding1 = embeddings.embed_query(word1)
                embedding2 = embeddings.embed_query(word2)
                
                # Calculate cosine similarity
                # Cosine similarity = dot product / (norm1 * norm2)
                # For normalized embeddings, this simplifies to dot product
                similarity = _cosine_similarity(embedding1, embedding2)
                
                similarities.append({
                    "word1": word1,
                    "word2": word2,
                    "similarity": float(similarity)
                })
                
                logger.debug(f"  {word1} vs {word2}: {similarity:.4f}")
                
            except Exception as e:
                logger.error(f"Failed to compute similarity for ({word1}, {word2}): {e}")
                # Continue with other pairs even if one fails
                similarities.append({
                    "word1": word1,
                    "word2": word2,
                    "similarity": 0.0,
                    "error": str(e)
                })
        
        # Sort by similarity (descending) - most similar first
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        logger.info(f"Computed similarity for {len(similarities)} word pairs")
        
        return similarities
        
    except Exception as e:
        logger.error(f"Failed to compute word similarity: {e}", exc_info=True)
        raise Exception(f"Could not compute word similarity: {e}") from e


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Cosine similarity measures the cosine of the angle between two vectors.
    For normalized embeddings, this is equivalent to the dot product.
    
    Formula: cosine_similarity = (vec1 · vec2) / (||vec1|| * ||vec2||)
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
    
    Returns:
        float: Cosine similarity score (-1.0 to 1.0, typically 0.0 to 1.0)
    
    Raises:
        ValueError: If vectors have different dimensions
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors must have same dimension: {len(vec1)} vs {len(vec2)}")
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate magnitudes (norms)
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Cosine similarity
    similarity = dot_product / (norm1 * norm2)
    
    return similarity


# Example usage (for testing/debugging)
if __name__ == "__main__":
    # Configure logging for example
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Test word similarity
        print("Testing word similarity...")
        word_results = search_word_similarity()
        print(f"\nWord Similarity Results (sorted by similarity):")
        for result in word_results:
            print(f"  {result['word1']} vs {result['word2']}: {result['similarity']:.4f}")
        
        # Test quote similarity
        print("\n\nTesting quote similarity...")
        quote_results = search_similar_quotes("getting over losing a job", k=5)
        print(f"\nTop {len(quote_results)} Similar Quotes:")
        for i, quote in enumerate(quote_results, 1):
            print(f"  {i}. [{quote['similarity']:.4f}] {quote['text'][:60]}...")
            print(f"     Category: {quote['category']}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure both vector-db and tanzu-nomic-embed-text services are bound to the application.")
