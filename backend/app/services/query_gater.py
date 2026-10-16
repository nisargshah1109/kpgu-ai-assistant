import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Out-of-scope patterns: General world trivia, programming generation, casual jokes/bot identity
EXPLICIT_OUT_OF_SCOPE_PATTERNS = [
    # Programming & coding script generation requests
    r'\b(write|create|generate|fix|debug)\b.*\b(python|javascript|java|c\+\+|html|css|sql|script|function|program)\b',
    # General world trivia / non-university facts
    r'\bwho is (the )?(prime minister|president|king|queen|ceo of (google|apple|microsoft|facebook))\b',
    r'\bwhat is the (capital|population|currency|distance to|speed of light|weather)\b',
    # Creative / casual chat
    r'\b(tell me a|write a)\s+(joke|poem|story|song)\b',
    # Prompt injection & System instruction extraction attempts
    r'\b(ignore|override|bypass)\b.*\b(previous|system|prompt|instructions|rules)\b',
    r'\b(show|reveal|print|tell)\b.*\b(system\s+prompt|api\s+key|secret|hidden\s+instructions)\b',
]

class QueryGater:
    """
    Dataset-Driven Query Scope Evaluator.
    Does NOT use a restrictive whitelist of allowed question categories.
    Only blocks explicit non-university requests (general trivia, programming, jokes, weather).
    Any query that could be present in the university dataset passes to Hybrid Retrieval.
    """
    
    @staticmethod
    def is_kpgu_related(query: str) -> Tuple[bool, str]:
        if not query or not query.strip():
            return False, "Empty query"
            
        q_clean = query.strip().lower()
        
        # 1. Check for explicit out-of-scope patterns (weather, trivia, python code, jokes)
        for pattern in EXPLICIT_OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                logger.info(f"Query Gater: Blocked explicit out-of-scope query: '{query}'")
                return False, "Explicit out-of-scope category"

        # 2. All other queries pass to Hybrid Retrieval!
        # The dataset itself determines whether the information exists.
        return True, "Passed to Hybrid Retrieval"
