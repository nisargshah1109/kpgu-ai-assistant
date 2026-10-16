import os
import sys

# Isolate torchvision to prevent operator torchvision::nms runtime crash in transformers
if "torchvision" not in sys.modules:
    sys.modules["torchvision"] = None

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import logging
logger = logging.getLogger(__name__)
import numpy as np

try:
    import faiss
except Exception as e:
    logger.warning(f"FAISS module import warning: {e}")
    faiss = None

import json
import hashlib
from typing import List, Dict, Any, Optional
from app.config import settings

class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.metadata = []

    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.model = None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        if self.model is None:
            self._load_model()
        if self.model is None:
            logger.error("Embedding model not loaded")
            return None

        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        """Generate embeddings for a batch of texts"""
        if self.model is None:
            self._load_model()
        if self.model is None:
            logger.error("Embedding model not loaded")
            return None

        try:
            embeddings = self.model.encode(texts)
            return embeddings.astype('float32')
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return None

    def build_index(self, chunks: List[Dict[str, Any]]) -> bool:
        """Build FAISS index from chunks"""
        if self.model is None:
            self._load_model()
        if self.model is None:
            logger.error("Embedding model not loaded")
            return False

        if not chunks:
            logger.warning("No chunks provided for indexing")
            return False

        try:
            # Extract texts for embedding
            texts = [chunk.get("content", "") for chunk in chunks]
            texts = [text for text in texts if text.strip()]  # Remove empty texts

            if not texts:
                logger.warning("No valid texts to embed")
                return False

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.generate_embeddings_batch(texts)

            if embeddings is None:
                return False

            # Initialize FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)

            # Add to index
            self.index.add(embeddings)

            # Store metadata (only for chunks that had valid text)
            valid_chunks = []
            text_idx = 0
            for chunk in chunks:
                if chunk.get("content", "").strip():
                    valid_chunks.append(chunk)
                    text_idx += 1
                else:
                    # Add placeholder metadata for empty chunks
                    valid_chunks.append(chunk)

            self.metadata = valid_chunks

            logger.info(f"Built FAISS index with {self.index.ntotal} vectors of dimension {dimension}")
            return True

        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
            return False

    def save_index(self, index_path: Optional[str] = None,
                   metadata_path: Optional[str] = None):
        """Save FAISS index and metadata to disk with dual-mirroring"""
        if index_path is None:
            index_path = settings.VECTOR_INDEX_PATH
        if metadata_path is None:
            metadata_path = settings.METADATA_PATH

        try:
            # Create primary directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)

            if self.index is not None:
                faiss.write_index(self.index, index_path)
                logger.info(f"Saved FAISS index to {index_path}")

            # Save metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata to {metadata_path}")

            # Mirror to root vector_store if saving to backend, or vice versa
            root_dir = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "vector_store"))
            backend_dir = os.path.abspath(os.path.join(settings.BASE_DIR, "vector_store"))
            target_dirs = [root_dir, backend_dir]

            for t_dir in target_dirs:
                t_idx = os.path.join(t_dir, "faiss_index.bin")
                t_meta = os.path.join(t_dir, "metadata.json")
                if os.path.abspath(index_path) != os.path.abspath(t_idx):
                    try:
                        os.makedirs(t_dir, exist_ok=True)
                        if self.index is not None:
                            faiss.write_index(self.index, t_idx)
                        with open(t_meta, 'w', encoding='utf-8') as f:
                            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
                        logger.info(f"Mirrored FAISS index and metadata to {t_dir}")
                    except Exception as me:
                        logger.warning(f"Could not mirror index to {t_dir}: {me}")

            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False

    def load_index(self, index_path: Optional[str] = None,
                   metadata_path: Optional[str] = None) -> bool:
        """Load FAISS index and metadata from disk"""
        if index_path is None:
            index_path = settings.VECTOR_INDEX_PATH
        if metadata_path is None:
            metadata_path = settings.METADATA_PATH

        try:
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                self.index = faiss.read_index(index_path)
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
                return True
            else:
                logger.warning(f"Index or metadata file not found: {index_path}, {metadata_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index not available or empty")
            return []

        if self.model is None:
            logger.error("Embedding model not loaded")
            return []

        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if query_embedding is None:
                return []

            query_vector = np.array([query_embedding], dtype='float32')
            faiss.normalize_L2(query_vector)  # Normalize for cosine similarity

            # Search
            distances, indices = self.index.search(query_vector, k)

            # Get results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['similarity_score'] = float(distances[0][i])
                    results.append(result)

            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return []

def build_embeddings_from_chunks(chunks_dir: Optional[str] = None,
                                index_path: Optional[str] = None,
                                metadata_path: Optional[str] = None) -> bool:
    """Build embeddings from processed chunks"""
    if chunks_dir is None:
        chunks_dir = settings.DATA_PROCESSED_DIR
    if index_path is None:
        index_path = settings.VECTOR_INDEX_PATH
    if metadata_path is None:
        metadata_path = settings.METADATA_PATH

    try:
        # Load chunks
        chunks = []
        if os.path.exists(chunks_dir):
            for filename in sorted(os.listdir(chunks_dir)):
                if filename.endswith(".json") and filename != "metadata.json":
                    filepath = os.path.join(chunks_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            chunk = json.load(f)
                            if isinstance(chunk, dict) and chunk.get("content"):
                                chunks.append(chunk)
                    except Exception as e:
                        logger.error(f"Error loading chunk {filepath}: {e}")

        if not chunks:
            logger.warning("No chunks found to process")
            return False

        # Build index
        embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL_NAME)
        success = embedding_service.build_index(chunks)

        if success:
            embedding_service.save_index(index_path, metadata_path)
            logger.info(f"Successfully built embeddings for {len(chunks)} chunks")
            return True
        else:
            logger.error("Failed to build embeddings index")
            return False

    except Exception as e:
        logger.error(f"Error in build_embeddings_from_chunks: {e}")
        return False