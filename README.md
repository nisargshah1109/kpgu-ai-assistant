# KPGU AI — Intelligent University Assistant

> **An AI-powered assistant for Drs. Kiran & Pallavi Patel Global University (KPGU), Vadodara.**  
> Built with RAG (Retrieval-Augmented Generation), FastAPI, React, FAISS, and Google Gemini.

---

## Problem Statement

Students, parents, and applicants seeking information about KPGU must navigate a large, multi-section website to find answers about admissions, programmes, fees, hostels, facilities, and campus life. This assistant provides a single conversational interface that retrieves accurate, source-grounded answers from official KPGU content — and responds *only* on university-related topics.

---

## Verified Features

| Feature | Status |
|---|---|
| React + Vite frontend (TypeScript, Tailwind CSS) | ✅ Verified |
| FastAPI backend with SQLite persistence | ✅ Verified |
| Hybrid RAG retrieval (FAISS vector + BM25 keyword) | ✅ Verified |
| Google Gemini LLM integration via `google-generativeai` | ✅ Verified |
| Local fallback answer when Gemini is unavailable | ✅ Verified |
| Sentence-Transformers embeddings (`all-MiniLM-L6-v2`) | ✅ Verified |
| Conversation history (SQLite, persistent across sessions) | ✅ Verified |
| Context-aware follow-up question resolution | ✅ Verified |
| Topic-scope filtering (prevents cross-topic answer pollution) | ✅ Verified |
| Entity-first retrieval boost (named entity matching) | ✅ Verified |
| Intent detection (admissions, hostel, placement, benefits, etc.) | ✅ Verified |
| Ambiguity detection and clarification prompting | ✅ Verified |
| PDF export of conversation (via ReportLab) | ✅ Verified |
| Hindi / Gujarati query handling (passed to Gemini in-context) | ✅ Verified |
| University website crawler (BeautifulSoup, Selenium) | ✅ Verified |
| Pre-built knowledge base (919 processed chunks, FAISS index) | ✅ Verified |

**Note:** Multilingual responses depend on whether context chunks contain translated content. The system instructs Gemini to respond in the user's language using only the retrieved KPGU context.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, TypeScript, Tailwind CSS 4, React Router 7 |
| Backend | Python 3.9+, FastAPI, Uvicorn |
| Database | SQLite via SQLAlchemy |
| Vector Store | FAISS (`faiss-cpu`), Sentence-Transformers |
| Embedding Model | `all-MiniLM-L6-v2` (384-dimensional vectors) |
| LLM | Google Gemini (`gemini-2.0-flash`) via `google-generativeai` |
| PDF Generation | ReportLab |
| Crawler | BeautifulSoup4, Requests, Selenium, WebDriver Manager |

---

## Architecture & Request Flow

```
KPGU Website
    │
    ▼
Crawler Service (BeautifulSoup / Selenium)
    │ raw JSON documents
    ▼
Text Processor (clean, normalize, semantic chunk)
    │ chunk_XXXX.json files
    ▼
Embedding Service (Sentence-Transformers → FAISS index)
    │ faiss_index.bin + metadata.json
    ▼
──────────────────────────────────────────────────
User Question (React Chat UI)
    │
    ▼
FastAPI /api/chat
    │
    ├─ Query Gater          (block non-KPGU queries)
    ├─ Intent Detector      (admissions / hostel / placement / benefits …)
    ├─ Entity Extractor     (named person, programme, facility)
    ├─ Ambiguity Handler    (follow-up context resolution)
    │
    ▼
Hybrid Retriever (FAISS vector score × 0.6 + BM25 × 0.4 + entity boost)
    │
    ├─ Entity Relevance Gate  (validate retrieved chunks contain entity)
    ├─ Topic Context Filter   (strip cross-topic pollution)
    │
    ▼
GeminiProvider (system prompt + history + context → answer)
    │
    ▼
Answer saved to SQLite → returned to React UI
```

---

## Project Structure

