import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from app.database import init_db, SessionLocal, Cluster

def main():
    print("Initializing SQLite database...")
    init_db()
    
    # Verify we can open a session and write a test cluster
    db = SessionLocal()
    try:
        # Check if we already have clusters
        count = db.query(Cluster).count()
        print(f"Current cluster count: {count}")
        if count == 0:
            print("Seeding a default cluster...")
            default_cluster = Cluster(
                id="default-general-inquiries",
                name="General Inquiries",
                description="Cluster for general questions about FlowZint services or contact details."
            )
            db.add(default_cluster)
            db.commit()
            print("Successfully seeded database.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        sys.exit(1)
    finally:
        db.close()
        
    print("Database verification complete!")

if __name__ == "__main__":
    main()
