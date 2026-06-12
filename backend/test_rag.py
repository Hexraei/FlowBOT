import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from app.llm import analyze_ticket, generate_grounded_response

def test_query(message):
    print("\n" + "="*60)
    print(f"Query: '{message}'")
    print("="*60)
    
    # 1. Run analysis to get intent/fallback context
    analysis = analyze_ticket(message)
    print(f"Analysis Intent: {analysis['intent']}")
    
    # 2. Run grounded response generation
    response = generate_grounded_response(message, analysis)
    print(f"Bot Response:\n{response}")

def main():
    test_queries = [
        "What are the internship tracks offered at FlowZint?",
        "Can you tell me about your AI and automation services?",
        "What is the capital of France, and how do I build a spaceship?"
    ]
    
    for q in test_queries:
        test_query(q)

if __name__ == "__main__":
    main()
