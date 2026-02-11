"""
Quotes Data Model: In-Memory Quotes

This module defines the inspirational quotes dataset (24 quotes from 5 categories)
and provides functions to retrieve quotes from memory.

The quotes are organized into 5 categories:
- Importance of Education (5 quotes)
- Being Kind to Others (4 quotes)
- Contributing to Others (5 quotes)
- Hard Work (5 quotes)
- Overcoming Failure (5 quotes)

This stage stores quotes in-memory (no database required).
"""
import random
from typing import List, Dict, Optional

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
