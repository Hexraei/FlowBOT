import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Ticket, Cluster

client = TestClient(app)

def clean_database():
    db = SessionLocal()
    db.query(Ticket).delete()
    db.query(Cluster).delete()
    db.commit()
    db.close()

def test_api():
    print("Clearing database for API tests...")
    clean_database()
    
    # 1. Test POST /api/chat (Internship query)
    print("\nQuerying POST /api/chat with internship question...")
    response = client.post("/api/chat", json={"message": "Do you offer web development internship programs?"})
    print(f"Status Code: {response.status_code}")
    data = response.json()
    ticket_id = data.get("id")
    print(f"Ticket ID  : {ticket_id}")
    print(f"Response   : {data.get('bot_response')[:120]}...")
    print(f"Intent     : {data.get('intent')}")
    print(f"Severity   : {data.get('severity')}")
    
    # 2. Test POST /api/chat (Duplicate internship query)
    print("\nQuerying duplicate POST /api/chat question...")
    response_dup = client.post("/api/chat", json={"message": "Tell me more about FlowZint internship opportunities"})
    data_dup = response_dup.json()
    print(f"Status Code: {response_dup.status_code}")
    print(f"Cluster ID : {data_dup.get('cluster_id')}")
    
    # 3. Test GET /api/tickets
    print("\nQuerying GET /api/tickets...")
    response_tickets = client.get("/api/tickets")
    tickets = response_tickets.json()
    print(f"Status Code: {response_tickets.status_code}")
    print(f"Found {len(tickets)} tickets in DB.")
    
    # 4. Test PUT /api/tickets/{id}
    print(f"\nQuerying PUT /api/tickets/{ticket_id} to update fields...")
    update_payload = {
        "severity": "medium",
        "status": "pending_review",
        "contact_details": "candidate@gmail.com"
    }
    response_put = client.put(f"/api/tickets/{ticket_id}", json=update_payload)
    print(f"Status Code: {response_put.status_code}")
    data_put = response_put.json()
    print(f"Updated Contact Details: {data_put.get('contact_details')}")
    print(f"Updated Severity       : {data_put.get('severity')}")
    
    # 5. Test POST /api/tickets/{id}/handoff
    print(f"\nQuerying POST /api/tickets/{ticket_id}/handoff...")
    response_handoff = client.post(f"/api/tickets/{ticket_id}/handoff")
    print(f"Status Code: {response_handoff.status_code}")
    handoff_data = response_handoff.json()
    print(f"GitHub URL : {handoff_data.get('github_issue_url')}")
    print(f"Discord ok : {handoff_data.get('discord_notified')}")
    print(f"New Status : {handoff_data.get('ticket_status')}")
    
    # 6. Test GET /api/clusters
    print("\nQuerying GET /api/clusters...")
    response_clusters = client.get("/api/clusters")
    clusters = response_clusters.json()
    print(f"Status Code: {response_clusters.status_code}")
    print(f"Active Clusters count: {len(clusters)}")
    for c in clusters:
        print(f"  Cluster '{c['name']}' has {c['ticket_count']} ticket(s).")
        
    print("\nAPI core endpoints verification complete!")

if __name__ == "__main__":
    test_api()
