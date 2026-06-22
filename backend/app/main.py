import logging
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import get_db, init_db, Ticket, Cluster
from app.schemas import (
    TicketRequest, TicketResponse, PublicTicketResponse, TicketUpdate,
    ClusterResponse, TakeoverRequest, AgentMessageRequest
)
from app.auth import verify_admin_key
from app.llm import (
    analyze_ticket,
    generate_grounded_response,
    rewrite_query_with_history,
    needs_coreference_resolution,
    generate_consolidated_response
)
from app.clustering import find_or_create_cluster
from app.handoff import trigger_github_handoff, trigger_discord_handoff
from app.sse import stream_session_messages, stream_admin_tickets

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiter (Redis-backed with in-memory fallback)
# ---------------------------------------------------------------------------
try:
    limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
    logger.info(f"Rate limiter initialized with Redis backend: {settings.REDIS_URL}")
except Exception as e:
    logger.warning(f"Redis unavailable ({e}). Falling back to in-memory rate limiting.")
    limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FlowZint Support Workflow Assistant API",
    description="Backend API for AI support ticket analysis, RAG, and engineering handoffs.",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — explicit origins only, no wildcard
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    if not settings.ADMIN_API_KEY:
        logger.critical(
            "SECURITY WARNING: ADMIN_API_KEY is not set in .env. "
            "All admin endpoints are exposed. Set ADMIN_API_KEY before going live."
        )

