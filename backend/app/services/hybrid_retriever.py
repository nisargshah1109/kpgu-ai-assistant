import os
import json
import math
import re
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

try:
    import faiss
except Exception as e:
    logger.warning(f"FAISS module import notice in hybrid_retriever: {e}")
    faiss = None

class HybridRetriever:
    """
    Hybrid Retriever combining BM25 keyword scoring and SentenceTransformer vector similarity.
    Supports Entity-First Boost and Intent-Aware ranking.
    Enforces a strict configurable RELEVANCE_THRESHOLD.
    """
    def __init__(self, metadata_path: str = "vector_store/metadata.json", index_path: str = "vector_store/faiss_index.bin"):
        self.metadata_path = metadata_path
        self.index_path = index_path
        self.metadata: List[Dict[str, Any]] = []
        self.faiss_index = None
        self.embedding_model = None
        self._load_store()

    def _load_store(self):
        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"HybridRetriever: Loaded {len(self.metadata)} metadata chunks")

            if faiss is not None and os.path.exists(self.index_path):
                self.faiss_index = faiss.read_index(self.index_path)
                logger.info(f"HybridRetriever: Loaded FAISS index with {self.faiss_index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error loading vector store in HybridRetriever: {e}")

    def _get_embedding_model(self):
        if self.embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            except Exception as e:
                logger.error(f"Error loading embedding model: {e}")
        return self.embedding_model

    def _compute_bm25_score(self, query: str, document_text: str) -> float:
        if not query or not document_text:
            return 0.0

        q_clean = query.lower()
        doc_clean = document_text.lower()
        
        q_tokens = [w for w in re.findall(r'\b\w+\b', q_clean) if len(w) >= 2]
        if not q_tokens:
            return 0.0

        course_codes = re.findall(r'\b(?:\d{2}[A-Z]{2,4}\d{3,4}|[A-Z]{2,4}-\d{3,4}|\d{5,8})\b', q_clean, re.IGNORECASE)
        code_boost = 0.0
        for code in course_codes:
            if code.lower() in doc_clean:
                code_boost += 0.5

        matches = 0
        total_tf = 0
        doc_words = doc_clean.split()
        doc_len = len(doc_words) if doc_words else 1

        stop_words = {"what", "is", "the", "who", "where", "how", "for", "in", "on", "of", "and", "to", "a", "an", "are", "about"}
        meaningful_tokens = [w for w in q_tokens if w not in stop_words]
        tokens_to_check = meaningful_tokens if meaningful_tokens else q_tokens

        for token in tokens_to_check:
            count = doc_clean.count(token)
            if count > 0:
                matches += 1
                total_tf += math.log(1 + count)

        match_ratio = matches / len(tokens_to_check)
        score = (0.5 * match_ratio) + (0.4 * min(total_tf / (doc_len ** 0.5 + 1), 1.0)) + code_boost
        return min(score, 1.0)

    def retrieve(self,
                 query: str,
                 top_k: int = None,
                 threshold: float = None,
                 is_benefits_intent: bool = False,
                 primary_entity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks matching query using Hybrid Retrieval.
        Supports Entity-First Boosting (substantially boosting exact entity record matches).
        Applies strict RELEVANCE_THRESHOLD filter.
        """
        if top_k is None:
            top_k = settings.MAX_CONTEXT_CHUNKS
        if threshold is None:
            threshold = settings.RELEVANCE_THRESHOLD

        self._load_store()
        if not self.metadata:
            return []

        # 1. Compute Vector Similarity Scores
        vector_scores = [0.0] * len(self.metadata)
        model = self._get_embedding_model()

        if model is not None:
            try:
                q_embedding = model.encode([query])[0]
                q_vec = np.array([q_embedding], dtype='float32')

                if self.faiss_index is not None and faiss is not None and self.faiss_index.ntotal == len(self.metadata):
                    faiss.normalize_L2(q_vec)
                    distances, indices = self.faiss_index.search(q_vec, min(top_k * 4, len(self.metadata)))
                    for i, idx in enumerate(indices[0]):
                        if 0 <= idx < len(self.metadata):
                            score = max(0.0, float(distances[0][i]))
                            vector_scores[idx] = score
                else:
                    norm_q = np.linalg.norm(q_embedding)
                    if norm_q > 0:
                        q_unit = q_embedding / norm_q
                        for idx, chunk in enumerate(self.metadata):
                            content = chunk.get("content", "")
                            bm25 = self._compute_bm25_score(query, f"{chunk.get('title','')} {content}")
                            vector_scores[idx] = bm25
            except Exception as e:
                logger.error(f"Error computing vector similarity: {e}")

        # 2. Compute BM25 Keyword Scores & Combine with Entity Boost
        hybrid_results = []
        entity_tokens = [w for w in re.findall(r'\b\w+\b', primary_entity.lower()) if w not in ["dr", "prof", "professor", "hod", "dean", "who", "is", "the", "what"]] if primary_entity else []

        for idx, chunk in enumerate(self.metadata):
            content = chunk.get("content", "")
            title = chunk.get("title", "")
            full_text = f"{title}\n{content}"

            if not content.strip():
                continue

            bm25_score = self._compute_bm25_score(query, full_text)
            vec_score = vector_scores[idx]

            if vec_score > 0:
                combined_score = (vec_score * 0.6) + (bm25_score * 0.4)
            else:
                combined_score = bm25_score

            if bm25_score > 0.15:
                combined_score = max(combined_score, bm25_score)

            # Entity-First Match Boost
            if primary_entity and entity_tokens:
                doc_lower = full_text.lower()
                matches = sum(1 for token in entity_tokens if token in doc_lower)
                if matches == len(entity_tokens):
                    # Substantial boost for chunks actually containing the requested named entity!
                    combined_score += 0.5
                    combined_score = min(combined_score, 1.0)

            # Benefit Intent Boost
            if is_benefits_intent:
                doc_lower = full_text.lower()
                benefit_keywords = ["placement", "recruiter", "facility", "accreditation", "recognition", "scholarship", "laboratory", "infrastructure", "program"]
                b_matches = sum(1 for k in benefit_keywords if k in doc_lower)
                if b_matches > 0:
                    combined_score += (0.08 * min(b_matches, 3))

            if bm25_score > 0.6:
                combined_score = max(combined_score, bm25_score)

            if combined_score >= threshold:
                res_chunk = chunk.copy()
                res_chunk["similarity_score"] = float(round(combined_score, 4))
                res_chunk["vector_score"] = float(round(vec_score, 4))
                res_chunk["bm25_score"] = float(round(bm25_score, 4))
                hybrid_results.append(res_chunk)

        hybrid_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_chunks = hybrid_results[:top_k]

        logger.info(f"HybridRetriever query='{query}' (primary_entity='{primary_entity}'): Found {len(top_chunks)} chunks above threshold {threshold}")
        return top_chunks
