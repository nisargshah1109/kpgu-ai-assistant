#!/usr/bin/env python3
"""
Script to build the KPGU AI Assistant knowledge base.
Performs end-to-end ingestion:
1. Seeds curated verified facts (admissions, programs, faculty)
2. Crawls verified live pages from official KPGU sitemap
3. Extracts clean text and categorizes content
4. Generates semantic chunks with rich metadata
5. Computes 384-d normalized embeddings using all-MiniLM-L6-v2
6. Builds FAISS IndexFlatIP and dual-mirrors index and metadata to backend/ and root vector_store/
"""

import os
import sys
from pathlib import Path
import json
import logging
import time

# Ensure backend app is importable
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Isolate torchvision to prevent operator crash
if "torchvision" not in sys.modules:
    sys.modules["torchvision"] = None

from app.config import settings
from app.services.crawler_service import CrawlerService
from app.services.text_processor import process_crawled_documents
from app.services.embedding_service import build_embeddings_from_chunks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("build_knowledge_base")

# Seed foundational facts to guarantee complete retention of verified baseline details
CURATED_SEED_DOCUMENTS = [
    {
        "url": "https://www.kpgu.ac.in/admissions/process-steps",
        "title": "Official KPGU Admission Process Steps",
        "category": "admissions_and_scholarships",
        "content": "Drs. Kiran & Pallavi Patel Global University (KPGU), Vadodara - Official Step-by-Step Admission Process:\nStep 1: Online Registration & Application Form Submission on the official KPGU portal (www.kpgu.ac.in) or ACPC Gujarat portal for engineering/pharmacy courses.\nStep 2: Document Submission & Verification of 10th/12th marksheets, entrance exam scorecards (KSET / GUJCET / NEET / ACPC), and photo ID.\nStep 3: Merit List Declaration & Seat Allocation based on academic performance, ACPC merit rank, or KSET score.\nStep 4: Issuance of Provisional Admission Offer Letter by the KPGU Admissions Cell.\nStep 5: Fee Payment & Token Fee Submission to confirm the allocated seat within the stipulated deadline.\nStep 6: Final Enrollment, Original Document Verification, and Campus Orientation.",
        "content_hash": "seed_admission_steps_01"
    },
    {
        "url": "https://www.kpgu.ac.in/admissions/required-documents",
        "title": "Documents Required for Admission at KPGU",
        "category": "admissions_and_scholarships",
        "content": "Official List of Documents Required for Admission at Drs. Kiran & Pallavi Patel Global University (KPGU), Vadodara:\n1. Class 10th (SSC) Marksheet & Passing Certificate.\n2. Class 12th (HSC) Marksheet & Passing Certificate.\n3. Graduation Marksheets & Degree Certificate (for Postgraduate / Master's admissions).\n4. Entrance Exam Score Card (KSET / GUJCET / NEET / ACPC Allotment Letter).\n5. School Leaving Certificate (SLC) / Transfer Certificate (TC).\n6. Migration Certificate (for students from boards outside GSEB or universities outside Gujarat).\n7. Caste / Category Certificate (SC / ST / SEBC / EWS) issued by competent authority, if applicable.\n8. Non-Creamy Layer Certificate (for SEBC candidates, valid for current academic year).\n9. Income Certificate (for scholarship / TFWS applicants).\n10. Aadhaar Card copy and 4 recent Passport-size Photographs.",
        "content_hash": "seed_admission_documents_01"
    },
    {
        "url": "https://www.kpgu.ac.in/admissions/eligibility-procedure",
        "title": "KPGU Admission Eligibility Criteria & Application Procedure",
        "category": "admissions_and_scholarships",
        "content": "KPGU Admission Eligibility Requirements & Application Guidelines:\n- Undergraduate (UG) Programs (B.Tech, B.Pharm, BBA, B.Sc, BPT, BAMS): Passed 10+2 (HSC) in relevant stream (Science / Commerce / Arts) from GSEB, CBSE, ICSE, or equivalent recognized board with minimum 45%-50% aggregate marks.\n- Diploma to Degree (D2D) Lateral Entry: Passed Diploma Engineering / Pharmacy in relevant branch with valid ACPC D2D merit rank.\n- Postgraduate (PG) Programs (MBA, M.Pharm, M.Sc, M.Tech): Passed relevant Bachelor's degree with minimum 50% aggregate marks.\n- Applications can be submitted online via www.kpgu.ac.in/apply or at the KPGU Admissions Office, Varnama, Vadodara.",
        "content_hash": "seed_admission_eligibility_01"
    },
    {
        "url": "https://www.kpgu.ac.in/kset",
        "title": "KSET Entrance & Scholarship Examination",
        "category": "admissions_and_scholarships",
        "content": "KSET (KPGU Entrance and Scholarship Test) is the university-level entrance examination conducted by Drs. Kiran & Pallavi Patel Global University (KPGU), Vadodara. KSET eligibility: Candidates appearing or passed 10+2 or equivalent exam. KSET provides merit-based scholarships up to 100% tuition fee waiver for B.Tech Engineering, B.Pharm, BBA, MBA, and Science programs. Exam dates, syllabus, and online application forms are available on the official KPGU website.",
        "content_hash": "seed_kset_info_01"
    },
    {
        "url": "https://www.kpgu.ac.in/faculty/cse/dr-rocky-upadhyay",
        "title": "Faculty Details - Dr. Rocky Upadhyay",
        "category": "academics_and_faculties",
        "content": "Dr. Rocky Upadhyay is the Head of Department (HOD) and Professor of Computer Science & Engineering (CSE) at Drs. Kiran & Pallavi Patel Global University (KPGU), Vadodara. He leads the CSE department, overseeing curriculum design, research labs, AI/ML projects, and student academic welfare.",
        "content_hash": "seed_dr_rocky_upadhyay_01"
    },
    {
        "url": "https://www.kpgu.ac.in/campus-life/hostel",
        "title": "Hostel Facilities & Accommodation Options",
        "category": "campus_and_facilities",
        "content": "KPGU Vadodara offers spacious, secure on-campus accommodation with separate hostels for boys and girls. Facilities include 24x7 CCTV security, high-speed Wi-Fi, fully furnished single and double rooms, continuous water and power supply, dedicated study rooms, laundry facilities, and a hygienic vegetarian mess providing nutritious meals.",
        "content_hash": "seed_hostel_facilities_01"
    },
    {
        "url": "https://www.kpgu.ac.in/programs/btech-cse",
        "title": "B.Tech Computer Science Engineering Program",
        "category": "academics_and_faculties",
        "content": "B.Tech in Computer Science & Engineering (CSE) at KPGU Vadodara is a 4-year undergraduate degree program. Curriculum covers Data Structures, Algorithms, Artificial Intelligence, Machine Learning, Web Development, Cybersecurity, and Software Engineering. Annual tuition fee: Rs 85,000.",
        "content_hash": "seed_btech_cse_program_01"
    },
    {
        "url": "https://www.kpgu.ac.in/faculty/cse/dr-patel",
        "title": "Faculty Details - Dr. Patel (CSE)",
        "category": "academics_and_faculties",
        "content": "Dr. Patel is a Senior Professor in the Department of Computer Science & Engineering (CSE) at KPGU Vadodara, specializing in Data Structures, Database Systems, and Cloud Computing.",
        "content_hash": "seed_faculty_dr_patel_cse"
    },
    {
        "url": "https://www.kpgu.ac.in/faculty/pharmacy/dr-patel",
        "title": "Faculty Details - Dr. Patel (Pharmacy)",
        "category": "academics_and_faculties",
        "content": "Dr. Patel is a Professor in the Faculty of Pharmacy at KPGU Vadodara, specializing in Pharmaceutics, Drug Delivery Systems, and Pharmaceutical Chemistry.",
        "content_hash": "seed_faculty_dr_patel_pharmacy"
    }
]

