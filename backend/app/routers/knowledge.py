from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
import asyncio
import json
import time
import hashlib
from app.services.crawler_service import crawl_kpgu_website
from app.services.text_processor import process_crawled_documents
from app.services.embedding_service import build_embeddings_from_chunks

router = APIRouter()

class CrawlResponse(BaseModel):
    status: str
    message: str

class UploadRequest(BaseModel):
    title: str
    content: str
    url: Optional[str] = "https://www.kpgu.ac.in/custom-doc"

class UploadResponse(BaseModel):
    status: str
    message: str
    document_id: Optional[str] = None

class RebuildResponse(BaseModel):
    status: str
    message: str

class KnowledgeStatusResponse(BaseModel):
    status: str
    document_count: int
    chunk_count: int
    last_updated: Optional[str] = None

class SourceResponse(BaseModel):
    id: int
    title: str
    url: str
    last_updated: str
    status: str

knowledge_status = {
    "status": "completed",
    "document_count": 0,
    "chunk_count": 0,
    "last_updated": None
}

@router.post("/crawl", response_model=CrawlResponse)
async def crawl_website(background_tasks: BackgroundTasks):
    """
    Trigger crawling of the KPGU website.
    """
    if knowledge_status["status"] == "crawling":
        raise HTTPException(status_code=409, detail="Crawl already in progress")

    knowledge_status["status"] = "crawling"
    background_tasks.add_task(run_full_pipeline)

    return CrawlResponse(
        status="started",
        message="Crawl started in background"
    )

@router.post("/upload", response_model=UploadResponse)
async def upload_document(request: UploadRequest, background_tasks: BackgroundTasks):
    """
    Upload a custom document text to process and add into the vector index.
    """
    try:
        raw_dir = "data/raw"
        os.makedirs(raw_dir, exist_ok=True)

        existing_files = [f for f in os.listdir(raw_dir) if f.startswith("document_") and f.endswith(".json")]
        next_idx = len(existing_files)
        doc_id = f"document_{next_idx:04d}"

        content_hash = hashlib.sha256(request.content.encode('utf-8')).hexdigest()
        doc = {
            "url": request.url,
            "title": request.title,
            "content": request.content,
            "content_hash": content_hash,
            "crawl_timestamp": time.time(),
            "word_count": len(request.content.split()),
            "char_count": len(request.content)
        }

        filepath = os.path.join(raw_dir, f"{doc_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

        # Trigger reprocessing and rebuilding embedding index in background
        background_tasks.add_task(run_processing_and_embedding)

        return UploadResponse(
            status="success",
            message="Document uploaded and processing queued",
            document_id=doc_id
        )
    except Exception as e:
        logging.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild_knowledge_base(background_tasks: BackgroundTasks):
    """
    Rebuild the entire knowledge base from scratch.
    """
    if knowledge_status["status"] == "rebuilding":
        raise HTTPException(status_code=409, detail="Rebuild already in progress")

    knowledge_status["status"] = "rebuilding"
    background_tasks.add_task(run_full_pipeline)

    return RebuildResponse(
        status="started",
        message="Knowledge base rebuild started in background"
    )

@router.get("/status", response_model=KnowledgeStatusResponse)
async def get_knowledge_status():
    """
    Get the current status of the knowledge base.
    """
    raw_dir = "data/raw"
    proc_dir = "data/processed"

    doc_count = len([f for f in os.listdir(raw_dir) if f.endswith('.json') and f != 'metadata.json']) if os.path.exists(raw_dir) else 0
    chunk_count = len([f for f in os.listdir(proc_dir) if f.endswith('.json') and f != 'metadata.json']) if os.path.exists(proc_dir) else 0

    knowledge_status["document_count"] = doc_count
    knowledge_status["chunk_count"] = chunk_count

    meta_path = "vector_store/metadata.json"
    if os.path.exists(meta_path):
        mtime = os.path.getmtime(meta_path)
        knowledge_status["last_updated"] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(mtime))

    return KnowledgeStatusResponse(**knowledge_status)

@router.get("/sources", response_model=List[SourceResponse])
async def get_sources():
    """
    Get indexed sources extracted from vector store metadata or raw directory.
    """
    meta_path = "vector_store/metadata.json"
    sources = []
    seen_urls = set()

    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
                idx = 1
                for item in metadata_list:
                    url = item.get("url", "https://www.kpgu.ac.in/")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        sources.append(SourceResponse(
                            id=idx,
                            title=item.get("title", "Indexed Document"),
                            url=url,
                            last_updated=time.strftime('%Y-%m-%d', time.localtime(item.get("crawl_timestamp", time.time()))),
                            status="Indexed"
                        ))
                        idx += 1
        except Exception as e:
            logging.error(f"Error reading metadata for sources: {e}")

    # Fallback to scanning raw directory if metadata list is empty
    if not sources and os.path.exists("data/raw"):
        try:
            idx = 1
            for filename in sorted(os.listdir("data/raw")):
                if filename.endswith(".json") and filename != "metadata.json":
                    with open(os.path.join("data/raw", filename), 'r', encoding='utf-8') as f:
                        doc = json.load(f)
                        url = doc.get("url", "https://www.kpgu.ac.in/")
                        if url not in seen_urls:
                            seen_urls.add(url)
                            sources.append(SourceResponse(
                                id=idx,
                                title=doc.get("title", filename),
                                url=url,
                                last_updated=time.strftime('%Y-%m-%d', time.localtime(doc.get("crawl_timestamp", time.time()))),
                                status="Indexed"
                            ))
                            idx += 1
        except Exception as e:
            logging.error(f"Error reading raw data for sources: {e}")

    return sources

async def run_processing_and_embedding():
    try:
        logger = logging.getLogger(__name__)
        logger.info("Processing raw documents into chunks...")
        knowledge_status["status"] = "processing"
        chunks = process_crawled_documents(input_dir="data/raw", output_dir="data/processed")
        knowledge_status["chunk_count"] = len(chunks)

        logger.info("Building vector embeddings...")
        knowledge_status["status"] = "embedding"
        success = build_embeddings_from_chunks(
            chunks_dir="data/processed",
            index_path="vector_store/faiss_index.bin",
            metadata_path="vector_store/metadata.json"
        )
        if success:
            knowledge_status["status"] = "completed"
        else:
            knowledge_status["status"] = "failed"
    except Exception as e:
        logging.error(f"Error in processing and embedding: {e}")
        knowledge_status["status"] = "failed"

async def run_full_pipeline():
    """
    Background task to run the full pipeline: crawl, process, embed.
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting full knowledge base pipeline...")

        knowledge_status["status"] = "crawling"
        documents = crawl_kpgu_website(max_pages=50)
        knowledge_status["document_count"] = len(documents)

        await run_processing_and_embedding()
    except Exception as e:
        logging.error(f"Knowledge base pipeline failed: {e}")
        knowledge_status["status"] = "failed"