# FlowZint Support Workflow Assistant

The FlowZint Support Workflow Assistant is an artificial intelligence support intelligence layer that sits on top of customer conversations and translates them into structured operational decisions for support and engineering teams. Rather than acting as a standard FAQ chat bot, it structures customer inquiries, groups duplicate issues, and connects client interactions to downstream engineering pipelines.

## System Architecture

The application is structured as a monorepo consisting of:
- **Backend**: Python FastAPI application exposing REST endpoints, storing tickets in SQLite, utilizing a Chroma vector database for retrieval-augmented generation (RAG), and calling local Ollama (Qwen) instances.
- **Frontend**: React, Vite, and TypeScript SPA providing a visitor chat interface and an operations panel dashboard for administrators.
- **Knowledge Base**: Extracted documents from FlowZint's official web pages used to seed the vector database.

## Technologies Used

- **Frontend**: React 18, TypeScript, Vite, Lucide Icons, Custom CSS variables
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, Pydantic, Requests
- **Machine Learning & Storage**: Chroma DB (vector storage), Sentence-Transformers (local text embeddings), SQLite (relational storage), Ollama / Qwen (local LLM)

## Features

- **Structured Intent Routing**: Classifies messages into target paths (careers, internships, service enquiries, partnerships, contact info).
- **Knowledge-Grounded Answering (RAG)**: Retrieves chunks from indexed FlowZint web contents to ground support responses.
- **Smart Fallbacks**: Employs deterministic, regex-based fallback routing and pre-scripted domain answers if local LLM servers are offline.
- **Leader-based Similarity Clustering**: Computes text embeddings to group duplicate or related incoming requests in real-time.
- **Downstream Handoffs**: Automatically drafts GitHub issues and generates Discord webhook payloads, falling back to clean placeholder logging in development environments.

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Ollama (installed locally and running the `qwen2.5:1.5b` model)

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the SQLite database schema and seed default records:
   ```bash
   python init_app.py
   ```

4. Index the FlowZint website knowledge base into Chroma:
   ```bash
   python index_kb.py
   ```

5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The interactive API documentation is available at http://localhost:8000/docs.*

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install npm packages:
   ```bash
   npm install
   ```

3. Build and launch the Vite client:
   ```bash
   npm run dev
   ```
   *The application will be accessible at http://localhost:5173.*

## Project Structure

```text
d:\SupportBOT\
├── backend/
│   ├── app/
│   │   ├── config.py        # Settings and environment variables
│   │   ├── database.py      # Database models and session setup
│   │   ├── llm.py           # Qwen LLM client and heuristic fallback
│   │   ├── vector_store.py  # Chroma DB connection and chunking
│   │   ├── clustering.py    # Text similarity clustering logic
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── handoff.py       # Handoff integrations to GitHub/Discord
│   │   └── main.py          # FastAPI application entrypoint
│   ├── requirements.txt
│   ├── init_app.py
│   ├── index_kb.py
│   └── instance/
│       └── database.db      # Local SQLite database file
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWidget.tsx      # Floating chat interface
│   │   │   ├── AdminDashboard.tsx  # KPI tracking and queues
│   │   │   └── TicketDetail.tsx    # Handoff reviewer panel
│   │   ├── App.tsx
│   │   ├── index.css               # Styling system
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── knowledge_base/                 # Scraped FlowZint pages
└── README.md
```

## Change Log

### June 17, 2026

#### 1. RAG Knowledge Ingestion Ingestion Fixes
- **Timeout Protection**: Resolved `WinError 10060` connection timeouts during scraping by building an audit crawler (`backend/audit_scraper.py`) with exponential backoffs and retry mechanisms.
- **Dense Retrieval Enhancements**: Prepended the document's page title directly to every chunk in `backend/app/vector_store.py` to prevent semantic dilution.
- **Orphan Chunk Prevention**: Reconfigured the vector database build logic to delete and recreate the Chroma DB collection during indexing to avoid orphaned chunks persisting.
- **Playwright Verification**: Created `backend/validate_scrape.py` using Playwright to confirm exact text-matching (like the `₹1999` internship price) against dynamic browser viewports.

