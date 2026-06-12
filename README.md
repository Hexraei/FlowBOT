# FlowZint Support Workflow Assistant

The FlowZint Support Workflow Assistant is an artificial intelligence support intelligence layer that sits on top of customer conversations and translates them into structured operational decisions for support and engineering teams. Rather than acting as a standard FAQ chat bot, it structures customer inquiries, groups duplicate issues, and connects client interactions to downstream engineering pipelines.

## System Architecture

The application is structured as a monorepo consisting of:
- **Backend**: Python FastAPI application exposing REST endpoints, storing tickets in SQLite, utilizing a Chroma vector database for retrieval-augmented generation (RAG), and calling local Ollama (Gemma) instances.
- **Frontend**: React, Vite, and TypeScript SPA providing a visitor chat interface and an operations panel dashboard for administrators.
- **Knowledge Base**: Extracted documents from FlowZint's official web pages used to seed the vector database.

## Technologies Used

- **Frontend**: React 18, TypeScript, Vite, Lucide Icons, Custom CSS variables
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, Pydantic, Requests
- **Machine Learning & Storage**: Chroma DB (vector storage), Sentence-Transformers (local text embeddings), SQLite (relational storage), Ollama / Gemma (local LLM)

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
- Ollama (installed locally and running the `gemma` model)

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
│   │   ├── llm.py           # Gemma LLM client and heuristic fallback
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
