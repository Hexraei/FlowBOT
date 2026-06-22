from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import settings
from app.database import get_db, init_db, Ticket, Cluster
from app.schemas import TicketRequest, TicketResponse, TicketUpdate, ClusterResponse
from app.llm import (
    analyze_ticket,
    generate_grounded_response,
    rewrite_query_with_history,
    needs_coreference_resolution,
    generate_consolidated_response
)
from app.clustering import find_or_create_cluster
from app.handoff import trigger_github_handoff, trigger_discord_handoff

app = FastAPI(
    title="FlowZint Support Workflow Assistant API",
    description="Backend API for AI support ticket analysis, RAG, and engineering handoffs.",
    version="1.0.0"
)

# Set up CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon/demo simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/api/chat", response_model=TicketResponse)
def handle_customer_message(req: TicketRequest, db: Session = Depends(get_db)):
    """
    Core customer chat endpoint. Analyzes the message, runs RAG with history context,
    saves the ticket state, runs duplicate clustering, and returns bot response.
    """
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # Pre-compute message embedding to reuse for clustering and optimize performance
        from app.vector_store import embedding_fn
        import json
        try:
            user_vector = embedding_fn([message])[0]
            user_vector_list = user_vector.tolist() if hasattr(user_vector, "tolist") else list(user_vector)
            message_embedding_json = json.dumps(user_vector_list)
        except Exception as e:
            print(f"Main API: Failed to pre-compute message embedding: {e}")
            message_embedding_json = None

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
        
        # 1 & 2. Run consolidated Triage classification and RAG Generation in a single LLM request
        bot_response, analysis = generate_consolidated_response(rewritten_query, history_list)
        
        # 3. Apply Actionable Ticket Escalation Filtering:
        # Only escalate if the query is high priority, includes contact details, or fails RAG.
        status = "resolved_by_ai"
        
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
        
        if is_high_priority or has_contact_info or is_fallback_triggered:
            status = "pending_review"
            
        # If user explicitly states the issue is resolved, auto-resolve all pending tickets in this session
        if analysis.get("intent") == "resolved" and req.session_id:
            status = "resolved"
            db.query(Ticket).filter(
                Ticket.session_id == req.session_id,
                Ticket.status == "pending_review"
            ).update({"status": "resolved"})
            db.commit()
            
        # 4. Create Ticket record
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
            embedding=message_embedding_json,
            status=status
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # 5. Perform duplicate grouping (Clustering)
        cluster_id = find_or_create_cluster(ticket, db)
        if cluster_id:
            ticket.cluster_id = cluster_id
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
        return ticket
    except Exception as e:
        db.rollback()
        print(f"Error handling customer message: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")

@app.get("/api/tickets", response_model=List[TicketResponse])
def get_all_tickets(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    intent: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves all support tickets with optional filtering."""
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if severity:
        query = query.filter(Ticket.severity == severity)
    if intent:
        query = query.filter(Ticket.intent == intent)
        
    # Order by newest first
    return query.order_by(Ticket.created_at.desc()).all()

@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_detail(ticket_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed information for a specific ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.put("/api/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket_review(ticket_id: str, payload: TicketUpdate, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

@app.post("/api/tickets/{ticket_id}/handoff")
def trigger_ticket_handoff(ticket_id: str, db: Session = Depends(get_db)):
    """Escalates a support ticket to engineering by generating GitHub issues and Discord alerts."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    try:
        # Trigger integrations
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
        print(f"Handoff integration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Handoff integration failed: {str(e)}")

@app.get("/api/clusters", response_model=List[ClusterResponse])
def get_all_clusters(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # Query clusters and their ticket counts in one join query to prevent N+1 query overhead
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
    # Order by ticket count desc
    return sorted(results, key=lambda x: x.ticket_count, reverse=True)

@app.get("/api/status")
def get_system_status():
    """Checks if the local Ollama instance is online and has the configured model available."""
    import requests
    from app.config import settings
    try:
        url = f"{settings.OLLAMA_HOST}/api/tags"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            configured_model = settings.OLLAMA_MODEL
            
            # Match configured model name (e.g. gemma or gemma:latest)
            model_installed = any(
                configured_model in name or name in configured_model
                for name in model_names
            )
            if model_installed:
                return {"status": "online"}
            else:
                print(f"Ollama is running, but configured model '{configured_model}' was not found in: {model_names}")
                return {"status": "offline"}
        return {"status": "offline"}
    except Exception as e:
        print(f"Status check failed: {e}")
        return {"status": "offline"}
