from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

class TicketRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

    @field_validator('message')
    @classmethod
    def message_length_limit(cls, v: str) -> str:
        if len(v.strip()) == 0:
            raise ValueError("Message cannot be empty.")
        if len(v) > 2000:
            raise ValueError("Message is too long. Please keep it under 2000 characters.")
        return v

class PublicTicketResponse(BaseModel):
    """
    Stripped-down ticket response for public/customer-facing endpoints.
    Excludes sensitive fields like contact_details, github_issue_url, discord_notified,
    cluster_id, confidence_score to prevent PII/operational leakage.
    """
    id: str
    session_id: Optional[str] = None
    created_at: datetime
    user_message: str
    bot_response: Optional[str] = None
    intent: Optional[str] = None
    status: str
    is_taken_over: bool
    agent_name: Optional[str] = None
    sender_type: str

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class TakeoverRequest(BaseModel):
    agent_name: str

    @field_validator('agent_name')
    @classmethod
    def agent_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Agent name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Agent name is too long.")
        return v

class AgentMessageRequest(BaseModel):
    message: str
    agent_name: str

    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if len(v.strip()) == 0:
            raise ValueError("Message cannot be empty.")
        if len(v) > 2000:
            raise ValueError("Message is too long.")
        return v

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

    class Config:
        from_attributes = True