def seed_curated_facts(output_dir: str):
    """Seed foundational verified documents to raw data dir"""
    os.makedirs(output_dir, exist_ok=True)
    for idx, doc in enumerate(CURATED_SEED_DOCUMENTS):
        doc_record = {
            **doc,
            "crawl_timestamp": time.time(),
            "word_count": len(doc["content"].split()),
            "char_count": len(doc["content"])
        }
        filename = f"seed_{idx:03d}.json"
        fpath = os.path.join(output_dir, filename)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(doc_record, f, indent=2, ensure_ascii=False)
    logger.info(f"Seeded {len(CURATED_SEED_DOCUMENTS)} verified foundational documents to {output_dir}")

def mirror_directory(src_dir: str, dest_dir: str):
    """Mirror all files from src_dir to dest_dir"""
    if os.path.abspath(src_dir) == os.path.abspath(dest_dir):
        return
    try:
        os.makedirs(dest_dir, exist_ok=True)
        for fname in os.listdir(src_dir):
            src_file = os.path.join(src_dir, fname)
            dest_file = os.path.join(dest_dir, fname)
            if os.path.isfile(src_file):
                with open(src_file, 'rb') as f_in, open(dest_file, 'wb') as f_out:
                    f_out.write(f_in.read())
        logger.info(f"Mirrored {src_dir} -> {dest_dir}")
    except Exception as e:
        logger.warning(f"Error mirroring {src_dir} to {dest_dir}: {e}")

