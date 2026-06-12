import json
import requests
from app.config import settings

def call_ollama(prompt: str, system_prompt: str = None, format_json: bool = True) -> str:
    """Helper to query the local Ollama instance running Gemma."""
    url = f"{settings.OLLAMA_HOST}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    if system_prompt:
        payload["system"] = system_prompt
    if format_json:
        payload["format"] = "json"
        
    try:
        response = requests.post(url, json=payload, timeout=25)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        print(f"Ollama/Gemma request failed: {e}")
        raise e

def analyze_ticket(message: str) -> dict:
    """
    Classifies intent, estimates severity, sentiment, urgency, component,
    and extracts contact details into a structured JSON dict using Gemma.
    """
    system_prompt = (
        "You are an expert AI support triaging agent. Your job is to read customer "
        "messages and extract structured intelligence. You must respond ONLY with a "
        "valid JSON object. Do not include any conversational text outside the JSON."
    )
    
    prompt = f"""
Analyze the following customer message and return a JSON object with these EXACT keys:
- "intent": Must be one of: "business_enquiry", "partnership", "contact_info", "careers", "internship_programs", "open_opportunities", "hiring_process", "service_inquiry", or "other".
- "summary": A concise, one-sentence summary of what the customer wants.
- "severity": Must be "high", "medium", or "low". High is for severe errors, billing complaints, or critical business blockers.
- "sentiment": Must be "positive", "neutral", "negative", or "frustrated".
- "probable_component": The module or area of the request (e.g., "AI & Automation", "SaaS Systems", "Careers", "Web Infrastructure", "Billing", "General").
- "urgency": An integer score from 1 (lowest) to 5 (highest) indicating the response priority.
- "contact_details": Extracted email, phone, or name if explicitly provided, otherwise "".
- "confidence_score": A float from 0.0 to 1.0 representing how confident you are in this analysis.

Customer message:
\"\"\"
{message}
\"\"\"

JSON Response:
"""

    try:
        response_text = call_ollama(prompt, system_prompt=system_prompt, format_json=True)
        data = json.loads(response_text)
        # Validate keys and types, apply defaults if missing
        return {
            "intent": data.get("intent", "other"),
            "summary": data.get("summary", message[:100] + "..."),
            "severity": data.get("severity", "low"),
            "sentiment": data.get("sentiment", "neutral"),
            "probable_component": data.get("probable_component", "General"),
            "urgency": int(data.get("urgency", 3)),
            "contact_details": data.get("contact_details", ""),
            "confidence_score": float(data.get("confidence_score", 0.5))
        }
    except Exception as e:
        print(f"Failed to process Gemma structured output: {e}")
        # Rule-based fallback if JSON parsing fails or Ollama is offline
        return rule_based_fallback_analysis(message)

def rule_based_fallback_analysis(message: str) -> dict:
    """Rule-based backup analyser when Ollama is offline or returns invalid JSON."""
    msg_lower = message.lower()
    
    # Simple keyword heuristics
    intent = "other"
    component = "General"
    urgency = 3
    severity = "low"
    sentiment = "neutral"
    contact_details = ""
    
    # Extract email placeholder if any
    for word in msg_lower.split():
        if "@" in word and "." in word:
            contact_details = word.strip(".,;:?!\"'")
            break
            
    import re
    if "hiring" in msg_lower or "job" in msg_lower or "recruit" in msg_lower:
        intent = "hiring_process"
        component = "Careers"
    elif re.search(r'\bintern(ship)?s?\b', msg_lower):
        intent = "internship_programs"
        component = "Careers"
    elif "partner" in msg_lower or "collaboration" in msg_lower:
        intent = "partnership"
        component = "General"
    elif "price" in msg_lower or "cost" in msg_lower or "quote" in msg_lower or "enquiry" in msg_lower or "inquire" in msg_lower:
        intent = "business_enquiry"
        component = "Branding & Growth"
    elif any(kw in msg_lower for kw in ["error", "fail", "broken", "500", "bug", "service", "automation", "ai", "saas", "infrastructure", "platform", "branding", "web", "mobile"]):
        intent = "service_inquiry"
        if any(kw in msg_lower for kw in ["error", "fail", "broken", "500", "bug"]):
            component = "Web Infrastructure"
            severity = "medium"
            urgency = 4
            sentiment = "negative"
        else:
            component = "AI & Automation"
            severity = "low"
            urgency = 3
            sentiment = "neutral"
        
    if "urgent" in msg_lower or "asap" in msg_lower or "emergency" in msg_lower:
        urgency = 5
        severity = "high"
        sentiment = "frustrated"

    return {
        "intent": intent,
        "summary": f"Fallback: {message[:60]}...",
        "severity": severity,
        "sentiment": sentiment,
        "probable_component": component,
        "urgency": urgency,
        "contact_details": contact_details,
        "confidence_score": 0.3  # Low confidence due to fallback
    }

