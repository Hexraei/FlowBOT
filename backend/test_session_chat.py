import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal, Ticket, Cluster

def clean_database():
    print("Resetting database for test...")
    db = SessionLocal()
    try:
        db.query(Ticket).delete()
        db.query(Cluster).delete()
        db.commit()
        
        # Seed general cluster
        default_cluster = Cluster(
            id="default-general-inquiries",
            name="General Inquiries",
            description="Cluster for general questions about FlowZint services."
        )
        db.add(default_cluster)
        db.commit()
    finally:
        db.close()

def main():
    clean_database()
    client = TestClient(app)
    session_id = "test-session-chat-999"
    
    print("\n" + "="*80)
    print("TEST 1: Asking initial question about internship price")
    print("="*80)
    
    payload1 = {
        "message": "What is the registration fee for the internships?",
        "session_id": session_id
    }
    resp1 = client.post("/api/chat", json=payload1)
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
    data1 = resp1.json()
    
    # Safe printing of response (replacing Rupee symbol to prevent CP1252 terminal crashes)
    safe_response1 = data1["bot_response"].replace("\u20b9", "Rs.")
    print(f"User   : {payload1['message']}")
    print(f"Bot    : {safe_response1}")
    print(f"Intent : {data1['intent']}")
    print(f"Status : {data1['status']}")
    assert data1["status"] == "resolved_by_ai", f"Expected resolved_by_ai, got {data1['status']}"
    assert "1999" in safe_response1, "Expected price ₹1999 to be in response"
    
    print("\n" + "="*80)
    print("TEST 2: Asking follow-up query with coreference ('in these')")
    print("="*80)
    
    payload2 = {
        "message": "okay what do you offer in these?",
        "session_id": session_id
    }
    resp2 = client.post("/api/chat", json=payload2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    safe_response2 = data2["bot_response"].replace("\u20b9", "Rs.")
    print(f"User   : {payload2['message']}")
    print(f"Bot    : {safe_response2}")
    print(f"Intent : {data2['intent']}")
    print(f"Status : {data2['status']}")
    assert data2["status"] == "resolved_by_ai", f"Expected resolved_by_ai, got {data2['status']}"
    assert data2["intent"] == "internship_programs", f"Expected intent internship_programs, got {data2['intent']}"
    assert any(kw in safe_response2.lower() for kw in ["curriculum", "assignment", "project", "certificate", "placement", "artificial", "website", "power bi", "engineering"]), "Expected internship details in response"

    print("\n" + "="*80)
    print("TEST 3: Asking business inquiry with contact details (should trigger pending_review)")
    print("="*80)
    
    payload3 = {
        "message": "Can you design a custom SaaS platform for us? Contact me at business@flowzint.in",
        "session_id": session_id
    }
    resp3 = client.post("/api/chat", json=payload3)
    assert resp3.status_code == 200
    data3 = resp3.json()
    safe_response3 = data3["bot_response"].replace("\u20b9", "Rs.")
    print(f"User   : {payload3['message']}")
    print(f"Bot    : {safe_response3}")
    print(f"Intent : {data3['intent']}")
    print(f"Status : {data3['status']}")
    print(f"Contact: {data3['contact_details']}")
    assert data3["status"] == "pending_review", f"Expected pending_review, got {data3['status']}"
    assert data3["contact_details"] == "business@flowzint.in", f"Expected email extraction, got {data3['contact_details']}"

    print("\nStateful Chat Session Context and Lead Escalation Filtering validation completed successfully!")

if __name__ == "__main__":
    main()