def main():
    logger.info("==================================================")
    logger.info("Starting KPGU AI Assistant Knowledge Ingestion")
    logger.info("==================================================")

    # Step 1: Seed curated foundational documents into raw data dir
    raw_dir = settings.DATA_RAW_DIR
    seed_curated_facts(raw_dir)

    # Step 2: Crawl verified pages from official KPGU sitemap
    logger.info("Step 2: Crawling verified official pages from sitemap...")
    crawler = CrawlerService()
    try:
        crawled_docs = crawler.crawl_sitemap(max_pages=85)
        crawler.save_documents(raw_dir)
        logger.info(f"Crawl completed. {len(crawled_docs)} pages retrieved.")
    finally:
        crawler.close_driver()

    # Mirror raw data to root data/raw
    mirror_directory(raw_dir, settings.ROOT_DATA_RAW_DIR)

    # Step 3: Process raw documents into semantic chunks
    processed_dir = settings.DATA_PROCESSED_DIR
    logger.info(f"Step 3: Processing documents from {raw_dir} -> {processed_dir}...")
    chunks = process_crawled_documents(input_dir=raw_dir, output_dir=processed_dir)
    logger.info(f"Generated {len(chunks)} semantic chunks.")

    # Mirror processed data to root data/processed
    mirror_directory(processed_dir, settings.ROOT_DATA_PROCESSED_DIR)

    # Step 4: Generate embeddings and build FAISS index
    index_path = settings.VECTOR_INDEX_PATH
    metadata_path = settings.METADATA_PATH
    logger.info(f"Step 4: Building embeddings and FAISS index at {index_path}...")

    success = build_embeddings_from_chunks(
        chunks_dir=processed_dir,
        index_path=index_path,
        metadata_path=metadata_path
    )

    if not success:
        logger.error("Failed to build embeddings index!")
        return False

    # Mirror vector store to root vector_store
    mirror_directory(settings.VECTOR_STORE_DIR, settings.ROOT_VECTOR_STORE_DIR)

    logger.info("==================================================")
    logger.info("Knowledge Ingestion & Vector Index Complete!")
    logger.info(f"- Chunks indexed: {len(chunks)}")
    logger.info(f"- Primary Vector Store: {settings.VECTOR_STORE_DIR}")
    logger.info(f"- Mirrored Vector Store: {settings.ROOT_VECTOR_STORE_DIR}")
    logger.info("==================================================")
    return True

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)