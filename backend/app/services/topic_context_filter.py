import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Topic Definitions & Forbidden Cross-Topic Pollution Keywords
TOPIC_RULES = {
    "hostel": {
        "allowed_keywords": ["hostel", "accommodation", "room", "mess", "dining", "laundry", "security", "wifi", "wi-fi", "stay", "residence", "hostel fee"],
        "forbidden_phrases": [
            r'\b(b\.?tech|b\.?pharm|mba|bba|m\.?tech)\b.*\b(tuition\s+)?fee[s]?\b',
            r'\btuition fee structure\b',
            r'\bkpgu was established under\b'
        ]
    },
    "tuition_fees": {
        "allowed_keywords": ["fee", "fees", "tuition", "cost", "frc", "payment", "installment"],
        "forbidden_phrases": [
            r'\blaundry facilities\b',
            r'\bboys and girls hostel mess\b'
        ]
    },
    "admission": {
        "allowed_keywords": ["admission", "apply", "eligibility", "process", "procedure", "acpc", "requirement", "document", "step", "steps"],
        "forbidden_phrases": [
            r'\b(hostel|mess|laundry|dining)\b',
            r'\b(b\.?tech|b\.?pharm|mba|bba)\s+(tuition\s+)?fee[s]?\b'
        ]
    }
}

class TopicContextFilter:
    """
    Topic Context Filter.
    Removes unrelated chunks or lines (e.g., tuition fees when asking about hostels)
    and sanitizes internal document metadata labels before passing to Gemini.
    """

    @staticmethod
    def identify_target_topic(query: str) -> str:
        from app.services.text_processor import TextProcessor
        q_norm = TextProcessor.normalize_user_query(query).lower()
        if any(w in q_norm for w in ["hostel", "accommodation", "stay", "mess", "room"]):
            return "hostel"
        elif any(w in q_norm for w in ["fee", "tuition", "cost"]) and not any(w in q_norm for w in ["hostel fee", "mess fee"]):
            return "tuition_fees"
        elif any(w in q_norm for w in ["admission", "apply", "eligibility", "process", "procedure", "step", "steps", "document", "documents", "required"]):
            return "admission"
        return "general"

    @staticmethod
    def filter_chunks(query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        target_topic = TopicContextFilter.identify_target_topic(query)
        logger.info(f"TopicContextFilter: Target topic identified as '{target_topic}' for query '{query}'")

        if target_topic == "general":
            # Sanitize titles & return
            return [TopicContextFilter._sanitize_chunk(c) for c in chunks]

        rule = TOPIC_RULES.get(target_topic, {})
        forbidden_patterns = rule.get("forbidden_phrases", [])

        filtered_chunks = []
        for chunk in chunks:
            content = chunk.get("content", "")
            title = chunk.get("title", "")
            
            # Clean internal document metadata title (e.g. "Pdf for hostel Fees" -> "Hostel Information")
            sanitized_chunk = TopicContextFilter._sanitize_chunk(chunk)
            
            # Check if chunk contains forbidden cross-topic pollution
            cleaned_content_lines = []
            for line in content.split("\n"):
                line_clean = line.strip()
                if not line_clean:
                    continue

                # Strip out forbidden pollution lines (e.g. B.Tech fee lines in a Hostel query)
                is_forbidden = any(re.search(pat, line_clean, re.IGNORECASE) for pat in forbidden_patterns)
                if not is_forbidden:
                    cleaned_content_lines.append(line_clean)

            cleaned_content = "\n".join(cleaned_content_lines).strip()
            if cleaned_content:
                sanitized_chunk["content"] = cleaned_content
                filtered_chunks.append(sanitized_chunk)

        logger.info(f"TopicContextFilter: Filtered {len(chunks)} -> {len(filtered_chunks)} topic-specific chunks for '{target_topic}'")
        return filtered_chunks

    @staticmethod
    def _sanitize_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
        c = chunk.copy()
        raw_title = c.get("title", "")
        # Remove internal file references like "Pdf for hostel Fees", "document_001.json"
        clean_title = re.sub(r'^(pdf for|doc for|file|document_\d+)\s*', '', raw_title, flags=re.IGNORECASE).strip()
        if not clean_title or clean_title.lower().startswith("document_"):
            clean_title = "KPGU Information"
        c["title"] = clean_title.title()
        return c
