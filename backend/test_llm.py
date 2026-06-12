import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
sys.path.append(os.path.dirname(__file__))

from app.llm import analyze_ticket

def test_message(message):
    print("\n" + "="*50)
    print(f"Testing message: '{message}'")
    print("="*50)
    analysis = analyze_ticket(message)
    for k, v in analysis.items():
        print(f"  {k:20}: {v} (Type: {type(v).__name__})")

def main():
    # Test cases representing different intents
    test_cases = [
        "Hi, I am interested in doing a partnership with FlowZint for digital infrastructure projects. You can email me at collabs@partner.com",
        "Where is your hiring process document? Are there open opportunities for react developer internships?",
        "Our dashboard is completely down! We are getting a 500 internal server error and it is blocking our customers. Please fix ASAP!",
        "Hello, just wanted to know what is your contact phone number?"
    ]
    
    for tc in test_cases:
        test_message(tc)

if __name__ == "__main__":
    main()
