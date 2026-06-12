import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from app.config import settings

# Initialize persistent Chroma client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

# Using Chroma's built-in sentence-transformers embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Create or get collection
collection = chroma_client.get_or_create_collection(
    name="flowzint_kb",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

def chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Helper to chunk text with overlap."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1  # count space
        if current_length >= max_chunk_size:
            chunks.append(" ".join(current_chunk))
            # Keep overlap: keep last N words
            overlap_words = current_chunk[-max_chunk_size // (5 * 5):] # simple heuristic
            current_chunk = list(overlap_words)
            current_length = sum(len(w) + 1 for w in current_chunk)
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def index_knowledge_base():
    """Reads all text files in the knowledge_base directory, chunks them, and stores in Chroma."""
    kb_path = settings.KNOWLEDGE_BASE_DIR
    if not os.path.exists(kb_path):
        print(f"Knowledge base directory '{kb_path}' does not exist.")
        return
        
    txt_files = glob.glob(os.path.join(kb_path, "*.txt"))
    if not txt_files:
        print(f"No .txt files found in '{kb_path}'")
        return
        
    print(f"Indexing {len(txt_files)} knowledge base files into Chroma...")
    
    documents = []
    metadatas = []
    ids = []
    
    chunk_counter = 0
    for file_path in txt_files:
        filename = os.path.basename(file_path)
        source_name = os.path.splitext(filename)[0]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Basic parsing of Title and URL from file headers
            title = source_name.replace("-", " ").title()
            url = ""
            lines = content.splitlines()
            body_start = 0
            
            if lines and lines[0].startswith("Title:"):
                title = lines[0].replace("Title:", "").strip()
                body_start = 1
            if len(lines) > 1 and lines[1].startswith("URL:"):
                url = lines[1].replace("URL:", "").strip()
                body_start = 2
                
            body_content = "\n".join(lines[body_start:])
            chunks = chunk_text(body_content)
            
            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": source_name,
                    "title": title,
                    "url": url,
                    "chunk_index": idx
                })
                ids.append(f"doc_{source_name}_{idx}")
                chunk_counter += 1
                
        except Exception as e:
            print(f"Failed to read/chunk {filename}: {e}")

    if documents:
        # Upsert documents to Chroma
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully indexed {chunk_counter} text chunks.")
    else:
        print("No document chunks to index.")

def retrieve_relevant_docs(query: str, limit: int = 3) -> list[dict]:
    """Retrieves relevant document chunks from Chroma given a search query."""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        retrieved_docs = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                retrieved_docs.append({
                    "content": doc,
                    "title": meta.get("title", ""),
                    "url": meta.get("url", ""),
                    "source": meta.get("source", ""),
                    "score": 1.0 - dist # Cosine similarity score
                })
        return retrieved_docs
    except Exception as e:
        print(f"Error querying Chroma vector store: {e}")
        return []