```
KPGU-AI-Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── Models.py            # SQLAlchemy ORM models
│   │   ├── db.py                # Database engine and session
│   │   ├── config.py            # Pydantic settings (reads .env)
│   │   ├── routers/
│   │   │   ├── chat.py          # POST /api/chat
│   │   │   ├── conversations.py # CRUD /api/conversations
│   │   │   ├── knowledge.py     # /api/knowledge/* (crawl, upload, rebuild, status)
│   │   │   └── health.py        # GET /api/health
│   │   └── services/
│   │       ├── chat_service.py         # Main RAG orchestration pipeline
│   │       ├── llm_provider.py         # Gemini provider (abstract + concrete)
│   │       ├── hybrid_retriever.py     # FAISS + BM25 hybrid retrieval
│   │       ├── embedding_service.py    # Sentence-Transformers + FAISS index
│   │       ├── crawler_service.py      # KPGU website crawler
│   │       ├── text_processor.py       # Text cleaning and semantic chunking
│   │       ├── pdf_service.py          # ReportLab PDF export
│   │       ├── intent_detector.py      # Query intent classification
│   │       ├── entity_extractor.py     # Named entity extraction
│   │       ├── entity_relevance_gate.py# Validate entity in retrieved chunks
│   │       ├── ambiguity_handler.py    # Follow-up context + ambiguity detection
│   │       ├── topic_context_filter.py # Topic-level context filtering
│   │       └── query_gater.py          # Pre-LLM KPGU topic scope gate
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment variable template (safe placeholder)
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx         # Main chat interface
│   │   │   ├── SourcesPage.tsx      # Indexed knowledge sources view
│   │   │   ├── UpdateDataPage.tsx   # Admin panel: crawl / rebuild KB
│   │   │   └── AboutPage.tsx        # About the assistant
│   │   ├── App.tsx              # React Router setup
│   │   ├── main.tsx             # React entry point
│   │   ├── App.css              # Component styles
│   │   └── index.css            # Tailwind base
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts           # Dev server port 5175, proxy /api → :8002
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── postcss.config.js
├── data/
│   ├── raw/                     # Crawled HTML/document JSON (64 source docs)
│   └── processed/               # Semantic chunks (919 chunk JSON files)
├── vector_store/
│   └── metadata.json            # FAISS metadata (index binary excluded from repo)
├── scripts/
│   ├── build_knowledge_base.py  # Full pipeline: crawl → process → embed
│   ├── run_tests.py             # Test runner helper
│   └── generate_pptx.py        # Presentation generator utility
├── tests/
│   ├── test_api.py              # FastAPI endpoint tests (6 tests)
│   └── test_rag.py              # RAG pipeline unit tests (3 tests)
└── README.md
```

---

## Prerequisites

