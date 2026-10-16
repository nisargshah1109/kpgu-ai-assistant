#!/usr/bin/env python3
"""
Test script to build the KPGU AI Assistant knowledge base with limited pages.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the backend app to the path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.crawler_service import crawl_kpgu_website
from app.services.text_processor import process_crawled_documents
from app.services.embedding_service import build_embeddings_from_chunks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the knowledge base build pipeline"""
    logger.info("Starting KPGU AI Assistant knowledge base build (test with 1 page)...")

    try:
        # Step 1: Crawl website - limit to 1 page for testing
        logger.info("Step 1: Crawling KPGU website (max 1 page)...")
        documents = crawl_kpgu_website(max_pages=1)  # Only 1 page for test
        logger.info(f"Crawled {len(documents)} documents")

        if len(documents) == 0:
            logger.warning("No documents were crawled. Check website connectivity.")
            return False

        # Step 2: Process documents
        logger.info("Step 2: Processing documents...")
        chunks = process_crawled_documents(
            input_dir="data/raw",
            output_dir="data/processed"
        )
        logger.info(f"Processed {len(chunks)} chunks")

        if len(chunks) == 0:
            logger.warning("No chunks were generated from crawled documents.")
            return False

        # Step 3: Generate embeddings
        logger.info("Step 3: Generating embeddings and building FAISS index...")
        success = build_embeddings_from_chunks(
            chunks_dir="data/processed",
            index_path="vector_store/faiss_index.bin",
            metadata_path="vector_store/metadata.json"
        )

        if success:
            logger.info("Knowledge base build completed successfully!")
            logger.info(f"- Documents: {len(documents)}")
            logger.info(f"- Chunks: {len(chunks)}")
            logger.info("- FAISS index built and saved")
            return True
        else:
            logger.error("Failed to build embeddings index")
            return False

    except Exception as e:
        logger.error(f"Knowledge base build failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)