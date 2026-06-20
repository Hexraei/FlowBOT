import datetime
import uuid
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import settings

Base = declarative_base()

class Cluster(Base):
    __tablename__ = "clusters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    tickets = relationship("Ticket", back_populates="cluster")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=True)
    
    # AI Structuring results
    intent = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    severity = Column(String, nullable=True)
    sentiment = Column(String, nullable=True)
    probable_component = Column(String, nullable=True)
    urgency = Column(Integer, nullable=True)
    contact_details = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationships & Metadata
    cluster_id = Column(String, ForeignKey("clusters.id"), nullable=True)
    embedding = Column(Text, nullable=True)  # Stores JSON string of the float embedding vector
    status = Column(String, default="pending_review") # pending_review, handoff_completed, resolved, ignored
    
    # Downstream integrations
    github_issue_url = Column(String, nullable=True)
    discord_notified = Column(Boolean, default=False)
    
    cluster = relationship("Cluster", back_populates="tickets")

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
