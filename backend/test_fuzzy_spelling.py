import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal, Ticket, Cluster
from app.llm import fuzzy_correct_token

def clean_database():
    print("Resetting database for test...")
    db = SessionLocal()
    try:
        db.query(Ticket).delete()
        db.query(Cluster).delete()
        db.commit()
    finally:
        db.close()

def test_unit_spelling():
    print("Running Unit Tests for Spelling Correction...")
    
    # 1. Assert "webstie" corrects to "website"
    res1 = fuzzy_correct_token("webstie")
    print(f"webstie -> {res1}")
    assert res1 == "website", f"Expected 'website', got '{res1}'"
    
    # 2. Assert "intrnshp" corrects to "internship"
    res2 = fuzzy_correct_token("intrnshp")
    print(f"intrnshp -> {res2}")
    assert res2 == "internship", f"Expected 'internship', got '{res2}'"
    
    # 3. Assert "crsh" corrects to "crash"
    res3 = fuzzy_correct_token("crsh")
    print(f"crsh -> {res3}")
    assert res3 == "crash", f"Expected 'crash', got '{res3}'"
    
    # 4. Assert "flznt" corrects to "flowzint"
    res4 = fuzzy_correct_token("flznt")
    print(f"flznt -> {res4}")
    assert res4 == "flowzint", f"Expected 'flowzint', got '{res4}'"
    
    print("Unit tests passed!")

def test_integration():
    print("\n" + "="*80)
    print("TEST: Posting query with multiple typos")
    print("="*80)
    
    client = TestClient(app)
    session_id = "test-session-fuzzy-111"
    
    # 5. Post query with typos: "NONE OF THE BTTONS ARE WRKING IN YOUR WEBSTIE!!!!"
    payload = {
        "message": "NONE OF THE BTTONS ARE WRKING IN YOUR WEBSTIE!!!!",
        "session_id": session_id
    }
    
    # For testing fallback rules, we can trigger rule_based_fallback_analysis directly
    # or let the API route fail over/fallback. Since we want to make sure fallback analysis 
    # executes successfully, let's run rule_based_fallback_analysis.
    from app.llm import rule_based_fallback_analysis
    
    fallback_res = rule_based_fallback_analysis(payload["message"])
    print(f"Fallback intent: {fallback_res['intent']}")
    print(f"Fallback severity: {fallback_res['severity']}")
    print(f"Fallback sentiment: {fallback_res['sentiment']}")
    print(f"Fallback component: {fallback_res['probable_component']}")
    print(f"Fallback urgency: {fallback_res['urgency']}")
    
    assert fallback_res["intent"] == "service_inquiry", f"Expected service_inquiry, got {fallback_res['intent']}"
    assert fallback_res["severity"] == "high", f"Expected high, got {fallback_res['severity']}"
    assert fallback_res["sentiment"] == "frustrated", f"Expected frustrated, got {fallback_res['sentiment']}"
    assert fallback_res["probable_component"] == "Web Infrastructure", f"Expected Web Infrastructure, got {fallback_res['probable_component']}"
    assert fallback_res["urgency"] == 5, f"Expected urgency 5, got {fallback_res['urgency']}"
    
    # Run through the actual endpoint to verify database insertion and status = "pending_review"
    resp1 = client.post("/api/chat", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    print(f"API Response Status: {data1['status']}")
    print(f"API Response Intent: {data1['intent']}")
    assert data1["status"] == "pending_review", f"Expected status pending_review, got {data1['status']}"
    
    # 6. Post follow-up: "nvermind, it is wrking now."
    print("\n" + "="*80)
    print("TEST: Resolution query with typos ('nvermind, it is wrking now.')")
    print("="*80)
    
    payload2 = {
        "message": "nvermind, it is wrking now.",
        "session_id": session_id
    }
    
    # Run through rule-based fallback to verify resolution intent extraction
    fallback_res2 = rule_based_fallback_analysis(payload2["message"])
    print(f"Fallback intent 2: {fallback_res2['intent']}")
    assert fallback_res2["intent"] == "resolved", f"Expected resolved, got {fallback_res2['intent']}"
    
    # Run API post
    resp2 = client.post("/api/chat", json=payload2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    print(f"API Response 2 Status: {data2['status']}")
    print(f"API Response 2 Intent: {data2['intent']}")
    assert data2["status"] == "resolved", f"Expected resolved, got {data2['status']}"
    assert data2["intent"] == "resolved", f"Expected resolved intent, got {data2['intent']}"
    
    # Verify in the DB that all previous tickets in the session have been updated to "resolved"
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).filter(Ticket.session_id == session_id).all()
        print(f"\nTickets in session {session_id} after resolution:")
        for t in tickets:
            print(f"  ID: {t.id} | Msg: '{t.user_message}' | Status: {t.status}")
            assert t.status == "resolved", f"Expected ticket status to be 'resolved', got '{t.status}'"
    finally:
        db.close()
        
    print("\nFuzzy spelling and auto-resolution integration verification passed!")

if __name__ == "__main__":
    clean_database()
    test_unit_spelling()
    test_integration()
