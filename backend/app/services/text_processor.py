import re
import json
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TextProcessor:
    @staticmethod
    def normalize_user_query(query: str) -> str:
        if not query:
            return ""
        q = query.strip()
        typo_map = {
            r'\badmition\b': 'admission',
            r'\badmissions\b': 'admission',
            r'\brequried\b': 'required',
            r'\brequire\b': 'required',
            r'\bgenrate\b': 'generate',
            r'\bprocees\b': 'process',
            r'\bdokument\b': 'document',
            r'\bdokuments\b': 'documents',
        }
        for pattern, replacement in typo_map.items():
            q = re.sub(pattern, replacement, q, flags=re.IGNORECASE)
        return q

    def __init__(self):
        # Common heading patterns for semantic chunking
        self.heading_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown headings
            r'^[A-Z][A-Z\s]{2,}:$',  # ALL CAPS headings with colon
            r'^\d+\.\s+.+$',  # Numbered headings
            r'^[A-Z][a-z\s]+:\s*$',  # Title case headings with colon
        ]

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\-.,;:!?()\'\"@#$%^&*+=<>/\\|\[\]{}~\`]', ' ', text)

        # Remove multiple consecutive punctuation
        text = re.sub(r'([\-.,;:!?()])\1{2,}', r'\1', text)

        return text

    def extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections based on headings for semantic chunking"""
        lines = text.split('\n')
        sections = []
        current_section = {"heading": "Introduction", "content": ""}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line looks like a heading
            is_heading = False
            for pattern in self.heading_patterns:
                if re.match(pattern, line, re.MULTILINE | re.IGNORECASE):
                    is_heading = True
                    break

            # Also check for common heading indicators
            if not is_heading:
                # Short line that ends with colon or is all caps
                if (len(line) < 100 and
                    (line.endswith(':') or line.isupper()) and
                    not line.endswith('.') and
                    len(line.split()) <= 10):
                    is_heading = True

            if is_heading and current_section["content"].strip():
                # Save current section and start new one
                sections.append(current_section)
                current_section = {"heading": line, "content": ""}
            else:
                # Add to current section
                if current_section["content"]:
                    current_section["content"] += " " + line
                else:
                    current_section["content"] = line

        # Don't forget the last section
        if current_section["content"].strip():
            sections.append(current_section)

        return sections

    def semantic_chunking(self, text: Any, max_chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        """Create semantic chunks from text or document dict"""
        if not text:
            return []

        doc_title = None
        if isinstance(text, dict):
            doc_title = text.get("title") or "KPGU Document"
            raw_content = text.get("content", "")
            text = str(raw_content)

        if not isinstance(text, str) or not text.strip():
            return []

        # First try to extract sections
        sections = self.extract_sections(text)

        chunks = []
        for section in sections:
            section_text = f"{section['heading']}\n{section['content']}".strip()

            # If section is small enough, keep it as one chunk
            if len(section_text) <= max_chunk_size:
                chunks.append({
                    "text": section_text,
                    "content": section_text,
                    "title": doc_title or section["heading"],
                    "heading": section["heading"],
                    "section_type": "semantic"
                })
            else:
                # Split large section into smaller chunks
                section_chunks = self._split_text(
                    section_text,
                    max_chunk_size,
                    overlap,
                    section["heading"]
                )
                for sc in section_chunks:
                    sc["content"] = sc["text"]
                    sc["title"] = doc_title or section["heading"]
                chunks.extend(section_chunks)

        # If no sections were found, fall back to regular chunking
        if not chunks:
            chunks = self._split_text(text, max_chunk_size, overlap, "Content")
            for sc in chunks:
                sc["content"] = sc["text"]
                sc["title"] = doc_title or "Content"

        return chunks

    def _split_text(self, text: str, max_size: int, overlap: int, heading: str) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap"""
        if len(text) <= max_size:
            return [{"text": text, "heading": heading, "section_type": "split"}]

        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + max_size

            # If we're not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings near the end
                search_start = max(start, end - 100)
                search_text = text[search_start:end]

                # Find last sentence ending
                sentence_end = -1
                for punct in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                    pos = search_text.rfind(punct)
                    if pos > sentence_end:
                        sentence_end = pos + len(punct) - 1  # Adjust for the space we added

                if sentence_end != -1 and (search_start + sentence_end + 1) > start + overlap:
                    end = search_start + sentence_end + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "heading": heading,
                    "section_type": "split",
                    "chunk_id": chunk_id
                })
                chunk_id += 1

            # Move start position with overlap, ensuring strictly positive progress
            next_start = end - overlap
            if next_start <= start:
                start = end
            else:
                start = next_start

            if start >= len(text) or end >= len(text):
                break

        return chunks

    def process_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single document into chunks"""
        try:
            # Clean the content
            cleaned_content = self.clean_text(document.get("content", ""))

            if not cleaned_content:
                return []

            # Create semantic chunks
            chunks = self.semantic_chunking(cleaned_content)

            # Add metadata to each chunk
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                processed_chunk = {
                    "document_id": document.get("url", ""),
                    "document_title": document.get("title", ""),
                    "url": document.get("url", ""),
                    "title": document.get("title", ""),
                    "category": document.get("category", "general"),
                    "content": chunk["text"],
                    "chunk_index": i,
                    "section": chunk.get("heading", ""),
                    "chunk_id": f"{document.get('url', '')}_{i}",
                    "content_hash": document.get("content_hash", ""),
                    "timestamp": document.get("crawl_timestamp", datetime.now().timestamp()),
                    "word_count": len(chunk["text"].split())
                }
                processed_chunks.append(processed_chunk)

            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing document {document.get('url', 'unknown')}: {e}")
            return []

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple documents into chunks"""
        all_chunks = []

        for document in documents:
            chunks = self.process_document(document)
            all_chunks.extend(chunks)

        logger.info(f"Processed {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks

def process_crawled_documents(input_dir: str = None, output_dir: str = None) -> List[Dict[str, Any]]:
    """Process all crawled documents"""
    from app.config import settings
    if input_dir is None:
        input_dir = settings.DATA_RAW_DIR
    if output_dir is None:
        output_dir = settings.DATA_PROCESSED_DIR

    os.makedirs(output_dir, exist_ok=True)

    processor = TextProcessor()
    documents = []

    # Load documents from raw directory
    if os.path.exists(input_dir):
        for filename in sorted(os.listdir(input_dir)):
            if filename.endswith(".json") and filename != "metadata.json":
                filepath = os.path.join(input_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        document = json.load(f)
                        if isinstance(document, dict) and document.get("content"):
                            documents.append(document)
                except Exception as e:
                    logger.error(f"Error loading {filepath}: {e}")

    # Process documents
    chunks = processor.process_documents(documents)

    # Save processed chunks to primary output_dir
    for i, chunk in enumerate(chunks):
        filename = f"chunk_{i:04d}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=2, ensure_ascii=False)

    # Save metadata
    metadata = {
        "total_chunks": len(chunks),
        "processed_timestamp": datetime.now().timestamp(),
        "source_documents": len(documents)
    }

    with open(os.path.join(output_dir, "metadata.json"), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved {len(chunks)} processed chunks to {output_dir}")

    # Mirror to alternate root/backend processed dir if applicable
    root_processed = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "data", "processed"))
    if os.path.abspath(output_dir) != root_processed and os.path.exists(os.path.dirname(root_processed)):
        try:
            os.makedirs(root_processed, exist_ok=True)
            for i, chunk in enumerate(chunks):
                fname = f"chunk_{i:04d}.json"
                with open(os.path.join(root_processed, fname), 'w', encoding='utf-8') as f:
                    json.dump(chunk, f, indent=2, ensure_ascii=False)
            with open(os.path.join(root_processed, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Mirrored {len(chunks)} processed chunks to {root_processed}")
        except Exception as e:
            logger.warning(f"Could not mirror chunks to {root_processed}: {e}")

    return chunks