def generate_heuristic_response(message: str, analysis: dict) -> str:
    """Generates a high-quality pre-scripted answer from FlowZint's text when Ollama is offline."""
    intent = analysis.get("intent", "other")
    
    if intent in ["careers", "hiring_process", "internship_programs", "open_opportunities"]:
        return (
            "FlowZint offers elite, intensive 30-Day corporate internship programs engineered "
            "for ambitious freshers. We offer 5 curated technical tracks: Artificial Intelligence, "
            "Power BI Data Analytics, Website Development, App Development, and Full Stack Engineering. "
            "Each track features daily assignments, mentor support, live projects, and a globally verifiable "
            "completion certificate with placement assistance. Freshers and college students are eligible."
        )
    elif intent in ["business_enquiry", "service_inquiry"]:
        return (
            "FlowZint builds future-ready enterprise digital infrastructure, SaaS systems, and intelligent AI "
            "automation platforms. Our key services include Web Infrastructure, Mobile Platforms, SaaS Systems, "
            "AI & Automation, Enterprise Systems, and Branding & Growth solutions. I have successfully logged "
            "your inquiry for the FlowZint team, and an operations lead will reach out to you."
        )
    elif intent == "partnership":
        return (
            "FlowZint is revolutionizing digital ecosystems and enterprise automation. We welcome partnerships "
            "with corporate entities, digital infrastructure vendors, and scale operations. I have logged your "
            "partnership request, and our collaboration team will review the details."
        )
    elif intent == "contact_info":
        return (
            "You can find official FlowZint contact channels at https://flowzint.in/fz/contact.html. "
            "Our corporate headquarters supports enquiries regarding SaaS systems, enterprise AI solutions, "
            "and hiring workflows directly through this assistant."
        )
    else:
        return (
            "I'm not fully sure about that detail. I've noted down your request "
            "and routed it to the FlowZint support team for a manual response."
        )

def generate_grounded_response(message: str, analysis: dict) -> str:
    """
    Generates a response grounded in FlowZint's official crawled content.
    If the content isn't relevant, triggers fallback behavior.
    """
    fallback_message = (
        "I'm not fully sure about that detail. I've noted down your request "
        "and routed it to the FlowZint support team for a manual response."
    )
    
    from app.vector_store import retrieve_relevant_docs
    
    # 1. Fetch relevant docs from Chroma
    docs = retrieve_relevant_docs(message, limit=3)
    
    # 2. Check if we have any documents and if they are relevant
    if not docs or max(d["score"] for d in docs) < 0.35:
        print(f"RAG: Best similarity score too low. Triggering fallback.")
        return generate_heuristic_response(message, analysis)
        
    # 3. Construct prompt for Gemma
    context_str = "\n\n".join(
        f"Source: {d['title']} ({d['url']})\nContent: {d['content']}" 
        for d in docs
    )
    
    system_prompt = (
        "You are the FlowZint AI Concierge, a helpful support assistant. "
        "Your task is to answer user queries using ONLY the provided FlowZint context. "
        "Do not invent facts. If the answer cannot be found in the context, say "
        "\"I don't know the answer based on the context.\""
    )
    
    prompt = f"""
Context:
{context_str}

User Question: {message}

Answer:
"""
    
    try:
        response_text = call_ollama(prompt, system_prompt=system_prompt, format_json=False)
        response_text = response_text.strip()
        
        # Check if LLM indicates it doesn't know
        lower_resp = response_text.lower()
        if "don't know" in lower_resp or "do not know" in lower_resp or "cannot find" in lower_resp or not response_text:
            print("RAG: LLM indicated it doesn't know. Triggering fallback.")
            return generate_heuristic_response(message, analysis)
            
        return response_text
    except Exception as e:
        print(f"RAG generation failed: {e}. Triggering fallback.")
        return generate_heuristic_response(message, analysis)
