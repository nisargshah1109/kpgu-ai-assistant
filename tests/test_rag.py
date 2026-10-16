import sys
import os
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.text_processor import TextProcessor
from app.services.embedding_service import EmbeddingService

def test_text_processor_cleaning():
    processor = TextProcessor()
    raw_text = "  KPGU   University   is   located  in  Vadodara,   Gujarat.  \n\n\n  "
    cleaned = processor.clean_text(raw_text)
    assert cleaned == "KPGU University is located in Vadodara, Gujarat."

def test_semantic_chunking():
    processor = TextProcessor()
    doc = {
        "title": "KPGU Overview",
        "url": "https://www.kpgu.ac.in/about",
        "content": "KPGU (Karnataka Pavitra Group of Universities) provides top quality higher education. Facilities include modern labs, library, and hostels. Admission requires 12th standard completion."
    }
    chunks = processor.semantic_chunking(doc, max_chunk_size=100)
    assert len(chunks) > 0
    assert chunks[0]["title"] == "KPGU Overview"
    assert "content" in chunks[0]

def test_embedding_generation_and_faiss():
    service = EmbeddingService()

    # Test single embedding
    embedding = service.generate_embedding("KPGU Admission details")
    assert embedding is not None
    assert len(embedding) == 384

    # Test indexing sample chunks
    sample_chunks = [
        {"title": "KPGU Courses", "url": "https://kpgu.ac.in/courses", "content": "Engineering, Pharmacy, Management and Science courses.", "content_hash": "hash1"},
        {"title": "KPGU Hostel", "url": "https://kpgu.ac.in/hostel", "content": "Separate hostels for boys and girls with 24x7 security and mess.", "content_hash": "hash2"}
    ]

    success = service.build_index(sample_chunks)
    assert success is True

    # Test search
    results = service.search("Where do students live?", k=1)
    assert len(results) == 1
    assert "Hostel" in results[0]["title"] or "hostel" in results[0]["content"].lower()
