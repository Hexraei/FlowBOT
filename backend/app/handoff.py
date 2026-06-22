import logging
import requests
from sqlalchemy.orm import Session
from app.database import Ticket
from app.config import settings

logger = logging.getLogger(__name__)

def trigger_github_handoff(ticket_id: str, db: Session) -> str:
    """
    Creates a GitHub issue for a support ticket.
    If no token is provided, runs in placeholder mode logging the mock issue.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        print(f"Handoff Error: Ticket {ticket_id} not found in DB.")
        return None
        
    title = f"[{ticket.severity.upper()}] {ticket.summary or 'Support Ticket'}"
    body = (
        f"### Support Ticket Details\n"
        f"- **Ticket ID**: `{ticket.id}`\n"
        f"- **Intent**: `{ticket.intent}`\n"
        f"- **Sentiment**: `{ticket.sentiment}`\n"
        f"- **Urgency Score**: `{ticket.urgency}/5`\n"
        f"- **Probable Component**: `{ticket.probable_component}`\n"
        f"- **Contact Details**: `{ticket.contact_details or 'None shared'}`\n\n"
        f"### Customer Message\n"
        f"> {ticket.user_message}\n\n"
        f"### Bot Response\n"
        f"> {ticket.bot_response or 'No response generated.'}\n"
    )
    
    # Check if we have credentials
    if settings.GITHUB_TOKEN:
        logger.info(f"Handoff: Creating GitHub issue for ticket {ticket.id}...")
        url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/issues"
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "title": title,
            "body": body,
            "labels": [ticket.intent, ticket.severity]
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 201:
                issue_data = response.json()
                issue_url = issue_data.get("html_url")
                ticket.github_issue_url = issue_url
                ticket.status = "handoff_completed"
                db.commit()
                logger.info(f"Handoff: GitHub issue created: {issue_url}")
                return issue_url
            else:
                raise Exception(f"GitHub API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.exception(f"Handoff: GitHub API call failed: {e}")
            raise e
    else:
        logger.info(f"[PLACEHOLDER HANDOFF - GITHUB ISSUE] Target: {settings.GITHUB_REPO} | Title: {title}")
        mock_url = f"https://github.com/{settings.GITHUB_REPO}/issues/mock-{ticket.id[:8]}"
        ticket.github_issue_url = mock_url
        ticket.status = "handoff_completed"
        db.commit()
        return mock_url

def trigger_discord_handoff(ticket_id: str, db: Session) -> bool:
    """
    Sends an alert notification to a Discord channel via webhook.
    If webhook URL is empty, runs in placeholder mode.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        print(f"Handoff Error: Ticket {ticket_id} not found in DB.")
        return False
        
    # Strip PII: contact_details is excluded from the public-facing Discord notification.
    # The full ticket (including contact) is only accessible through the authenticated admin dashboard.
    payload = {
        "embeds": [
            {
                "title": f"[ALERT] Support Escalation: {ticket.summary or 'New Ticket'}",
                "description": f"**Message:** {ticket.user_message}",
                "color": 15158332 if ticket.severity == "high" else 3066993,
                "fields": [
                    {"name": "Intent", "value": ticket.intent or "N/A", "inline": True},
                    {"name": "Urgency", "value": f"{ticket.urgency}/5" if ticket.urgency else "N/A", "inline": True},
                    {"name": "Component", "value": ticket.probable_component or "N/A", "inline": True},
                    {"name": "Contact Provided", "value": "Yes — see admin dashboard" if ticket.contact_details else "No", "inline": False}
                ]
            }
        ]
    }
    
    if settings.DISCORD_WEBHOOK_URL:
        logger.info(f"Handoff: Sending Discord alert for ticket {ticket.id}...")
        try:
            response = requests.post(settings.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code in [200, 204]:
                ticket.discord_notified = True
                db.commit()
                logger.info("Handoff: Discord notification sent successfully.")
                return True
            else:
                raise Exception(f"Discord API returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.exception(f"Handoff: Discord webhook failed: {e}")
            raise e
    else:
        logger.info(f"[PLACEHOLDER HANDOFF - DISCORD ALERT] Payload: {payload}")
        ticket.discord_notified = True
        db.commit()
        return True
