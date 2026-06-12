import json
import uuid
import numpy as np
from sqlalchemy.orm import Session
from app.database import Ticket, Cluster
from app.vector_store import embedding_fn
from app.config import settings

def cosine_similarity(v1, v2):
    """Computes cosine similarity between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm_v1 * norm_v2)

def find_or_create_cluster(ticket: Ticket, db: Session) -> str:
    """
    Computes embedding of the ticket message, finds the most similar existing ticket.
    If similarity > CLUSTERING_THRESHOLD, groups them under the same cluster.
    Returns the cluster_id.
    """
    # 1. Embed the new ticket message
    try:
        new_vector = embedding_fn([ticket.user_message])[0]
    except Exception as e:
        print(f"Clustering: Failed to embed new ticket message: {e}")
        return None
        
    # 2. Query all existing tickets that have a user_message and are not this ticket
    existing_tickets = db.query(Ticket).filter(
        Ticket.id != ticket.id,
        Ticket.user_message != None
    ).all()
    
    if not existing_tickets:
        print("Clustering: No existing tickets to compare with.")
        return None
        
    # 3. Embed all existing tickets (on the fly for MVP simplicity)
    try:
        messages = [t.user_message for t in existing_tickets]
        existing_vectors = embedding_fn(messages)
    except Exception as e:
        print(f"Clustering: Failed to embed existing messages: {e}")
        return None
        
    # 4. Find the highest similarity
    best_score = -1.0
    best_match_ticket = None
    
    for t, vec in zip(existing_tickets, existing_vectors):
        sim = cosine_similarity(new_vector, vec)
        if sim > best_score:
            best_score = sim
            best_match_ticket = t
            
    print(f"Clustering: Best match found with similarity score: {best_score:.4f}")
    
    # 5. Check against threshold
    if best_score >= settings.CLUSTERING_THRESHOLD and best_match_ticket:
        # If the matching ticket already has a cluster, join it
        if best_match_ticket.cluster_id:
            print(f"Clustering: Grouping with existing cluster: {best_match_ticket.cluster_id}")
            return best_match_ticket.cluster_id
        else:
            # Create a new cluster for both tickets
            cluster_name = f"Cluster: {ticket.summary or 'Issue Pattern'}"
            new_cluster = Cluster(
                id=str(uuid.uuid4()),
                name=cluster_name,
                description=f"Auto-generated cluster grouping similar tickets like: '{ticket.user_message[:60]}...'"
            )
            db.add(new_cluster)
            db.commit()
            db.refresh(new_cluster)
            
            # Update the existing matching ticket to be in this cluster too
            best_match_ticket.cluster_id = new_cluster.id
            db.add(best_match_ticket)
            db.commit()
            
            print(f"Clustering: Created new cluster: {new_cluster.id}")
            return new_cluster.id
            
    print("Clustering: No cluster match found above threshold.")
    return None
