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

def chunk_text(text: str, max_chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Recursively splits text into chunks of max_chunk_size with overlap.
    Tries splitting on paragraphs (\n\n), newlines (\n), sentences (. ), and spaces (words) in order.
    """
    if max_chunk_size is None:
        max_chunk_size = settings.RAG_CHUNK_SIZE
    if overlap is None:
        overlap = settings.RAG_CHUNK_OVERLAP
        
    separators = ["\n\n", "\n", ". ", " ", ""]
    
    def split_recursive(text_to_split: str, current_sep_idx: int) -> list[str]:
        if len(text_to_split) <= max_chunk_size:
            return [text_to_split]
            
        if current_sep_idx >= len(separators):
            # Hard split at chunk boundary
            return [text_to_split[i : i + max_chunk_size] for i in range(0, len(text_to_split), max_chunk_size)]
            
        separator = separators[current_sep_idx]
        splits = text_to_split.split(separator) if separator else list(text_to_split)
        
        chunks = []
        current_chunk = []
        current_len = 0
        
        for part in splits:
            part_len = len(part) + (len(separator) if current_chunk else 0)
            
            # If a single part exceeds max_chunk_size, split recursively with next separator
            if part_len > max_chunk_size:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                sub_chunks = split_recursive(part, current_sep_idx + 1)
                chunks.extend(sub_chunks)
                continue
                
            if current_len + part_len > max_chunk_size:
                chunks.append(separator.join(current_chunk))
                # Retain overlap: backtrack from current_chunk to fill up overlap character count
                overlap_chunk = []
                overlap_len = 0
                for prev in reversed(current_chunk):
                    prev_len = len(prev) + (len(separator) if overlap_chunk else 0)
                    if overlap_len + prev_len > overlap:
                        break
                    overlap_chunk.insert(0, prev)
                    overlap_len += prev_len
                current_chunk = overlap_chunk
                current_len = overlap_len
                
            current_chunk.append(part)
            current_len += part_len
            
        if current_chunk:
            chunks.append(separator.join(current_chunk))
            
        return chunks

    return split_recursive(text, 0)

def index_knowledge_base():
    """Reads all text files in the knowledge_base directory, chunks them, and stores in Chroma."""
    global collection
    kb_path = settings.KNOWLEDGE_BASE_DIR
    if not os.path.exists(kb_path):
        print(f"Knowledge base directory '{kb_path}' does not exist.")
        return
        
    txt_files = glob.glob(os.path.join(kb_path, "*.txt"))
    if not txt_files:
        print(f"No .txt files found in '{kb_path}'")
        return
        
    print(f"Clearing existing Chroma collection to prevent orphan chunks...")
    try:
        chroma_client.delete_collection("flowzint_kb")
    except Exception as e:
        print(f"No collection to delete: {e}")
        
    collection = chroma_client.get_or_create_collection(
        name="flowzint_kb",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
        
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
                # Prepend the page title to embed document-level semantics in every chunk
                chunk_with_context = f"Page Title: {title}\n{chunk}"
                documents.append(chunk_with_context)
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

def retrieve_relevant_docs(query: str, limit: int = None) -> list[dict]:
    """Retrieves relevant document chunks from Chroma given a search query."""
    if limit is None:
        limit = settings.RAG_TOP_K
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

def retrieve_relevant_docs_by_vector(vector: list[float], limit: int = None) -> list[dict]:
    """Retrieves relevant document chunks from Chroma given a pre-computed query vector."""
    if limit is None:
        limit = settings.RAG_TOP_K
    try:
        results = collection.query(
            query_embeddings=[vector],
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
        print(f"Error querying Chroma vector store by vector: {e}")
        return []