- **Python** 3.9 or newer
- **Node.js** 18 or newer
- **Git**
- A **Google Gemini API key** — obtain free from [Google AI Studio](https://aistudio.google.com/)

> **Windows users:** `faiss-cpu` requires the Microsoft Visual C++ Redistributable.  
> Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/nisargshah1109/kpgu-ai-assistant.git
cd kpgu-ai-assistant
```

### 2. Backend setup

```powershell
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create your .env file from the template
Copy-Item .env.example .env
```

Edit `backend/.env` and add your real Gemini API key:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 3. Frontend setup

```powershell
cd ..\frontend
npm install
```

---

## Running the Application

### Option A — Use the pre-built knowledge base

The repository includes pre-processed knowledge chunks (`data/processed/`) and vector store metadata (`vector_store/metadata.json`). You only need to rebuild the FAISS binary index:

```powershell
# From project root — activate venv first
cd backend
.\venv\Scripts\Activate.ps1
python -c "
from app.services.embedding_service import build_embeddings_from_chunks
build_embeddings_from_chunks()
print('FAISS index rebuilt successfully.')
"
```

### Option B — Full crawl and rebuild (optional)

```powershell
# From project root
cd backend
.\venv\Scripts\Activate.ps1
python ..\scripts\build_knowledge_base.py
```

This will crawl the KPGU website, re-process all content, and rebuild the FAISS index from scratch. Requires internet access and takes several minutes.

### Start the backend

```powershell
# From the backend directory (venv must be active)
uvicorn app.main:app --reload --port 8002
```

Backend available at:
- API: http://localhost:8002
- Swagger docs: http://localhost:8002/docs

### Start the frontend

```powershell
# From the frontend directory
npm run dev
```

Frontend available at: **http://localhost:5175**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (DB, Gemini, vector store) |
| `POST` | `/api/chat` | Send message, get RAG-generated answer |
| `POST` | `/api/conversations` | Create new conversation |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get conversation with messages |
| `PUT` | `/api/conversations/{id}` | Update conversation title |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |
| `POST` | `/api/conversations/{id}/messages` | Add message to conversation |
| `GET` | `/api/conversations/{id}/messages` | List conversation messages |
| `POST` | `/api/knowledge/crawl` | Trigger website crawl (background) |
| `POST` | `/api/knowledge/upload` | Upload custom text document |
| `POST` | `/api/knowledge/rebuild` | Rebuild knowledge base (background) |
| `GET` | `/api/knowledge/status` | Knowledge base status |
| `GET` | `/api/sources` | List indexed knowledge sources |

---

## Environment Variables

Create `backend/.env`:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

All other settings have sane defaults in `backend/app/config.py`:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_MODEL_NAME` | `gemini-2.0-flash` | Gemini model to use |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence-Transformers model |
| `RELEVANCE_THRESHOLD` | `0.20` | Minimum hybrid score to include a chunk |
| `MAX_CONTEXT_CHUNKS` | `4` | Maximum chunks sent to Gemini |
| `MAX_HISTORY_MESSAGES` | `6` | Conversation history window |
| `MAX_OUTPUT_TOKENS` | `512` | Gemini max output token limit |

---

## Running Tests

```powershell
# From project root — activate backend venv first
cd backend
.\venv\Scripts\Activate.ps1
pip install pytest pytest-asyncio

cd ..
python -m pytest tests/ -v
```

**Verified test results** (Python 3.13, Windows):

| Test | Result |
|---|---|
| `test_root_endpoint` | ✅ PASSED |
| `test_health_endpoint` | ✅ PASSED |
| `test_conversations_crud` | ✅ PASSED |
| `test_knowledge_status_endpoint` | ✅ PASSED |
| `test_sources_endpoint` | ✅ PASSED |
| `test_upload_document_endpoint` | ✅ PASSED |
| `test_text_processor_cleaning` | ✅ PASSED |
| `test_semantic_chunking` | ✅ PASSED |
| `test_embedding_generation_and_faiss` | ⚠️ Environment-specific (regex DLL on Windows) |

---

## Known Limitations

1. **FAISS index not in repository** — The `faiss_index.bin` binary (1.4 MB) is excluded. Run the rebuild step above to regenerate it.
2. **FAISS on Windows** — Requires the Visual C++ Redistributable. The backend gracefully handles missing FAISS by falling back to BM25-only retrieval.
3. **`google-generativeai` deprecation warning** — The package displays a FutureWarning about migration to `google.genai`. The library remains functional. Migration is planned.
4. **CORS** — Currently allows all origins (`allow_origins=["*"]`). Restrict to your frontend domain for production use.
5. **No authentication** — The admin panel (crawl, rebuild) is unprotected. Add auth before exposing publicly.
6. **Multilingual responses** — Hindi/Gujarati responses depend on Gemini understanding the language instruction. Context chunks are in English only.

---

## Security Guidance

- **Never commit your `backend/.env`** file. It is excluded by `.gitignore`.
- The repository contains only `backend/.env.example` with a placeholder value.
- Keep your Gemini API key private. Rotate it immediately if accidentally exposed.
- The SQLite database (`kpgu_assistant.db`) contains conversation history and is excluded from the repository.
- Add rate limiting (e.g., `slowapi`) before deploying this API publicly.

---

## Credits

Built by **Nisarg Shah** and **Harsh Shah** — KPGU Students.

This project is for educational and demonstrative purposes. Please respect the [KPGU website's terms of service](https://www.kpgu.ac.in/) when using the crawler.

**Technologies used:**
- [FastAPI](https://fastapi.tiangolo.com/) · [React](https://reactjs.org/) · [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/) · [Google Gemini](https://ai.google.dev/)
- [Sentence Transformers](https://www.sbert.net/) · [FAISS](https://github.com/facebookresearch/faiss)
- [ReportLab](https://www.reportlab.com/) · [SQLAlchemy](https://www.sqlalchemy.org/)