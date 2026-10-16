import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class EntityRelevanceGate:
    """
    Entity Relevance Gate.
    Verifies that retrieved context chunks ACTUALLY refer to the user's requested entity.
    Filters out generic KPGU establishment/fee/location chunks when an entity is requested.
    """

    @staticmethod
    def validate_entity_chunks(primary_entity: str, entity_type: str, chunks: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validates retrieved chunks against primary entity.
        Returns (has_valid_chunks, filtered_chunks).
        """
        if not primary_entity or entity_type == "none":
            # No specific entity requested -> all chunks pass threshold as normal
            return True, chunks

        if not chunks:
            return False, []

        entity_clean = primary_entity.lower()
        entity_tokens = [w for w in re.findall(r'\b\w+\b', entity_clean) if w not in ["dr", "prof", "professor", "hod", "dean", "who", "is", "the", "what", "is"]]
        
        valid_chunks = []
        for chunk in chunks:
            content = chunk.get("content", "").lower()
            title = chunk.get("title", "").lower()
            full_text = f"{title}\n{content}"

            # 1. Exact Match Check
            if entity_clean in full_text:
                valid_chunks.append(chunk)
                continue

            # 2. Token Overlap Check for Person Entity (e.g. Rocky AND Upadhyay)
            if entity_type == "person" and entity_tokens:
                # Require all surname/firstname tokens to be present
                token_matches = sum(1 for token in entity_tokens if token in full_text)
                if token_matches == len(entity_tokens):
                    valid_chunks.append(chunk)
                    continue

            # 3. Special Code / Exam Match Check (e.g. KSET, 21CS2406)
            if entity_type in ["code", "special_entity"]:
                if primary_entity.lower() in full_text:
                    valid_chunks.append(chunk)
                    continue

        if not valid_chunks:
            logger.info(f"EntityRelevanceGate: REJECTED all {len(chunks)} generic chunks. No chunk refers to requested entity '{primary_entity}'")
            return False, []

        logger.info(f"EntityRelevanceGate: PASSED {len(valid_chunks)}/{len(chunks)} chunks referring specifically to entity '{primary_entity}'")
        return True, valid_chunks
