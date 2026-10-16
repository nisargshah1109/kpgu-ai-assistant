import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import logging
from typing import List, Dict, Any, Optional
import time

from app.db import SessionLocal
from app.Models import Conversation, Message
from app.config import settings
from app.services.query_gater import QueryGater
from app.services.hybrid_retriever import HybridRetriever
from app.services.llm_provider import GeminiProvider
from app.services.ambiguity_handler import AmbiguityHandler
from app.services.pdf_service import PDFService
from app.services.intent_detector import IntentDetector, QueryIntent
from app.services.entity_extractor import EntityExtractor
from app.services.entity_relevance_gate import EntityRelevanceGate
from app.services.topic_context_filter import TopicContextFilter

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.llm_provider = GeminiProvider()

    async def process_chat_message(self,
                                 conversation_id: int,
                                 user_message: str,
                                 db: SessionLocal) -> Dict[str, Any]:
        clean_user_query = user_message.strip()

        # 1. Save user message to database
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=clean_user_query
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 2. Get past conversation history for context preservation
        past_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        history_list = [
            {"role": m.role, "content": m.content}
            for m in past_messages[:-1]
        ]

        from app.services.text_processor import TextProcessor
        normalized_query = TextProcessor.normalize_user_query(clean_user_query)

        # 3. Detect User Intent & Extract Entities
        intent, intent_meta = IntentDetector.detect_intent(normalized_query)
        is_benefits_intent = (intent == QueryIntent.BENEFITS_WHY)
        primary_entity, entity_type = EntityExtractor.extract_entity(normalized_query)

        # 4. Check for Follow-Up Clarification Context Resolution
        search_query = AmbiguityHandler.resolve_followup_context(normalized_query, history_list)

        # 5. Check Explicit PDF Request Intent
        user_wants_pdf = PDFService.is_pdf_requested(clean_user_query)

        # 6. Pre-LLM Query Scope Detection
        is_relevant, gate_reason = QueryGater.is_kpgu_related(search_query)
        if not is_relevant:
            logger.info(f"ChatService: Query Gater blocked non-KPGU query '{clean_user_query}'")
            not_found_answer = "Not in data set."

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=not_found_answer
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)

            return {
                "conversation_id": conversation_id,
                "answer": not_found_answer,
                "message_id": assistant_msg.id,
                "data_found": False,
                "sources": []
            }

        # 7. Hybrid RAG Retrieval with Entity-First Boosting
        retrieved_chunks = self.retriever.retrieve(
            query=search_query,
            top_k=settings.MAX_CONTEXT_CHUNKS,
            threshold=settings.RELEVANCE_THRESHOLD,
            is_benefits_intent=is_benefits_intent,
            primary_entity=primary_entity
        )

        # 8. Strict Entity Relevance Gate Validation
        has_entity_chunks, valid_chunks = EntityRelevanceGate.validate_entity_chunks(
            primary_entity=primary_entity,
            entity_type=entity_type,
            chunks=retrieved_chunks
        )

        if not has_entity_chunks or not valid_chunks:
            logger.info(f"ChatService: Entity Relevance Gate failed for primary entity '{primary_entity}'. Returning 'Not in data set.' without Gemini call.")
            not_found_answer = "Not in data set."

            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=not_found_answer
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)

            return {
                "conversation_id": conversation_id,
                "answer": not_found_answer,
                "message_id": assistant_msg.id,
                "data_found": False,
                "sources": []
            }

        # 9. Strict Topic-Level Context Filtering (Removes cross-topic pollution like tuition fees in hostel queries)
        retrieved_chunks = TopicContextFilter.filter_chunks(search_query, valid_chunks)

        if not retrieved_chunks:
            not_found_answer = "Not in data set."
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=not_found_answer
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)

            return {
                "conversation_id": conversation_id,
                "answer": not_found_answer,
                "message_id": assistant_msg.id,
                "data_found": False,
                "sources": []
            }

        # 10. Check for Universal Ambiguity (Multiple Record Candidates)
        if not user_wants_pdf and not is_benefits_intent:
            is_ambiguous, clarification_prompt, options = AmbiguityHandler.detect_ambiguity(search_query, retrieved_chunks)
            if is_ambiguous:
                logger.info(f"ChatService: Ambiguity detected for '{search_query}'. Asking clarification: {clarification_prompt}")
                
                assistant_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=clarification_prompt
                )
                db.add(assistant_msg)
                db.commit()
                db.refresh(assistant_msg)

                return {
                    "conversation_id": conversation_id,
                    "answer": clarification_prompt,
                    "message_id": assistant_msg.id,
                    "data_found": True,
                    "is_ambiguous": True,
                    "clarification_options": options,
                    "sources": []
                }

        # 11. Generate Answer using Gemini Provider with Topic Scope Instructions
        answer = await self.llm_provider.generate_response(
            query=search_query,
            context_chunks=retrieved_chunks,
            history=history_list,
            is_benefits_intent=is_benefits_intent
        )

        data_found = True
        if answer.strip() == "Not in data set.":
            data_found = False

        # Extract verified sources
        sources = []
        seen_urls = set()
        if data_found:
            for chunk in retrieved_chunks:
                url = chunk.get("url", settings.KPGU_BASE_URL)
                title = chunk.get("title") or chunk.get("document_title") or "KPGU Information"
                ts = chunk.get("timestamp") or time.time()
                date_str = time.strftime('%Y-%m-%d', time.localtime(ts)) if ts else None

                if url not in seen_urls:
                    seen_urls.add(url)
                    sources.append({
                        "title": title,
                        "url": url,
                        "last_updated": date_str
                    })

        # 12. Handle Explicit PDF Export URL if user requested PDF
        pdf_export_url = None
        if user_wants_pdf and data_found:
            pdf_export_url = f"{settings.KPGU_BASE_URL}api/conversations/{conversation_id}/export-pdf"
            answer = f"{answer}\n\n📄 **Requested PDF Document**: You can download your requested PDF using the Download Chat button or [Click Here to Download Document]({pdf_export_url})."

        # Save assistant message to DB
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "message_id": assistant_msg.id,
            "data_found": data_found,
            "pdf_export_url": pdf_export_url,
            "sources": sources if data_found else []
        }