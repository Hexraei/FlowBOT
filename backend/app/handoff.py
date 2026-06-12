import requests
from sqlalchemy.orm import Session
from app.database import Ticket
from app.config import settings

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
        print(f"Handoff: Creating real GitHub issue for ticket {ticket.id}...")
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
                print(f"Handoff: Real GitHub issue created: {issue_url}")
                return issue_url
            else:
                print(f"Handoff Error: GitHub API returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Handoff Error: Failed to call GitHub API: {e}")
            
    # Placeholder Mode Fallback
    print(f"\n[PLACEHOLDER HANDOFF - GITHUB ISSUE]")
    print(f"Target Repository : {settings.GITHUB_REPO}")
    print(f"Issue Title       : {title}")
    print(f"Issue Body        :\n{body}")
    print(f"[END GITHUB PLACEHOLDER]\n")
    
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
        
    payload = {
        "embeds": [
            {
                "title": f"[ALERT] Support Escalation: {ticket.summary or 'New Ticket'}",
                "description": f"**Message:** {ticket.user_message}",
                "color": 15158332 if ticket.severity == "high" else 3066993, # Red for High, Green otherwise
                "fields": [
                    {"name": "Intent", "value": ticket.intent or "N/A", "inline": True},
                    {"name": "Urgency", "value": f"{ticket.urgency}/5" if ticket.urgency else "N/A", "inline": True},
                    {"name": "Component", "value": ticket.probable_component or "N/A", "inline": True},
                    {"name": "Contact", "value": ticket.contact_details or "None shared", "inline": False}
                ]
            }
        ]
    }
    
    # Check if webhook URL is set
    if settings.DISCORD_WEBHOOK_URL:
        print(f"Handoff: Sending Discord webhook for ticket {ticket.id}...")
        try:
            response = requests.post(settings.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code in [200, 204]:
                ticket.discord_notified = True
                db.commit()
                print("Handoff: Discord notification sent successfully.")
                return True
            else:
                print(f"Handoff Error: Discord API returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Handoff Error: Failed to post to Discord webhook: {e}")
            
    # Placeholder Mode Fallback
    print(f"\n[PLACEHOLDER HANDOFF - DISCORD ALERT]")
    print(f"Webhook URL       : (Empty / Placeholder)")
    print(f"Discord Payload   : {payload}")
    print(f"[END DISCORD PLACEHOLDER]\n")
    
    ticket.discord_notified = True
    db.commit()
    return True
