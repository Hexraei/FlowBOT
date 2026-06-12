import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal, Ticket, init_db
from app.handoff import trigger_github_handoff, trigger_discord_handoff

def test_handoff():
    db = SessionLocal()
    init_db()
    
    # Create a test ticket
    test_ticket = Ticket(
        user_message="Hello FlowZint team, we are seeking a SaaS system deployment and AI automation workflow consulting. Contact me at leads@client.com",
        summary="SaaS & AI automation enquiry",
        intent="business_enquiry",
        sentiment="positive",
        severity="medium",
        probable_component="AI & Automation",
        urgency=4,
        contact_details="leads@client.com",
        bot_response="Certainly! I have captured your enquiry..."
    )
    db.add(test_ticket)
    db.commit()
    db.refresh(test_ticket)
    
    print(f"Created ticket: {test_ticket.id}")
    
    # Run handoffs
    github_url = trigger_github_handoff(test_ticket.id, db)
    discord_success = trigger_discord_handoff(test_ticket.id, db)
    
    # Query ticket again to verify database updates
    db.refresh(test_ticket)
    
    print("\n" + "="*50)
    print("Verification Results:")
    print("="*50)
    print(f"GitHub URL stored: {test_ticket.github_issue_url}")
    print(f"Discord notified : {test_ticket.discord_notified}")
    print(f"Ticket Status    : {test_ticket.status}")
    
    db.close()

if __name__ == "__main__":
    test_handoff()
