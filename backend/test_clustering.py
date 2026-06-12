import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal, Ticket, Cluster, init_db
from app.clustering import find_or_create_cluster

def clean_database(db):
    db.query(Ticket).delete()
    db.query(Cluster).delete()
    db.commit()

def test_clustering():
    db = SessionLocal()
    init_db()
    
    print("Clearing database for test...")
    clean_database(db)
    
    # Define similar and dissimilar test cases
    tickets_data = [
        {"msg": "Billing dashboard shows internal server error 500", "summary": "Billing 500 Error"},
        {"msg": "We are getting a billing server error 500 when loading dashboard", "summary": "Billing dashboard error"},
        {"msg": "500 server error on the billing page", "summary": "Billing page 500"},
        {"msg": "Are there open opportunities for React developers in your internship programs?", "summary": "Internships query"}
    ]
    
    tickets = []
    for data in tickets_data:
        t = Ticket(
            user_message=data["msg"],
            summary=data["summary"],
            intent="other",
            severity="low"
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        tickets.append(t)
        
    print(f"Added {len(tickets)} test tickets.")
    
    # Run clustering sequentially
    print("\nRunning clustering for each ticket...")
    for idx, t in enumerate(tickets):
        print(f"\nProcessing Ticket #{idx+1}: '{t.user_message}'")
        cluster_id = find_or_create_cluster(t, db)
        t.cluster_id = cluster_id
        db.add(t)
        db.commit()
        print(f"Assigned Cluster ID: {cluster_id}")
        
    # Verify results
    print("\n" + "="*50)
    print("Verification Results:")
    print("="*50)
    
    all_tickets = db.query(Ticket).all()
    for t in all_tickets:
        print(f"Ticket: '{t.user_message[:40]}...' -> Cluster: {t.cluster_id}")
        
    db.close()

if __name__ == "__main__":
    test_clustering()
