# Project Context and Future Prospects

This document serves as a comprehensive reference guide for the **FlowZint Support Workflow Assistant** (or **FlowZint AI Concierge**). It integrates the product requirements, implementation designs, technical architectural stack, and the future extension roadmap to guide developers through ongoing maintenance and feature scaling.

---

## 1. Project Background and Objective

### Overview
FlowZint positions itself as a company building enterprise digital infrastructure, SaaS systems, AI automation, and scalable operations. Because their business paths are highly structured around service inquiries, partnerships, and hiring workflows, standard FAQ chatbots are insufficient. 

### Core Concept
The product is a **support intelligence layer** that acts as a bridge between three target user groups:
1. **Customer / Visitor**: Gets direct, grounded answers from FlowZint's official documentation.
2. **Support Team**: Receives automated, structured ticket information, enabling quick manual triage and reviews.
3. **Engineering Team**: Obtains actionable incident reports and prioritization alerts.

Instead of just answering queries, the assistant analyzes the intent, generates grounded answers, groups duplicate issues, and connects client interactions directly to downstream team queues.

---

## 2. Technical Implementation Architecture

The application is engineered as a decoupled monorepo structure designed for zero-license cost, offline capability, and low-setup friction:

### Technical Stack
- **Frontend**: React (with Vite & TypeScript). Built using custom CSS variables,Outfit/Inter typography, deep slate/blue radial gradients, hover micro-animations, and glassmorphic panels.
- **Backend**: Python FastAPI web server.
- **Relational Storage**: SQLite (via SQLAlchemy) for ticket state tracking, metadata, and cluster management.
- **Vector Database**: Chroma DB persistence for local semantic search indexing.
- **Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`) for local chunk embedding and cosine similarity queries.
- **LLM Selection**: Local Ollama execution running the `gemma` model.

### Database Schema

1. **`tickets` Table**:
   - `id` (UUID, primary key)
   - `created_at` (Timestamp)
   - `user_message` (Text)
   - `bot_response` (Text)
   - `intent` (String: `business_enquiry`, `partnership`, `careers`, `internship_programs`, `service_inquiry`, `other`)
   - `summary` (Text)
   - `severity` (String: `high`, `medium`, `low`)
   - `sentiment` (String: `positive`, `neutral`, `negative`, `frustrated`)
   - `probable_component` (String)
   - `urgency` (Integer: 1 to 5)
   - `contact_details` (String)
   - `confidence_score` (Float: 0.0 to 1.0)
   - `cluster_id` (UUID, ForeignKey to `clusters`)
   - `status` (String: `pending_review`, `handoff_completed`, `resolved`, `ignored`)
   - `github_issue_url` (String, Nullable)
   - `discord_notified` (Boolean)

2. **`clusters` Table**:
   - `id` (UUID, primary key)
   - `name` (String)
   - `description` (Text)
   - `created_at` (Timestamp)

---

## 3. Core Functional Logic

### RAG & Fallback Responder
1. The backend receives a visitor message and queries the Chroma vector database.
2. The vector DB searches 22 pre-populated FlowZint crawled plain-text pages.
3. If the best cosine similarity score exceeds `0.35`, the content chunks are injected into the LLM context to formulate a grounded answer.
4. If similarity is below `0.35`, or if the LLM states it does not know the answer, the system triggers a **fallback flow**:
   - Classifies the message using keywords/regex.
   - Returns a structured pre-scripted response matching the intent (e.g. Careers, Business, Partnerships) to provide helpful info even when offline.

### Duplicate Clustering
- Uses sentence embeddings to convert user queries into vectors.
- Computes cosine similarity against all historical tickets.
- If similarity exceeds `0.80`, it groups the new ticket into the matched cluster. Otherwise, the ticket remains standalone until further matches occur, in which case a new cluster is created.

### Downstream Handoff
- Supports manual reviews by administrators.
- Allows staff to review structured fields and click a button to trigger escalations:
  - **GitHub Issues**: Submits a formatted markdown issue card to the target repo.
  - **Discord Webhook**: Sends embed notifications indicating ticket properties and severity colors.
  - Defaults to **placeholder mode** (stdout logging) in the absence of credentials, ensuring setup-free testing.

---

## 4. Future Prospects and Feature Roadmap

### Phase 1: Foundational Enhancements
- **Dynamic Crawler**: Implement a periodic crawler script using BeautifulSoup or Scrapy to update the local `knowledge_base` folder automatically when the FlowZint website updates.
- **RAG Scoring Calibration**: Implement a user feedback loop (+1 / -1 thumbs up buttons in the ChatWidget) to continuously optimize vector DB similarity thresholds.

### Phase 2: Workflow Automation
- **Lead Generation Forms**: When `business_enquiry` is detected, dynamically display a questionnaire form in the chat widget requesting budget, timeline, and scope, feeding it directly into the sales queue.
- **Career Routing & Resume Parsing**: Add resume upload capabilities to the chat widget when intent maps to `careers`, parsing skills and matching them to open internship opportunities.

### Phase 3: Analytics and Operations Panel
- **Telemetry Charts**: Implement charts in the dashboard showing volume over time, average sentiment trends, and intent distributions.
- **Recommended Next Actions**: Train a classifier or rule-engine to suggest actions (e.g. "Recommend scheduling a meeting on Google Calendar" or "Send standard partnership NDA").

### Phase 4: Autonomous Operations (Stretch Goals)
- **Automatic Email Drafts**: Use Gemma to generate draft email replies for the support team based on RAG context.
- **Lead Scoring Engine**: Score business inquiries based on contact detail authenticity, urgency, and project descriptions to prioritize high-value client acquisitions.

---

## 5. Required Context for Development

### Environment Setup
Create a `.env` file in the root backend directory to configure real external endpoints:
```ini
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma
DATABASE_URL=sqlite:///instance/database.db
CHROMA_PERSIST_DIR=instance/chroma_db
KNOWLEDGE_BASE_DIR=../knowledge_base
GITHUB_TOKEN=your_personal_access_token
GITHUB_REPO=Hexraei/FlowBOT
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

### Verification Scripts
To test and debug independent subsystems, execute the following CLI tools from the repository root:
- Initialize DB: `python backend/init_app.py`
- Populate and Test Chroma: `python backend/index_kb.py`
- Test Fallback & Gemma Analysis: `python backend/test_llm.py`
- Test Grounded QA Responses: `python backend/test_rag.py`
- Test Cosine Clustering: `python backend/test_clustering.py`
- Test API client: `python backend/test_api.py`
