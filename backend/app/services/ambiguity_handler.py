import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class AmbiguityHandler:
    """
    Universal Ambiguity & Clarification Engine.
    Detects when multiple distinct records/interpretations exist for a query and asks targeted clarification.
    Preserves context when user responds to a clarification prompt.
    """

    @staticmethod
    def detect_ambiguity(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], List[str]]:
        """
        Inspects retrieved knowledge chunks for multiple distinct entity records.
        Returns (is_ambiguous, clarification_question, option_list).
        """
        if not retrieved_chunks or len(retrieved_chunks) < 2:
            return False, None, []

        q_lower = query.lower().strip()

        # 1. Person / Faculty Ambiguity Check (e.g. "Dr. Patel", "Professor Sharma")
        person_match = re.search(r'\b(who is|dr\.|prof\.|professor|hod)\s+([a-z]+)\b', q_lower)
        if person_match:
            # Check if retrieved chunks refer to multiple distinct departments / faculties
            departments = set()
            for chunk in retrieved_chunks:
                content = chunk.get("content", "")
                title = chunk.get("title", "")
                # Extract department mentions
                for dept in ["engineering", "pharmacy", "medicine", "management", "nursing", "physiotherapy", "chemistry"]:
                    if dept in content.lower() or dept in title.lower():
                        departments.add(dept.capitalize())

            if len(departments) > 1:
                options = list(departments)[:4]
                question = f"I found multiple records for {person_match.group(0).title()}. Which department are you asking about?"
                return True, question, options

        # 2. Course / Program Ambiguity Check (e.g. "BCA", "B.Sc", "Diploma", "M.Sc")
        if any(term in q_lower for term in ["bca", "bsc", "msc", "diploma", "b.sc", "m.sc"]) and not any(spec in q_lower for spec in ["chemistry", "nursing", "computer", "biotech", "physics"]):
            specs = set()
            for chunk in retrieved_chunks:
                title = chunk.get("title", "")
                content = chunk.get("content", "")
                for spec in ["Chemistry", "Biotechnology", "Physics", "Computer Science", "Nursing"]:
                    if spec.lower() in content.lower() or spec.lower() in title.lower():
                        specs.add(spec)
            if len(specs) > 1:
                options = list(specs)[:4]
                question = f"Which program or specialization are you asking about?"
                return True, question, options

        # 3. Admission Notice / Application Form Ambiguity
        if ("admission notice" in q_lower or "application form" in q_lower) and not any(p in q_lower for p in ["b.tech", "btech", "b.pharm", "mba", "diploma", "d2d"]):
            programs = set()
            for chunk in retrieved_chunks:
                content = chunk.get("content", "")
                for prog in ["B.Tech Engineering", "B.Pharm", "Diploma (D2D)", "MBA / BBA", "B.Sc Nursing"]:
                    if any(w.lower() in content.lower() for w in prog.split()):
                        programs.add(prog)
            if len(programs) > 1:
                options = list(programs)[:4]
                question = "Which program's admission notice or application form do you need?"
                return True, question, options

        # 4. Exam / Timetable Ambiguity
        if ("exam" in q_lower or "examination" in q_lower or "timetable" in q_lower) and not any(s in q_lower for s in ["sem", "semester", "7th", "3rd", "1st", "5th"]):
            semesters = set()
            for chunk in retrieved_chunks:
                content = chunk.get("content", "")
                for sem in ["1st Semester", "3rd Semester (D2D)", "5th Semester", "7th Semester"]:
                    if sem.lower() in content.lower():
                        semesters.add(sem)
            if len(semesters) > 1:
                options = list(semesters)[:4]
                question = "Which exam or semester timetable are you asking about?"
                return True, question, options

        # 5. Generic Admission Process Ambiguity (if program is not specified at all)
        if q_lower in ["what is the admission process?", "admission procedure", "how to apply?", "admissions"] or q_lower == "admission process":
            programs = ["B.Tech Engineering", "B.Pharm", "Diploma to Degree (D2D)", "MBA / BBA", "B.Sc Nursing"]
            question = "Which program are you asking about?"
            return True, question, programs

        return False, None, []

    @staticmethod
    def resolve_followup_context(user_reply: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Combines previous query intent + user's clarification response for refined retrieval.
        Example: Previous assistant message asked "Which program?", user replies "B.Tech CSE".
                 Combines into "B.Tech CSE Admission Process".
        """
        if not conversation_history or len(conversation_history) < 2:
            return user_reply

        # Find the last user query before the assistant's clarification
        last_user_query = ""
        last_assistant_msg = ""

        for msg in reversed(conversation_history):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "assistant" and not last_assistant_msg:
                last_assistant_msg = content
            elif role == "user" and not last_user_query:
                last_user_query = content
                break

        # Check if last assistant message was a clarification question
        if last_assistant_msg and ("which" in last_assistant_msg.lower() or "multiple records" in last_assistant_msg.lower() or "?" in last_assistant_msg):
            combined = f"{user_reply} {last_user_query}"
            logger.info(f"AmbiguityHandler: Combined follow-up context -> '{combined}'")
            return combined

        return user_reply
