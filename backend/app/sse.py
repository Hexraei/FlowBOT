import asyncio
import json
import logging
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from app.database import Ticket, get_db

logger = logging.getLogger(__name__)

async def stream_session_messages(session_id: str, db_factory) -> AsyncGenerator[str, None]:
    """
    SSE generator: yields new messages for a given session_id every time new rows appear.
    Sends a heartbeat comment every 15 seconds to keep the connection alive through proxies.
    """
    last_seen_id = None
    consecutive_failures = 0

    while True:
        try:
            db: Session = next(db_factory())
            try:
                query = (
                    db.query(Ticket)
                    .filter(Ticket.session_id == session_id)
                    .order_by(Ticket.created_at.asc())
                )
                if last_seen_id:
                    # Fetch only tickets newer than the last one we sent
                    from sqlalchemy import func
                    subq = db.query(Ticket.created_at).filter(Ticket.id == last_seen_id).scalar_subquery()
                    query = query.filter(Ticket.created_at > subq)

                new_tickets = query.all()

                if new_tickets:
                    for ticket in new_tickets:
                        last_seen_id = ticket.id
                        payload = {
                            "id": ticket.id,
                            "session_id": ticket.session_id,
                            "user_message": ticket.user_message,
                            "bot_response": ticket.bot_response,
                            "sender_type": ticket.sender_type,
                            "agent_name": ticket.agent_name,
                            "is_taken_over": ticket.is_taken_over,
                            "intent": ticket.intent,
                            "status": ticket.status,
                            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                consecutive_failures = 0
            finally:
                db.close()

        except Exception as e:
            consecutive_failures += 1
            logger.warning(f"SSE session stream error (attempt {consecutive_failures}): {e}")
            if consecutive_failures >= 5:
                # Give up after 5 consecutive failures to avoid infinite error loops
                logger.error(f"SSE: Too many failures for session {session_id}. Closing stream.")
                break

        # Heartbeat comment to keep the connection alive through HTTP proxies
        yield ": heartbeat\n\n"
        await asyncio.sleep(2)


async def stream_admin_tickets(db_factory, status_filter: str = "pending_review") -> AsyncGenerator[str, None]:
    """
    SSE generator: yields the full pending ticket list to the admin dashboard
    whenever a new ticket is detected, with a 5-second refresh cycle.
    """
    last_ticket_count = -1
    consecutive_failures = 0

    while True:
        try:
            db: Session = next(db_factory())
            try:
                query = db.query(Ticket)
                if status_filter:
                    query = query.filter(Ticket.status == status_filter)

                tickets = query.order_by(Ticket.created_at.desc()).limit(100).all()
                current_count = len(tickets)

                if current_count != last_ticket_count:
                    last_ticket_count = current_count
                    payload = [
                        {
                            "id": t.id,
                            "session_id": t.session_id,
                            "user_message": t.user_message,
                            "bot_response": t.bot_response,
                            "intent": t.intent,
                            "severity": t.severity,
                            "sentiment": t.sentiment,
                            "probable_component": t.probable_component,
                            "urgency": t.urgency,
                            "contact_details": t.contact_details,
                            "confidence_score": t.confidence_score,
                            "cluster_id": t.cluster_id,
                            "status": t.status,
                            "github_issue_url": t.github_issue_url,
                            "discord_notified": t.discord_notified,
                            "is_taken_over": t.is_taken_over,
                            "agent_name": t.agent_name,
                            "sender_type": t.sender_type,
                            "created_at": t.created_at.isoformat() if t.created_at else None,
                        }
                        for t in tickets
                    ]
                    yield f"data: {json.dumps(payload)}\n\n"

                consecutive_failures = 0
            finally:
                db.close()

        except Exception as e:
            consecutive_failures += 1
            logger.warning(f"SSE admin stream error (attempt {consecutive_failures}): {e}")
            if consecutive_failures >= 5:
                logger.error("SSE: Too many failures on admin ticket stream. Closing stream.")
                break

        yield ": heartbeat\n\n"
        await asyncio.sleep(5)