# ---------------------------------------------------------------------------
# Public: Customer Chat Endpoint
# ---------------------------------------------------------------------------
@app.post("/api/chat", response_model=PublicTicketResponse)
@limiter.limit("20/minute")
def handle_customer_message(
    request: Request,
    req: TicketRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Core customer chat endpoint. Analyzes the message, runs RAG with history context,
    saves the ticket state, runs duplicate clustering in background, and returns bot response.
    """
    message = req.message.strip()

    try:
        # Check if the session is currently taken over by an agent
        is_taken_over = False
        agent_name = None
        if req.session_id:
            last_takeover_ticket = (
                db.query(Ticket)
                .filter(Ticket.session_id == req.session_id)
                .filter(Ticket.is_taken_over == True)
                .first()
            )
            if last_takeover_ticket:
                is_taken_over = True
                agent_name = last_takeover_ticket.agent_name

        if is_taken_over:
            # Bypass LLM and RAG. Simply save user message and return it.
            ticket = Ticket(
                session_id=req.session_id,
                user_message=message,
                bot_response=None,
                intent="live_chat",
                summary="Active human chat takeover",
                severity="low",
                sentiment="neutral",
                probable_component="Live Chat",
                urgency=1,
                status="resolved",
                is_taken_over=True,
                agent_name=agent_name,
                sender_type="user"
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return ticket

        # Direct heuristic takeover trigger for the exact suggestion text
        if message.lower() == "connect me to an agent":
            ticket = Ticket(
                session_id=req.session_id,
                user_message=message,
                bot_response="Please wait while we connect you to a real agent. Our support team has been notified and will join this chat shortly.",
                intent="human_takeover",
                summary="Customer clicked Connect me to an Agent",
                severity="medium",
                sentiment="neutral",
                probable_component="Live Chat",
                urgency=4,
                status="pending_review",
                is_taken_over=False,
                agent_name=None,
                sender_type="user"
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            return ticket

        # Pre-compute message embedding to reuse for clustering and optimize performance
        from app.vector_store import embedding_fn
        import json
        message_embedding_json = None
        try:
            user_vector = embedding_fn([message])[0]
            user_vector_list = user_vector.tolist() if hasattr(user_vector, "tolist") else list(user_vector)
            message_embedding_json = json.dumps(user_vector_list)
        except Exception as e:
            logger.warning(f"Failed to pre-compute message embedding: {e}")

        # Fetch conversation history if session_id is provided
        history_list = []
        if req.session_id:
            past_tickets = (
                db.query(Ticket)
                .filter(Ticket.session_id == req.session_id)
                .order_by(Ticket.created_at.asc())
                .limit(6)
                .all()
            )
            for t in past_tickets:
                history_list.append({"sender": "user", "text": t.user_message})
                if t.bot_response:
                    history_list.append({"sender": "assistant", "text": t.bot_response})

        # Rewrite query to resolve coreferences if history exists and contains pronouns
        if history_list and needs_coreference_resolution(message):
            rewritten_query = rewrite_query_with_history(message, history_list)
        else:
            rewritten_query = message

        # Run consolidated Triage classification and RAG Generation in a single LLM request
        bot_response, analysis = generate_consolidated_response(rewritten_query, history_list)

        # Apply Actionable Ticket Escalation Filtering
        ticket_status = "resolved_by_ai"

        is_high_priority = (
            analysis.get("severity") in ["medium", "high"] or
            analysis.get("urgency", 3) >= 4 or
            analysis.get("sentiment") in ["negative", "frustrated"]
        )
        has_contact_info = bool(analysis.get("contact_details"))
        is_fallback_triggered = (
            "routed it to the FlowZint support team" in bot_response or
            "operations lead will reach out" in bot_response
        )

        if is_high_priority or has_contact_info or is_fallback_triggered or analysis.get("intent") == "human_takeover":
            ticket_status = "pending_review"

        if analysis.get("intent") == "human_takeover":
            bot_response = "Please wait while we connect you to a real agent. Our support team has been notified and will join this chat shortly."

        # If user explicitly states the issue is resolved, auto-resolve pending tickets in session
        if analysis.get("intent") == "resolved" and req.session_id:
            ticket_status = "resolved"
            db.query(Ticket).filter(
                Ticket.session_id == req.session_id,
                Ticket.status == "pending_review"
            ).update({"status": "resolved"})
            db.commit()

        # Create Ticket record
        ticket = Ticket(
            session_id=req.session_id,
            user_message=message,
            bot_response=bot_response,
            intent=analysis.get("intent"),
            summary=analysis.get("summary"),
            severity=analysis.get("severity"),
            sentiment=analysis.get("sentiment"),
            probable_component=analysis.get("probable_component"),
            urgency=analysis.get("urgency"),
            contact_details=analysis.get("contact_details"),
            confidence_score=analysis.get("confidence_score"),
            status=ticket_status,
            embedding=message_embedding_json,
            is_taken_over=False,
            sender_type="user"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        # Run clustering in background — does not block the HTTP response
        background_tasks.add_task(find_or_create_cluster, ticket.id, ticket.user_message, message_embedding_json)

        return ticket

    except Exception as e:
        db.rollback()
        logger.exception(f"Error handling customer message: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")


# ---------------------------------------------------------------------------
# Admin: Ticket Management (auth-protected)
# ---------------------------------------------------------------------------

@app.get("/api/tickets", response_model=List[TicketResponse])
def get_all_tickets(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    intent: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """Retrieves support tickets with optional filtering and pagination."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 200:
        page_size = 50

    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if severity:
        query = query.filter(Ticket.severity == severity)
    if intent:
        query = query.filter(Ticket.intent == intent)

    return query.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()


@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_detail(
    ticket_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """Retrieves detailed information for a specific ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.put("/api/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket_review(
    ticket_id: str,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """Allows support staff to manually edit ticket fields (review correction)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)

    try:
        db.commit()
        db.refresh(ticket)
        return ticket
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating ticket.")


@app.post("/api/tickets/{ticket_id}/handoff")
def trigger_ticket_handoff(
    ticket_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """Escalates a support ticket to engineering via GitHub issues and Discord alerts."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        github_url = trigger_github_handoff(ticket_id, db)
        if settings.GITHUB_TOKEN and not github_url:
            raise Exception("Failed to obtain GitHub issue URL.")

        discord_success = trigger_discord_handoff(ticket_id, db)
        if settings.DISCORD_WEBHOOK_URL and not discord_success:
            raise Exception("Failed to send Discord alert notification.")

        db.refresh(ticket)
        return {
            "status": "handoff_processed",
            "github_issue_url": ticket.github_issue_url,
            "discord_notified": ticket.discord_notified,
            "ticket_status": ticket.status
        }
    except Exception as e:
        db.rollback()
        logger.exception(f"Handoff integration failed for ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Handoff integration failed: {str(e)}")


@app.get("/api/clusters", response_model=List[ClusterResponse])
def get_all_clusters(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    from sqlalchemy import func
    cluster_counts = (
        db.query(Cluster, func.count(Ticket.id).label("ticket_count"))
        .outerjoin(Ticket, Ticket.cluster_id == Cluster.id)
        .group_by(Cluster.id)
        .all()
    )
    results = []
    for c, count in cluster_counts:
        results.append(
            ClusterResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                created_at=c.created_at,
                ticket_count=count
            )
        )
    return sorted(results, key=lambda x: x.ticket_count, reverse=True)


# ---------------------------------------------------------------------------
# Public: System Status
# ---------------------------------------------------------------------------

@app.get("/api/status")
def get_system_status():
    """Checks if the local Ollama instance is online and has the configured model available."""
    import requests as req_lib
    try:
        url = f"{settings.OLLAMA_HOST}/api/tags"
        response = req_lib.get(url, timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            configured_model = settings.OLLAMA_MODEL
            model_installed = any(
                configured_model in name or name in configured_model
                for name in model_names
            )
            return {"status": "online" if model_installed else "offline"}
        return {"status": "offline"}
    except Exception as e:
        logger.warning(f"Status check failed: {e}")
        return {"status": "offline"}


# ---------------------------------------------------------------------------
# Agent: Live Takeover Routes (auth-protected)
# ---------------------------------------------------------------------------

@app.post("/api/tickets/session/{session_id}/takeover")
@limiter.limit("10/minute")
def takeover_session(
    request: Request,
    session_id: str,
    req: TakeoverRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    tickets = db.query(Ticket).filter(Ticket.session_id == session_id).all()
    for t in tickets:
        t.is_taken_over = True
        t.agent_name = req.agent_name
        t.status = "resolved"

    system_ticket = Ticket(
        session_id=session_id,
        user_message=f"{req.agent_name} has joined the chat.",
        bot_response=None,
        intent="system_event",
        summary="System takeover notification",
        status="resolved",
        is_taken_over=True,
        agent_name=req.agent_name,
        sender_type="system"
    )
    db.add(system_ticket)
    db.commit()
    return {"status": "success", "agent_name": req.agent_name}


@app.post("/api/tickets/session/{session_id}/message", response_model=TicketResponse)
@limiter.limit("60/minute")
def send_agent_message(
    request: Request,
    session_id: str,
    req: AgentMessageRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    agent_ticket = Ticket(
        session_id=session_id,
        user_message=req.message,
        bot_response=None,
        intent="agent_message",
        summary="Response from support agent",
        status="resolved",
        is_taken_over=True,
        agent_name=req.agent_name,
        sender_type="agent"
    )
    db.add(agent_ticket)
    db.commit()
    db.refresh(agent_ticket)
    return agent_ticket


@app.get("/api/tickets/session/{session_id}/messages", response_model=List[PublicTicketResponse])
@limiter.limit("60/minute")
def get_session_messages(
    request: Request,
    session_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Public: returns session messages for the customer chat widget (no auth, PII-stripped)."""
    if limit < 1 or limit > 500:
        limit = 100
    messages = (
        db.query(Ticket)
        .filter(Ticket.session_id == session_id)
        .order_by(Ticket.created_at.asc())
        .limit(limit)
        .all()
    )
    return messages


# ---------------------------------------------------------------------------
# SSE: Real-time Streaming Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/stream/session/{session_id}")
async def sse_session_stream(session_id: str):
    """
    SSE stream for a customer chat session.
    Replaces polling in ChatWidget.tsx and TakeoverPanel.tsx.
    Client connects once; new messages are pushed as they arrive.
    """
    return StreamingResponse(
        stream_session_messages(session_id, get_db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disables Nginx buffering for SSE
        }
    )


@app.get("/api/stream/tickets")
async def sse_admin_tickets_stream(
    status: Optional[str] = "pending_review",
    _: str = Depends(verify_admin_key)
):
    """
    SSE stream for the admin dashboard ticket list.
    Replaces the 5s polling interval in AdminDashboard.tsx.
    Requires X-Admin-Key header.
    """
    return StreamingResponse(
        stream_admin_tickets(get_db, status_filter=status or "pending_review"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
