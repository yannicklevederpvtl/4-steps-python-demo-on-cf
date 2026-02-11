"""
Quotes Data Model - Inspirational quotes dataset and loading logic.

This module defines the inspirational quotes dataset (24 quotes from the Java Spring AI example)
and provides functions to load them into the vector store as LangChain Document objects.

The quotes are organized into 5 categories:
- Importance of Education (5 quotes)
- Being Kind to Others (4 quotes)
- Contributing to Others (5 quotes)
- Hard Work (5 quotes)
- Overcoming Failure (5 quotes)

Each quote is stored as a LangChain Document with metadata (category) for filtering
and organization. The quotes are loaded into the PGVector store with their embeddings
for similarity search.
"""
import logging
from typing import List, Dict
from langchain_core.documents import Document
from vector_store import initialize_store

# Configure logging
logger = logging.getLogger(__name__)


# Quote dataset - matches the Java Spring AI example exactly
QUOTES_DATA: List[Dict[str, str]] = [
    # Importance of Education (5 quotes)
    {
        "text": "Education is the most powerful weapon which you can use to change the world. – Nelson Mandela",
        "category": "Importance of Education"
    },
    {
        "text": "The only person who is educated is the one who has learned how to learn and change. – Carl Rogers",
        "category": "Importance of Education"
    },
    {
        "text": "An investment in knowledge pays the best interest. – Benjamin Franklin",
        "category": "Importance of Education"
    },
    {
        "text": "Education is not the filling of a pail, but the lighting of a fire. – William Butler Yeats",
        "category": "Importance of Education"
    },
    {
        "text": "The roots of education are bitter, but the fruit is sweet. – Aristotle",
        "category": "Importance of Education"
    },
    
    # Being Kind to Others (4 quotes)
    {
        "text": "No act of kindness, no matter how small, is ever wasted. – Aesop",
        "category": "Being Kind to Others"
    },
    {
        "text": "Kindness is a language which the deaf can hear and the blind can see. – Mark Twain",
        "category": "Being Kind to Others"
    },
    {
        "text": "Carry out a random act of kindness, with no expectation of reward, safe in the knowledge that one day someone might do the same for you. – Princess Diana",
        "category": "Being Kind to Others"
    },
    {
        "text": "A single act of kindness throws out roots in all directions, and the roots spring up and make new trees. – Amelia Earhart",
        "category": "Being Kind to Others"
    },
    
    # Contributing to Others (5 quotes)
    {
        "text": "The best way to find yourself is to lose yourself in the service of others. – Mahatma Gandhi",
        "category": "Contributing to Others"
    },
    {
        "text": "We make a living by what we get. We make a life by what we give. – Winston Churchill",
        "category": "Contributing to Others"
    },
    {
        "text": "No one has ever become poor by giving. – Anne Frank",
        "category": "Contributing to Others"
    },
    {
        "text": "The meaning of life is to find your gift. The purpose of life is to give it away. – Pablo Picasso",
        "category": "Contributing to Others"
    },
    {
        "text": "Only a life lived for others is a life worthwhile. – Albert Einstein",
        "category": "Contributing to Others"
    },
    
    # Hard Work (5 quotes)
    {
        "text": "There is no substitute for hard work. – Thomas Edison",
        "category": "Hard Work"
    },
    {
        "text": "The only place where success comes before work is in the dictionary. – Vidal Sassoon",
        "category": "Hard Work"
    },
    {
        "text": "I'm a greater believer in luck, and I find the harder I work the more I have of it. – Thomas Jefferson",
        "category": "Hard Work"
    },
    {
        "text": "Success is not the result of spontaneous combustion. You must set yourself on fire. – Arnold H. Glasow",
        "category": "Hard Work"
    },
    {
        "text": "Hard work beats talent when talent doesn't work hard. – Tim Notke",
        "category": "Hard Work"
    },
    
    # Overcoming Failure (5 quotes)
    {
        "text": "Failure is simply the opportunity to begin again, this time more intelligently. – Henry Ford",
        "category": "Overcoming Failure"
    },
    {
        "text": "Success is not final, failure is not fatal: It is the courage to continue that counts. – Winston Churchill",
        "category": "Overcoming Failure"
    },
    {
        "text": "Our greatest glory is not in never falling, but in rising every time we fall. – Confucius",
        "category": "Overcoming Failure"
    },
    {
        "text": "The only real mistake is the one from which we learn nothing. – Henry Ford",
        "category": "Overcoming Failure"
    },
    {
        "text": "I have not failed. I've just found 10,000 ways that won't work. – Thomas Edison",
        "category": "Overcoming Failure"
    },
]


def get_quotes_data() -> List[Dict[str, str]]:
    """
    Get the complete quotes dataset.
    
    Returns:
        List[Dict[str, str]]: List of quote dictionaries, each with 'text' and 'category'
    """
    return QUOTES_DATA.copy()


