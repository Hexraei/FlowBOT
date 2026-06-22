from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TicketRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class TicketResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    created_at: datetime
    user_message: str
    bot_response: Optional[str] = None
    intent: Optional[str] = None
    severity: Optional[str] = None
    sentiment: Optional[str] = None
    probable_component: Optional[str] = None
    urgency: Optional[int] = None
    contact_details: Optional[str] = None
    confidence_score: Optional[float] = None
    cluster_id: Optional[str] = None
    status: str
    github_issue_url: Optional[str] = None
    discord_notified: bool
    is_taken_over: bool
    agent_name: Optional[str] = None
    sender_type: str

class TakeoverRequest(BaseModel):
    agent_name: str

class AgentMessageRequest(BaseModel):
    message: str
    agent_name: str

class TicketUpdate(BaseModel):
    intent: Optional[str] = None
    severity: Optional[str] = None
    sentiment: Optional[str] = None
    probable_component: Optional[str] = None
    urgency: Optional[int] = None
    contact_details: Optional[str] = None
    status: Optional[str] = None

class ClusterResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    ticket_count: int
