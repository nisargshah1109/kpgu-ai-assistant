import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Entity Extractor for user queries.
    Identifies specific named entities: Persons (Faculty/HOD/Deans), Exam/Test codes (KSET, GUJCET),
    Course/Subject codes (21CS2406), and specific Departments/Programs.
    """

    @staticmethod
    def extract_entity(query: str) -> Tuple[Optional[str], str]:
        """
        Extracts primary named entity and entity type from query.
        Returns (primary_entity_name, entity_type).
        """
        if not query:
            return None, "none"

        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Person / Faculty Name Extraction (e.g., "Dr. Rocky Upadhyay", "Who is Dr. Patel", "Prof. Sharma")
        person_match = re.search(r'\b(dr\.|prof\.|professor|hod|dean|chancellor|registrar)\s+([a-z0-9\s]+)\b', q_lower, re.IGNORECASE)
        if person_match:
            person_name = person_match.group(0).title()
            logger.info(f"EntityExtractor: Found Person Entity -> '{person_name}'")
            return person_name, "person"

        # Check for explicit name query "Who is X Y" (e.g., "Who is Rocky Upadhyay?")
        who_is_match = re.search(r'\bwho is\s+([a-z]+\s+[a-z]+)\b', q_lower, re.IGNORECASE)
        if who_is_match:
            name = who_is_match.group(1).title()
            if name.lower() not in ["the hod", "the dean", "the chancellor", "the principal", "admission process", "kpgu university"]:
                logger.info(f"EntityExtractor: Found Person Entity from 'Who is' -> '{name}'")
                return name, "person"

        # 2. Subject / Course Code Extraction (e.g., 21CS2406, BTECH-101)
        code_match = re.search(r'\b(?:\d{2}[A-Z]{2,4}\d{3,4}|[A-Z]{2,4}-\d{3,4}|\d{5,8})\b', q_clean)
        if code_match:
            code = code_match.group(0).upper()
            logger.info(f"EntityExtractor: Found Course Code Entity -> '{code}'")
            return code, "code"

        # 3. Special Exam / System Entities (e.g., KSET, GUJCET, MYSY, ACPC)
        for special in ["kset", "gujcet", "mysy", "acpc", "bams", "bpt", "bpharm", "mpharm"]:
            if re.search(rf'\b{special}\b', q_lower):
                logger.info(f"EntityExtractor: Found Special Entity -> '{special.upper()}'")
                return special.upper(), "special_entity"

        return None, "none"
