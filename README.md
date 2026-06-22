# FlowZint Support BOT - Dual-Window Live Chat Takeover System

Welcome to the FlowZint Support BOT project! This application provides a dual-window interface demonstrating a state-of-the-art customer service workflow, combining local RAG-based AI concierge support with a live human takeover dashboard.

---

## 🚀 Quick Start Instructions

This project includes automated setup and launcher scripts for a seamless developer experience.

### Step 1: Install Dependencies
Open a terminal in the project root folder and run the setup script:
```bash
python install_req.py
```
This script will:
* Check for and install all required **Python packages** (FastAPI, SQLAlchemy, ChromaDB, etc.).
* Verify if **Node.js** and **npm** are installed.
* Automatically install **npm packages** in the frontend folder.
* Verify if **Ollama** is running locally and automatically pull the `qwen2.5:1.5b` model if it is missing.

### Step 2: Start the Servers
Once the setup is successful, launch all three servers simultaneously with a single command:
```bash
python main.py
```
* **On Windows**: This opens three separate command prompt terminal windows (one for each server) so you can easily view log outputs and debug in real-time.
* **On Mac/Linux**: This spins them up cleanly as background processes.
* **Stopping the App**: Simply press `Enter` or `Ctrl+C` in the main launcher terminal, and it will cleanly terminate all running servers.

---

## 🌐 Server Port Layout

The application runs on three independent local ports:
1. **FastAPI Backend**: `http://localhost:8000` (API services, RAG query pipelines, and database logs).
2. **Operations Dashboard**: [http://localhost:5173](http://localhost:5173) (Internal admin panel for reviewing support tickets, configuring agent profiles, and joining live chats).
3. **Customer Website Mockup**: [http://localhost:5174](http://localhost:5174) (FlowZint dummy landing page displaying scraped service, internship, and career facts, complete with an embedded AI customer support chat widget).

---

## 💡 How It Works

1. **AI Chat Mode**: When a visitor opens the chat widget at `http://localhost:5174`, they converse with the local `qwen2.5:1.5b` model. The AI answers queries grounded on FlowZint crawled facts using a single-pass consolidated RAG pipeline.
2. **Intent & Severity Triaging**: The backend automatically parses the messages, categorizing intents (e.g., business inquiries, careers, internships) and sentiments in real-time. If a ticket meets high-priority metrics (e.g., negative sentiment or explicit business inquiry), it is flagged for review.
3. **Human Request Shortcut**: A quick-suggestion button **"Connect me to an agent"** is provided. Selecting it triggers a heuristic override that alerts the user: *"Please wait while we connect you to a real agent..."* and routes the ticket to the admin dashboard.
4. **Live Human Takeover**:
   * Open the Operations Dashboard at `http://localhost:5173` and input your **Agent Name** in the top-right navbar.
   * Locate the pending ticket in the list (refreshes automatically every **5 seconds**).
   * Click **Review** to open the details slide-out drawer, then click **Join Live Chat Takeover**.
   * A popup system message is sent to the customer widget saying `"[Agent Name] has joined the chat."` and the bot is put into bypass mode.
   * From this point on, two-way communication between you and the customer is direct, bypassing the LLM completely.

---

## 📁 Repository Structure

* `main.py` - Single-entry launcher script to run all 3 servers.
* `install_req.py` - Pre-requisites installation and verification script.
* `requirements.txt` - Python backend package requirements.
* `backend/` - FastAPI backend application code.
* `frontend/` - React/Vite web interface containing components for the dashboard, landing page, and chat bubble widget.
* `knowledge_base/` - Text documents of crawled FlowZint facts used for RAG grounding.
* `docs/` - Product Requirements Documents (PRD) and evaluation reports.