#### 2. Stateful Conversation History & Lead Escalation Filtering
- **Stateful Context Memory**: Added `session_id` to database schemas (`backend/app/database.py`, `backend/app/schemas.py`) and cached unique session IDs in the React front-end `ChatWidget.tsx`.
- **Coreference Resolution**: Integrated a Qwen query rewriter in `backend/app/llm.py` that parses conversation history to translate context-dependent messages (e.g. *"okay what do you offer in these?"*) into standalone search queries before retrieval.
- **Lead Filtering**: Created `resolved_by_ai` status for purely informational chats. Only logs tickets as `pending_review` (actionable leads) if they contain contact information, express negative sentiment, have high urgency/severity, or fail RAG grounding.
- **Dashboard Cleanup**: Set the `AdminDashboard.tsx` status queue to filter by `pending_review` by default, keeping the dashboard clean. Styled a custom `RESOLVED BY AI` status badge.

#### 3. Bug Report Classification & Empathetic Fallback Responses
- **Bug Detection Heuristics**: Expanded `rule_based_fallback_analysis` in `backend/app/llm.py` to identify error keywords and interface components. Handled typos (like "webstie") and added overrides for uppercase/exclamation complaints, force-escalating them as high-severity/frustrated tickets.
- **Empathetic Heuristic Responses**: Updated `generate_heuristic_response` to check for technical issues and apologize + log technical complaints immediately, avoiding generic marketing pitches for broken systems.
- **Ollama Timeout Resolution**: Increased the REST request timeout limit from 25 seconds to 60 seconds in `call_ollama`. Added `"keep_alive": "1h"` to the request payload so that the local Ollama instance keeps the Qwen model weights loaded in system RAM for 1 hour, preventing cold-start delays.

#### 4. Fuzzy Spelling Engine & Conversational Auto-Resolution
- **Fuzzy Spelling Corrector**: Built an edit-distance fuzzy spelling correction engine utilizing the standard Python library `difflib` and a comprehensive support dictionary covering errors, interface elements, intents, and resolution keywords. Misspelled words (e.g. `webstie` -> `website`, `intrnshp` -> `internship`, `crsh` -> `crash`, `flznt` -> `flowzint`) are corrected while preserving original casing.
- **Dynamic Auto-Resolution**: Refined the `/api/chat` route in `backend/app/main.py` to identify user resolutions (intent `resolved`). When a user resolves an issue, a database hook instantly updates all pending reviews in the same session to `resolved`, clearing the admin review queue in real-time.
- **Automated Verification**: Created `backend/test_fuzzy_spelling.py` to verify unit spelling corrections and end-to-end API session resolution behavior.

### June 20, 2026

#### 1. Performance & Scalability Enhancements
- **Clustering Embeddings Caching**: Added a persistent `embedding` column to the `Ticket` database model in `backend/app/database.py`, and refactored `clustering.py` to cache embeddings and lazily calculate them for historical records. This optimizes duplicate detection calculations from $O(N)$ to $O(1)$ model operations.
- **N+1 Database Queries Fix**: Replaced iterative counts in the `/api/clusters` endpoint in `backend/app/main.py` with an optimized single join query using SQLAlchemy `func.count` and `group_by`.
- **Consolidated Single-Pass LLM Call**: Combined RAG answer generation and structured ticket triage into a single unified prompt in `backend/app/llm.py`, saving an entire LLM call per request and cutting response times by 50% to 66%.
- **Coreference-Bypass Heuristics**: Bypasses the query rewriting LLM call for direct messages that contain no pronouns referring to history, saving another LLM call for the majority of initial chat requests.
- **Single-Pass Vector Embedding**: Pre-computes the query message vector once in `main.py` and reuses it for both document retrieval and clustering.

#### 2. RAG Pipeline Upgrades
- **Recursive Character Splitting Chunker**: Replaced the custom word count chunker in `vector_store.py` with a recursive character splitter (splitting sequentially on `\n\n`, `\n`, `. `, and ` `) to ensure document chunks retain structural and semantic cohesion.
- **Parameterization**: Exposed RAG settings (`RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`, `RAG_TOP_K`) in `backend/app/config.py` for easy hyperparameter tuning.

#### 3. Bug Corrections & Code Quality Hardening
- **Integration Handoff Failures**: Upgraded `handoff.py` and `main.py` to propagate GitHub/Discord API failure errors (like HTTP 401 Bad Credentials) back as HTTP 500 to the frontend instead of silently completing handoffs with mock URLs.
- **SSRF Crawler Hardening**: Refactored `backend/audit_scraper.py` to validate crawl domains strictly, preventing out-of-domain traversal.
- **CSS Loading Spin Animation**: Added `.animate-spin` classes in Vanilla CSS to `index.css` to fix the static dashboard refresh spinner.
- **Modernized API Methods**: Replaced deprecated Pydantic `.dict()` calls with `.model_dump()` and updated deprecated timezone-naive `datetime.utcnow()` fields.


