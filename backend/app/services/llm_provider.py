import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Allows easy switching between Gemini, OpenAI, or local LLM backends.
    """
    @abstractmethod
    async def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], history: List[Dict[str, str]] = None, is_benefits_intent: bool = False) -> str:
        pass

class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM Implementation.
    Generates concise responses based STRICTLY on retrieved university context.
    Supports Intent-Aware Benefit structuring ("Why KPGU?") and Strict Topic-Scope Filtering.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL_NAME
        self._configured = False

    def _configure_api(self):
        api_key = settings.GEMINI_API_KEY
        if api_key:
            genai.configure(api_key=api_key)
            self._configured = True

    async def generate_response(self, query: str, context_chunks: List[Dict[str, Any]], history: List[Dict[str, str]] = None, is_benefits_intent: bool = False) -> str:
        self._configure_api()
        if not settings.GEMINI_API_KEY:
            logger.warning("GeminiProvider: GEMINI_API_KEY not configured")
            return self._build_direct_fallback_answer(query, context_chunks, is_benefits_intent)

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": settings.MAX_OUTPUT_TOKENS,
                    "top_p": 0.8
                }
            )

            # Strict System Instruction with Topic-Scope Filtering
            benefit_guideline = ""
            if is_benefits_intent:
                benefit_guideline = (
                    "\n7. INTENT GUIDELINE FOR 'WHY KPGU?' / BENEFIT QUESTIONS:\n"
                    "   - Frame response objectively as 'Factors to Consider Based on Official KPGU Data'.\n"
                    "   - Summarize documented advantages (e.g. 60+ programs, recognitions, placements, facilities, labs, scholarships).\n"
                    "   - Do NOT make unsupported claims like 'best university in Gujarat' or 'guaranteed job'. Use factual phrasing like 'According to available KPGU information...'.\n"
                )

            system_instruction = (
                "You are the official KPGU AI University Assistant for Drs. Kiran & Pallavi Patel Global University, Vadodara.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. Answer ONLY using the supplied KPGU Knowledge Context below.\n"
                "2. Do NOT use outside knowledge, general assumptions, or guessing.\n"
                "3. If the supplied context does NOT contain enough factual information to answer the question, output EXACTLY:\n"
                "   \"Not in data set.\"\n"
                "4. STRICT TOPIC SCOPE: Answer ONLY the specific topic requested by the user. If the user asks about hostel facilities, include ONLY hostel details (rooms, amenities, security, Wi-Fi, mess, hostel fee). Do NOT append unrelated B.Tech/B.Pharm/MBA tuition fees, general establishment history, or non-hostel facts merely because they appear in the retrieved context.\n"
                "5. METADATA PROTECTION: Never output raw internal document labels like 'Pdf for hostel Fees' or file IDs in text unless the user explicitly requested a PDF/document.\n"
                "6. Keep your answer clear, accurate, professional, and well-structured using markdown bullet points when appropriate.\n"
                "7. If the user asks in Hindi or Gujarati, respond in that language using ONLY the supplied context facts."
                f"{benefit_guideline}"
            )

            history_text = ""
            if history:
                recent_history = history[-settings.MAX_HISTORY_MESSAGES:]
                for msg in recent_history:
                    role = msg.get("role", "user").capitalize()
                    content = msg.get("content", "").strip()
                    if content and content != "Not in data set.":
                        history_text += f"{role}: {content}\n"

            context_text = ""
            if context_chunks:
                for idx, chunk in enumerate(context_chunks, 1):
                    title = chunk.get("title", "KPGU Information")
                    content = chunk.get("content", "").strip()
                    url = chunk.get("url", "https://www.kpgu.ac.in/")
                    context_text += f"\n--- Source [{idx}]: {title} ({url}) ---\n{content}\n"

            prompt = (
                f"{system_instruction}\n\n"
                f"Conversation History:\n{history_text}\n"
                f"Supplied KPGU Knowledge Context:\n{context_text}\n\n"
                f"User Question: {query}\n\n"
                f"Answer:"
            )

            response = await asyncio.to_thread(model.generate_content, prompt)
            answer_text = response.text.strip() if response and response.text else "Not in data set."

            if not answer_text or "not in data set" in answer_text.lower():
                return "Not in data set."

            return answer_text

        except Exception as e:
            logger.error(f"GeminiProvider API error: {e}")
            return self._build_direct_fallback_answer(query, context_chunks, is_benefits_intent)

    def _build_direct_fallback_answer(self, query: str, context_chunks: List[Dict[str, Any]], is_benefits_intent: bool = False) -> str:
        if not context_chunks:
            return "Not in data set."

        clean_facts = [c.get("content", "").strip() for c in context_chunks[:4] if c.get("content", "").strip()]
        if not clean_facts:
            return "Not in data set."

        if is_benefits_intent:
            bullets = "\n\n".join([f"• **Key Factor**: {fact}" for fact in clean_facts[:3]])
            return f"### 🎓 Factors to Consider for KPGU Admission\n\nBased on official KPGU information available, factors you may consider include:\n\n{bullets}\n\n🔗 **Official University Website**: [kpgu.ac.in](https://www.kpgu.ac.in/)"

        bullets = "\n\n".join([f"• {fact}" for fact in clean_facts[:3]])
        return f"{bullets}\n\n🔗 **Official University Website**: [kpgu.ac.in](https://www.kpgu.ac.in/)"
