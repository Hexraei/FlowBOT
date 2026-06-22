import json
import uuid
import logging
import numpy as np
from sqlalchemy.orm import Session
from app.database import Ticket, Cluster, SessionLocal
from app.vector_store import embedding_fn
from app.config import settings

logger = logging.getLogger(__name__)

# Cap the number of historical tickets compared per new ticket to prevent O(n) blowup
CLUSTERING_LOOKBACK = 200


def cosine_similarity(v1, v2):
    """Computes cosine similarity between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm_v1 * norm_v2)


def find_or_create_cluster(ticket_id: str, user_message: str, embedding_json: str = None):
    """
    Background-safe clustering task. Opens its own DB session.
    Compares the new ticket embedding against the most recent CLUSTERING_LOOKBACK tickets
    and groups them if similarity is above the configured threshold.

    This runs via FastAPI BackgroundTasks so it does not block the HTTP response.
    """
    db: Session = SessionLocal()
    try:
        # Retrieve the ticket
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            logger.warning(f"Clustering: Ticket {ticket_id} not found in background task.")
            return

        # 1. Retrieve or embed the new ticket message and cache it
        try:
            if embedding_json:
                new_vector = json.loads(embedding_json)
            elif ticket.embedding:
                new_vector = json.loads(ticket.embedding)
            else:
                new_vector = embedding_fn([user_message])[0]
                new_vector_list = new_vector.tolist() if hasattr(new_vector, "tolist") else list(new_vector)
                ticket.embedding = json.dumps(new_vector_list)
                db.add(ticket)
                db.commit()
                db.refresh(ticket)
                new_vector = new_vector_list
        except Exception as e:
            logger.warning(f"Clustering: Failed to get embedding for ticket {ticket_id}: {e}")
            return

        # 2. Query the most recent CLUSTERING_LOOKBACK tickets (not this ticket)
        existing_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.id != ticket_id,
                Ticket.user_message != None,
                Ticket.sender_type == "user"  # Only compare customer messages
            )
            .order_by(Ticket.created_at.desc())
            .limit(CLUSTERING_LOOKBACK)
            .all()
        )

        if not existing_tickets:
            logger.info("Clustering: No existing tickets to compare with.")
            return

        # 3. Lazily compute embeddings for any tickets missing them (batched)
        missing_tickets = [t for t in existing_tickets if t.embedding is None]
        if missing_tickets:
            try:
                logger.info(f"Clustering: Computing embeddings for {len(missing_tickets)} historical tickets...")
                missing_msgs = [t.user_message for t in missing_tickets]
                missing_vectors = embedding_fn(missing_msgs)
                for t, vec in zip(missing_tickets, missing_vectors):
                    vec_list = vec.tolist() if hasattr(vec, "tolist") else list(vec)
                    t.embedding = json.dumps(vec_list)
                    db.add(t)
                db.commit()
            except Exception as e:
                logger.warning(f"Clustering: Failed to compute lazy embeddings: {e}")

        # 4. Find highest similarity among cached embeddings
        best_score = -1.0
        best_match_ticket = None

        for t in existing_tickets:
            if not t.embedding:
                continue
            try:
                vec = json.loads(t.embedding)
                sim = cosine_similarity(new_vector, vec)
                if sim > best_score:
                    best_score = sim
                    best_match_ticket = t
            except Exception as e:
                logger.debug(f"Clustering: Failed to parse embedding for ticket {t.id}: {e}")

        logger.info(f"Clustering: Best match score: {best_score:.4f}")

        # 5. Check against threshold and assign cluster
        if best_score >= settings.CLUSTERING_THRESHOLD and best_match_ticket:
            if best_match_ticket.cluster_id:
                logger.info(f"Clustering: Joining existing cluster: {best_match_ticket.cluster_id}")
                ticket.cluster_id = best_match_ticket.cluster_id
            else:
                cluster_name = f"Cluster: {ticket.summary or 'Issue Pattern'}"
                new_cluster = Cluster(
                    id=str(uuid.uuid4()),
                    name=cluster_name,
                    description=f"Auto-generated cluster: '{user_message[:60]}...'"
                )
                db.add(new_cluster)
                db.commit()
                db.refresh(new_cluster)
                best_match_ticket.cluster_id = new_cluster.id
                ticket.cluster_id = new_cluster.id
                db.add(best_match_ticket)
                logger.info(f"Clustering: Created new cluster: {new_cluster.id}")

            db.add(ticket)
            db.commit()
        else:
            logger.info("Clustering: No cluster match above threshold.")

    except Exception as e:
        logger.exception(f"Clustering background task failed for ticket {ticket_id}: {e}")
        db.rollback()
    finally:
        db.close()
