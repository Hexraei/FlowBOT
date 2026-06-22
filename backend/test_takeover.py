import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Ticket
from app.config import settings

client = TestClient(app)

def test_live_takeover_flow():
    print("\n--- Starting Takeover Flow Test ---")
    session_id = f"test_session_{os.urandom(4).hex()}"
    
    # 1. Send first user message
    print(f"1. Sending user message for session: {session_id}")
    response = client.post("/api/chat", json={"message": "I want to apply for React internships", "session_id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["sender_type"] == "user"
    assert data["bot_response"] is not None
    assert "taken_over" not in data or data["is_taken_over"] is False
    print("User message answered by bot successfully!")

    # 2. Trigger Takeover
    print("2. Triggering takeover by agent 'David'")
    takeover_response = client.post(f"/api/tickets/session/{session_id}/takeover", json={"agent_name": "David"})
    assert takeover_response.status_code == 200
    takeover_data = takeover_response.json()
    assert takeover_data["status"] == "success"
    assert takeover_data["agent_name"] == "David"
    print("Session takeover successful!")

    # 3. Retrieve messages and check history
    print("3. Querying message stream history...")
    messages_response = client.get(f"/api/tickets/session/{session_id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()
    
    # We expect 3 messages: 
    # - User query (t.sender_type = "user")
    # - Bot response (represented as t.bot_response on the user query, or if mapped: in DB it's stored on same ticket)
    # - System takeover notification (t.sender_type = "system", message = "David has joined the chat.")
    assert len(messages) == 2 # 1 User ticket (which contains user msg + bot response) and 1 System ticket
    
    system_msg = messages[1]
    assert system_msg["sender_type"] == "system"
    assert "David has joined" in system_msg["user_message"]
    print("History verified with system takeover notification!")

    # 4. Agent sends response
    print("4. Agent sends response: 'Hello, this is David. How can I help?'")
    agent_response = client.post(f"/api/tickets/session/{session_id}/message", json={
        "message": "Hello, this is David. How can I help?",
        "agent_name": "David"
    })
    assert agent_response.status_code == 200
    agent_data = agent_response.json()
    assert agent_data["sender_type"] == "agent"
    assert agent_data["user_message"] == "Hello, this is David. How can I help?"
    assert agent_data["agent_name"] == "David"
    assert agent_data["is_taken_over"] is True
    print("Agent message saved successfully!")

    # 5. Customer replies (should bypass LLM)
    print("5. Customer replies: 'I want to ask about registration fees'")
    customer_response = client.post("/api/chat", json={
        "message": "I want to ask about registration fees",
        "session_id": session_id
    })
    assert customer_response.status_code == 200
    cust_data = customer_response.json()
    assert cust_data["sender_type"] == "user"
    assert cust_data["bot_response"] is None # Bypassed!
    assert cust_data["is_taken_over"] is True
    assert cust_data["agent_name"] == "David"
    print("Customer reply processed and LLM bypassed successfully!")

    # 6. Retrieve history again and verify total messages
    print("6. Verifying final history stream...")
    final_response = client.get(f"/api/tickets/session/{session_id}/messages")
    assert final_response.status_code == 200
    final_messages = final_response.json()
    
    # Expected messages:
    # 1. First user ticket (user message + bot response)
    # 2. System takeover notification
    # 3. Agent message
    # 4. Second customer message (no bot response)
    assert len(final_messages) == 4
    assert final_messages[0]["sender_type"] == "user"
    assert final_messages[1]["sender_type"] == "system"
    assert final_messages[2]["sender_type"] == "agent"
    assert final_messages[3]["sender_type"] == "user"
    assert final_messages[3]["bot_response"] is None
    
    print("\nTakeover Flow Test passed successfully!")

if __name__ == "__main__":
    test_live_takeover_flow()
