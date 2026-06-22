# FlowBOT — Customer Support Chat with Live Agent Takeover

A local customer support chat system where an AI handles questions first, and a real person can take over the conversation at any point.

---

## What It Does

- Customers open a chat widget on a demo website and ask questions.
- The local AI model reads the question and replies using information from a built-in knowledge base.
- The support team watches incoming chats on a private dashboard.
- When needed, an agent can join any conversation — from that point, the customer talks directly to a real person. The AI steps aside completely.
- The dashboard shows all conversations, lets agents review details, and can escalate tickets to GitHub Issues or Discord.

---

## Requirements

Before running anything, make sure you have:

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Ollama** running locally — download from [ollama.com](https://ollama.com/)
- *(Optional)* **Redis** — for persistent rate limiting. The app works without it but falls back to in-memory mode.

---

## Setup

**Step 1 — Run the setup script.** It checks and installs everything automatically:

```bash
python install_req.py
```

This will install Python packages, npm packages, and pull the AI model if it's not already downloaded. It also checks if Redis is available.

**Step 2 — Configure your secrets.** Copy the example env files and fill in the values:

```
backend/.env
frontend/.env
```

At minimum, set the same value for `ADMIN_API_KEY` in both files. This key protects the admin dashboard and agent routes. The default placeholder value is for local development only — change it before sharing the app with anyone.

**Step 3 — Start everything:**

```bash
python main.py
```

On Windows this opens three separate terminal windows. On Mac/Linux it runs them in the background. Press `Enter` or `Ctrl+C` to stop all three servers at once.

---

## Where to Open

| What | URL |
|---|---|
| Customer chat (demo website) | http://localhost:5174 |
| Agent dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |

---

## How to Take Over a Chat

1. Open the agent dashboard at `http://localhost:5173`.
2. Enter your name in the top-right corner.
3. Find a pending conversation in the list and click **Review**.
4. Click **Join Live Chat Takeover**.
5. A message appears in the customer's chat saying you've joined. The AI stops responding.
6. Type replies in the agent panel — the customer sees them in real time.

The customer side also has a **"Connect me to an agent"** quick-reply button. Pressing it sends an immediate alert to the dashboard.

---

## Folder Layout

```
main.py            — starts all 3 servers with one command
install_req.py     — installs and checks all dependencies
requirements.txt   — Python package list
backend/           — API server (FastAPI + SQLite + local AI model)
frontend/          — Dashboard and demo website (React)
knowledge_base/    — Text files the AI reads to answer questions
docs/              — Planning and reference documents
```

---

## Security Notes

- The admin dashboard and all agent routes require an `X-Admin-Key` header. Set this in both `.env` files before use.
- Neither `.env` file is committed to this repository — keep your secrets out of version control.
- CORS is locked to `localhost:5173` and `localhost:5174` by default. Change `ALLOWED_ORIGINS` in `backend/.env` if you host this elsewhere.
- Session IDs use the browser's built-in secure random generator.
- Rate limiting is on by default: 20 messages/minute from the chat widget, 60 requests/minute on agent endpoints.
