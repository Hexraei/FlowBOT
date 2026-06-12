import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from app.vector_store import index_knowledge_base, retrieve_relevant_docs

def main():
    print("Starting knowledge base indexing...")
    index_knowledge_base()
    
    print("\nVerifying search capability with test query: 'react internships'...")
    results = retrieve_relevant_docs("react internships", limit=2)
    
    for i, res in enumerate(results):
        print(f"\nResult #{i+1}:")
        print(f"  Title   : {res['title']}")
        print(f"  URL     : {res['url']}")
        print(f"  Score   : {res['score']:.4f}")
        print(f"  Content : {res['content'][:150]}...")
        
    print("\nKnowledge Base RAG verification complete!")

if __name__ == "__main__":
    main()
