"""
Quotes Data Model: PostgreSQL Integration

This module defines the inspirational quotes dataset (24 quotes from 5 categories)
and provides functions to retrieve quotes from both memory and PostgreSQL database.

The quotes are organized into 5 categories:
- Importance of Education (5 quotes)
- Being Kind to Others (4 quotes)
- Contributing to Others (5 quotes)
- Hard Work (5 quotes)
- Overcoming Failure (5 quotes)

It extends the in-memory quotes by adding PostgreSQL database integration:
- Quotes can be stored in PostgreSQL database
- Functions available for both in-memory (backward compatibility) and database access
- Database functions use the database.py module for PostgreSQL operations
"""
import logging
import random
from typing import List, Dict, Optional
from database import (
    initialize_quotes_table,
    insert_quote,
    get_random_quote as db_get_random_quote,
    get_all_quotes as db_get_all_quotes,
    get_quotes_count
)

# Configure logging
logger = logging.getLogger(__name__)

# Quote dataset - matches Stage 3 exactly (24 quotes in 5 categories)
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


def get_random_quote() -> Dict[str, str]:
    """
    Get a random quote from the in-memory quotes dataset.
    
    Returns:
        Dict[str, str]: A dictionary with 'text' and 'category' keys containing a random quote
    """
    return random.choice(QUOTES_DATA).copy()


def get_all_quotes() -> List[Dict[str, str]]:
    """
    Get all quotes from the in-memory quotes dataset.
    
    Returns:
        List[Dict[str, str]]: List of all 24 quote dictionaries, each with 'text' and 'category' keys
    """
    return [quote.copy() for quote in QUOTES_DATA]


def get_quotes_by_category(category: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get quotes filtered by category (optional helper function).
    
    Args:
        category: Optional category name to filter by. If None, returns all quotes.
    
    Returns:
        List[Dict[str, str]]: List of quote dictionaries matching the category, or all quotes if category is None
    """
    if category is None:
        return get_all_quotes()
    
    return [quote.copy() for quote in QUOTES_DATA if quote["category"] == category]


# ============================================================================
# DATABASE FUNCTIONS - Stage 2: PostgreSQL Integration
# ============================================================================

def load_quotes_to_db(service_name: Optional[str] = None, force: bool = False) -> int:
    """
    Load all quotes from QUOTES_DATA into PostgreSQL database.
    
    This function inserts all 24 quotes from the in-memory QUOTES_DATA
    into the PostgreSQL database. It first ensures the quotes table exists,
    then inserts each quote.
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
        force: If True, loads quotes even if they already exist. If False, skips if quotes exist.
    
    Returns:
        int: Number of quotes loaded into the database
    
    Raises:
        ValueError: If database service is not found
        Exception: If database operations fail
    """
    logger.info("Loading quotes into PostgreSQL database...")
    
    try:
        # Step 1: Ensure the quotes table exists
        logger.info("Initializing quotes table...")
        initialize_quotes_table(service_name)
        
        # Step 2: Check if quotes already exist (unless force=True)
        if not force:
            existing_count = get_quotes_count(service_name)
            if existing_count > 0:
                logger.info(f"Database already contains {existing_count} quote(s). Skipping load. Use force=True to reload.")
                return existing_count
        
        # Step 3: Insert all quotes from QUOTES_DATA
        loaded_count = 0
        for quote in QUOTES_DATA:
            try:
                insert_quote(quote["text"], quote["category"], service_name)
                loaded_count += 1
            except Exception as e:
                logger.warning(f"Failed to insert quote: {quote['text'][:50]}... Error: {e}")
                # Continue with next quote even if one fails
        
        logger.info(f"Successfully loaded {loaded_count} quote(s) into database")
        return loaded_count
        
    except Exception as e:
        logger.error(f"Failed to load quotes into database: {e}", exc_info=True)
        raise


def get_random_quote_from_db(service_name: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get a random quote from PostgreSQL database.
    
    This function retrieves a random quote from the database and returns it
    in the same format as the in-memory version (text and category only).
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Returns:
        Optional[Dict[str, str]]: A dictionary with 'text' and 'category' keys containing a random quote.
                                 Returns None if no quotes exist in the database.
    
    Raises:
        ValueError: If database service is not found
        Exception: If database query fails
    """
    try:
        # Get quote from database (includes id, text, category, created_at)
        db_quote = db_get_random_quote(service_name)
        
        if db_quote is None:
            logger.debug("No quotes found in database")
            return None
        
        # Return in same format as in-memory version (text and category only)
        return {
            "text": db_quote["text"],
            "category": db_quote["category"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get random quote from database: {e}", exc_info=True)
        raise


def get_all_quotes_from_db(service_name: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get all quotes from PostgreSQL database.
    
    This function retrieves all quotes from the database and returns them
    in the same format as the in-memory version (text and category only).
    
    Args:
        service_name: Name of the PostgreSQL service (default: from env var or "vector-db")
    
    Returns:
        List[Dict[str, str]]: List of quote dictionaries, each with 'text' and 'category' keys.
                             Returns empty list if no quotes exist in the database.
    
    Raises:
        ValueError: If database service is not found
        Exception: If database query fails
    """
    try:
        # Get all quotes from database (includes id, text, category, created_at)
        db_quotes = db_get_all_quotes(service_name)
        
        if not db_quotes:
            logger.debug("No quotes found in database")
            return []
        
        # Return in same format as in-memory version (text and category only)
        result = [
            {
                "text": quote["text"],
                "category": quote["category"]
            }
            for quote in db_quotes
        ]
        
        logger.debug(f"Retrieved {len(result)} quote(s) from database")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get all quotes from database: {e}", exc_info=True)
        raise
