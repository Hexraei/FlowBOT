from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import settings
from app.database import get_db, init_db, Ticket, Cluster
from app.schemas import TicketRequest, TicketResponse, TicketUpdate, ClusterResponse
from app.llm import analyze_ticket, generate_grounded_response
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
    Core customer chat endpoint. Analyzes the message, runs RAG,
    saves the ticket, runs duplicate clustering, and returns bot response.
    """
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        # 1. Run LLM Structured Analysis
        analysis = analyze_ticket(message)
        
        # 2. Generate Grounded Support Response (RAG/Fallback)
        bot_response = generate_grounded_response(message, analysis)
        
        # 3. Create Ticket record
        ticket = Ticket(
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
            status="pending_review"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # 4. Perform duplicate grouping (Clustering)
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

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
        
    update_data = payload.dict(exclude_unset=True)
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
        
    # Trigger integrations
    github_url = trigger_github_handoff(ticket_id, db)
    discord_success = trigger_discord_handoff(ticket_id, db)
    
    db.refresh(ticket)
    return {
        "status": "handoff_processed",
        "github_issue_url": ticket.github_issue_url,
        "discord_notified": ticket.discord_notified,
        "ticket_status": ticket.status
    }

@app.get("/api/clusters", response_model=List[ClusterResponse])
def get_all_clusters(db: Session = Depends(get_db)):
    """Retrieves all clusters along with the count of tickets associated with each."""
    clusters = db.query(Cluster).all()
    results = []
    for c in clusters:
        count = db.query(Ticket).filter(Ticket.cluster_id == c.id).count()
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