def quotes_to_documents(quotes: List[Dict[str, str]]) -> List[Document]:
    """
    Convert quote dictionaries to LangChain Document objects.
    
    Each quote is converted to a Document with:
    - page_content: The quote text
    - metadata: Dictionary containing the category
    
    Args:
        quotes: List of quote dictionaries with 'text' and 'category' keys
    
    Returns:
        List[Document]: List of LangChain Document objects ready for vector store
    """
    documents = []
    for quote in quotes:
        doc = Document(
            page_content=quote["text"],
            metadata={"category": quote["category"]}
        )
        documents.append(doc)
    
    return documents


def is_collection_empty(vectorstore) -> bool:
    """
    Check if the vector store collection is empty.
    
    Uses similarity search with an empty query to check if any documents exist.
    If the collection is empty, the search will return no results.
    
    Args:
        vectorstore: PGVector store instance
    
    Returns:
        bool: True if collection is empty, False otherwise
    """
    try:
        # Try to retrieve a small number of documents
        # If collection is empty, this will return an empty list
        results = vectorstore.similarity_search("", k=1)
        return len(results) == 0
    except Exception as e:
        # If there's an error (e.g., collection doesn't exist), consider it empty
        logger.warning(f"Error checking collection status: {e}. Assuming empty.")
        return True


def initialize_quotes(
    vectorstore=None,
    collection_name: str = "inspirational_quotes",
    force_reload: bool = False
) -> dict:
    """
    Initialize quotes in the vector store if collection is empty.
    
    This function checks if the collection already has quotes loaded. If the collection
    is empty (or force_reload=True), it loads all 24 quotes as Document objects with
    their embeddings into the vector store.
    
    The loading process:
    1. Checks if collection is empty
    2. Converts quotes to Document objects with metadata
    3. Adds documents to vector store (embeddings generated automatically)
    4. Logs the operation
    
    Args:
        vectorstore: Optional PGVector store instance. If None, initializes a new one.
        collection_name: Name of the collection to use (default: "inspirational_quotes")
        force_reload: If True, reload quotes even if collection has data (default: False)
    
    Returns:
        dict: Status dictionary with 'status', 'message', and 'count' keys
    
    Raises:
        Exception: If vector store initialization or document loading fails
    """
    logger.info("Initializing quotes in vector store...")
    
    try:
        # Initialize vector store if not provided
        if vectorstore is None:
            logger.info("Initializing vector store...")
            vectorstore = initialize_store(collection_name=collection_name)
        
        # Check if collection is empty
        is_empty = is_collection_empty(vectorstore)
        
        if not is_empty and not force_reload:
            logger.info("Collection already contains quotes. Skipping initialization.")
            return {
                "status": "skipped",
                "message": "Quotes already loaded",
                "count": 0
            }
        
        if force_reload:
            logger.info("Force reload requested. Reloading quotes...")
        
        # Get quotes data
        quotes = get_quotes_data()
        logger.info(f"Loading {len(quotes)} quotes into vector store...")
        
        # Convert quotes to Document objects with metadata
        documents = quotes_to_documents(quotes)
        logger.info(f"Converted {len(documents)} quotes to Document objects")
        
        # Add documents to vector store
        # This will automatically generate embeddings for each quote
        # and store them in the PostgreSQL database with pgvector
        logger.info("Adding documents to vector store (generating embeddings)...")
        vectorstore.add_documents(documents)
        
        logger.info(f"Successfully loaded {len(documents)} quotes into vector store")
        
        # Log category distribution
        categories = {}
        for quote in quotes:
            category = quote["category"]
            categories[category] = categories.get(category, 0) + 1
        
        logger.info("Quote categories loaded:")
        for category, count in categories.items():
            logger.info(f"  - {category}: {count} quotes")
        
        return {
            "status": "success",
            "message": f"{len(documents)} quotes loaded",
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize quotes: {e}", exc_info=True)
        raise Exception(f"Could not initialize quotes: {e}") from e


# Example usage (for testing/debugging)
if __name__ == "__main__":
    # Configure logging for example
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Get quotes data
        quotes = get_quotes_data()
        print(f"Total quotes: {len(quotes)}")
        
        # Show categories
        categories = {}
        for quote in quotes:
            category = quote["category"]
            categories[category] = categories.get(category, 0) + 1
        
        print("\nQuotes by category:")
        for category, count in categories.items():
            print(f"  - {category}: {count} quotes")
        
        # Test document conversion
        documents = quotes_to_documents(quotes)
        print(f"\nConverted to {len(documents)} Document objects")
        print(f"Sample document: {documents[0].page_content[:50]}...")
        print(f"Sample metadata: {documents[0].metadata}")
        
        # Initialize quotes in vector store
        print("\nInitializing quotes in vector store...")
        result = initialize_quotes()
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure both vector-db and tanzu-nomic-embed-text services are bound to the application.")
