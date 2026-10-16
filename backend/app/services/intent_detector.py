import re
import logging
from enum import Enum
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    BENEFITS_WHY = "benefits_why"         # "Why KPGU?", "Why choose B.Tech CSE?", "Benefits of studying at KPGU?", "Is KPGU good?"
    PROCEDURAL = "procedural"             # "What is the admission process?", "How to apply?"
    REQUIREMENT = "requirement"           # "What documents are required?", "Eligibility criteria?"
    INFORMATIONAL = "informational"       # "What is KSET?", "Where is KPGU?", "What is the fee?"
    COMPARISON = "comparison font"         # "Why choose KPGU over another university?"

# Patterns for Benefits / Why / Advantages Intent
BENEFIT_PATTERNS = [
    r'\bwhy (should i|choose|join|take admission|study|select|prefer)\b',
    r'\bwhy kpgu\b',
    r'\bwhat are the (benefits|advantages|strengths|highlights|features) of\b',
    r'\bis kpgu (good|best|suitable|worth|recommended)\b',
    r'\bwhy should i (choose|take) (btech|b\.tech|cse|bpharm|mba|d2d)\b',
    r'\bwhat makes kpgu (different|special|unique)\b',
    r'\bwhat opportunities (does|are)\b',
]

# Patterns for Procedural Intent
PROCEDURAL_PATTERNS = [
    r'\b(how to|procedure for|process for|steps to|how can i) (apply|register|enroll|get admission)\b',
    r'\badmission process\b',
    r'\badmission procedure\b'
]

# Patterns for Requirement Intent
REQUIREMENT_PATTERNS = [
    r'\b(what documents|documents required|eligibility criteria|qualification|requirements) for\b',
    r'\beligible for\b'
]

class IntentDetector:
    """
    Intent Detector for user queries.
    Identifies if a question is asking for Benefits/Reasons ("Why KPGU?"), Procedures, Requirements, or Information.
    """

    @staticmethod
    def detect_intent(query: str) -> Tuple[QueryIntent, Dict[str, Any]]:
        if not query:
            return QueryIntent.INFORMATIONAL, {}

        q_clean = query.strip().lower()

        # 1. Check Benefits / Why Intent
        for pattern in BENEFIT_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                # Check if course-specific (e.g., B.Tech CSE, B.Pharm)
                course_specific = None
                for c in ["btech", "b.tech", "cse", "computer science", "bpharm", "b.pharm", "mba", "d2d"]:
                    if c in q_clean:
                        course_specific = c
                        break

                logger.info(f"IntentDetector: Detected BENEFITS_WHY intent for '{query}' (course_specific={course_specific})")
                return QueryIntent.BENEFITS_WHY, {"course_specific": course_specific}

        # 2. Check Procedural Intent
        for pattern in PROCEDURAL_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                logger.info(f"IntentDetector: Detected PROCEDURAL intent for '{query}'")
                return QueryIntent.PROCEDURAL, {}

        # 3. Check Requirement Intent
        for pattern in REQUIREMENT_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                logger.info(f"IntentDetector: Detected REQUIREMENT intent for '{query}'")
                return QueryIntent.REQUIREMENT, {}

        # Default: Informational
        return QueryIntent.INFORMATIONAL, {}
