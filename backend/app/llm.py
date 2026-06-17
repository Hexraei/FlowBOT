import json
import requests
import difflib
from app.config import settings

SUPPORT_DICTIONARY = [
    "error", "fail", "broken", "bug", "crash", "issue", "problem", "freeze", "stuck", 
    "down", "offline", "slow", "load", "blank", "button", "link", "menu", "page", 
    "site", "website", "app", "portal", "screen", "click", "form", "input", "hiring", 
    "job", "recruit", "intern", "internship", "partner", "collaboration", "price", 
    "cost", "quote", "enquiry", "inquire", "flowzint", "nevermind", "resolved", 
    "solved", "fixed", "kidding", "working", "never", "mind", "urgent", "asap", 
    "emergency"
]

def fuzzy_correct_token(token: str, threshold: float = 0.7) -> str:
    """Corrects a token using difflib.get_close_matches if a close match is found in SUPPORT_DICTIONARY."""
    cleaned_token = token.strip(".,;:?!\"'()[]{}")
    if not cleaned_token or len(cleaned_token) < 3:
        return token
    
    matches = difflib.get_close_matches(cleaned_token.lower(), SUPPORT_DICTIONARY, n=1, cutoff=threshold)
    if matches:
        matched = matches[0]
        if cleaned_token.isupper():
            matched = matched.upper()
        elif cleaned_token[0].isupper():
            matched = matched.capitalize()
            
        prefix = token[:token.find(cleaned_token)]
        suffix = token[token.find(cleaned_token) + len(cleaned_token):]
        return prefix + matched + suffix
    return token

def call_ollama(prompt: str, system_prompt: str = None, format_json: bool = True) -> str:
    """Helper to query the local Ollama instance running Gemma."""
    url = f"{settings.OLLAMA_HOST}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "1h"  # Keeps model loaded in RAM for 1 hour to prevent cold-start delays
    }
    if system_prompt:
        payload["system"] = system_prompt
    if format_json:
        payload["format"] = "json"
        
    try:
        response = requests.post(url, json=payload, timeout=60)
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
- "intent": Must be one of: "business_enquiry", "partnership", "contact_info", "careers", "internship_programs", "open_opportunities", "hiring_process", "service_inquiry", "resolved", or "other".
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
    # Pre-process message using fuzzy spelling engine
    corrected_message = " ".join(fuzzy_correct_token(tok) for tok in message.split())
    msg_lower = corrected_message.lower()
    
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
    
    # Resolution detection keywords
    is_resolution = any(kw in msg_lower for kw in [
        "just kidding", "nevermind", "it is working", "working now", "resolved", 
        "fixed now", "fixed it", "solved", "cancel query", "all good", "it works", 
        "no problem", "never mind", "already working"
    ])
    
    # Bug / technical issue detection keywords
    has_error_kw = any(kw in msg_lower for kw in [
        "error", "fail", "broken", "500", "bug", "crash", "issue", "problem", 
        "not working", "won't work", "does not work", "freeze", "frozen", "stuck",
        "down", "offline", "slow", "load", "blank", "cannot", "can't", "working"
    ])
    
    is_interface_element = any(kw in msg_lower for kw in [
        "button", "link", "menu", "page", "site", "website", "app", 
        "portal", "screen", "click", "form", "input", "load"
    ])
    
    if is_resolution:
        intent = "resolved"
        component = "General"
        severity = "low"
        urgency = 1
        sentiment = "positive"
    elif "hiring" in msg_lower or "job" in msg_lower or "recruit" in msg_lower:
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
    elif "flowzint" in msg_lower and any(w in msg_lower for w in ["what", "who", "about", "info", "profile", "explain", "detail", "is"]):
        intent = "about_flowzint"
        component = "General"
    elif has_error_kw or any(kw in msg_lower for kw in ["service", "automation", "ai", "saas", "infrastructure", "platform", "branding", "web", "mobile"]):
        intent = "service_inquiry"
        if has_error_kw:
            component = "Web Infrastructure" if is_interface_element else "AI & Automation"
            severity = "medium"
            urgency = 4
            sentiment = "negative"
        else:
            component = "AI & Automation"
            severity = "low"
            urgency = 3
            sentiment = "neutral"
            
    # Explicit override for angry bug reports (caps lock, multiple exclamation marks, or error keywords)
    if (msg_lower != corrected_message and len(corrected_message) > 5 and corrected_message.isupper()) or "!!!" in corrected_message or (has_error_kw and is_interface_element):
        if has_error_kw or "work" in msg_lower or "button" in msg_lower:
            intent = "service_inquiry"
            component = "Web Infrastructure"
            severity = "high"
            urgency = 5
            sentiment = "frustrated"
        
    if "urgent" in msg_lower or "asap" in msg_lower or "emergency" in msg_lower:
        urgency = 5
        severity = "high"
        sentiment = "frustrated"

    return {
        "intent": intent,
        "summary": f"Fallback: {corrected_message[:60]}...",
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
    sentiment = analysis.get("sentiment", "neutral")
    severity = analysis.get("severity", "low")
    
    if intent == "resolved":
        return (
            "Glad to hear everything is working now! Let me know if you have any other questions or need further assistance."
        )
    
    # Check if this is a technical issue/bug report (service_inquiry/other with negative/frustrated sentiment or medium/high severity)
    is_technical_issue = (
        (intent in ["service_inquiry", "other"]) and 
        (sentiment in ["frustrated", "negative"] or severity in ["medium", "high"])
    )
    
    if is_technical_issue:
        return (
            "I'm very sorry to hear that you're experiencing technical issues with our website or services. "
            "I have logged this issue for our engineering and support teams to investigate and resolve immediately."
        )
    
    if intent in ["careers", "hiring_process", "internship_programs", "open_opportunities"]:
        return (
            "FlowZint offers elite, intensive 30-Day corporate internship programs engineered "
            "for ambitious freshers. We offer 5 curated technical tracks: Artificial Intelligence, "
            "Power BI Data Analytics, Website Development, App Development, and Full Stack Engineering. "
            "Each track features daily assignments, mentor support, live projects, and a globally verifiable "
            "completion certificate with placement assistance. Freshers and college students are eligible."
        )
    elif intent in ["business_enquiry", "service_inquiry"]:
        msg = (
            "FlowZint builds future-ready enterprise digital infrastructure, SaaS systems, and intelligent AI "
            "automation platforms. Our key services include Web Infrastructure, Mobile Platforms, SaaS Systems, "
            "AI & Automation, Enterprise Systems, and Branding & Growth solutions."
        )
        if analysis.get("contact_details"):
            msg += " I have successfully logged your inquiry for the FlowZint team, and an operations lead will reach out to you."
        return msg
    elif intent == "partnership":
        msg = (
            "FlowZint is revolutionizing digital ecosystems and enterprise automation. We welcome partnerships "
            "with corporate entities, digital infrastructure vendors, and scale operations."
        )
        if analysis.get("contact_details"):
            msg += " I have logged your partnership request, and our collaboration team will review the details."
        return msg
    elif intent == "contact_info":
        return (
            "You can find official FlowZint contact channels at https://flowzint.in/fz/contact.html. "
            "Our corporate headquarters supports enquiries regarding SaaS systems, enterprise AI solutions, "
            "and hiring workflows directly through this assistant."
        )
    elif intent == "about_flowzint":
        return (
            "FlowZint is an upcoming technology company specializing in building enterprise "
            "digital infrastructure, SaaS systems, and intelligent AI automation platforms. "
            "We build future-ready solutions for global scale, helping organizations optimize "
            "workflows and integrate connected technologies."
        )
    else:
        return (
            "I'm not fully sure about that detail. I've noted down your request "
            "and routed it to the FlowZint support team for a manual response."
        )


def generate_grounded_response(message: str, analysis: dict, history: list[dict] = None) -> str:
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
    
    # Format history for the prompt if present
    history_str = ""
    if history:
        for msg in history:
            role = "User" if msg.get("sender") == "user" else "Assistant"
            history_str += f"{role}: {msg.get('text')}\n"
    
    system_prompt = (
        "You are the FlowZint AI Concierge, a polite and professional customer support assistant. "
        "Your goal is to help visitors by answering their questions using the provided facts. "
        "Important Guidelines:\n"
        "1. Speak naturally as if you are a customer support agent talking directly to a customer.\n"
        "2. Do NOT mention words like 'context', 'provided facts', 'according to the text', 'source documentation', or 'given information'. Just answer the question directly.\n"
        "3. Do not invent details. If you cannot answer the question using the facts provided, respond EXACTLY with: 'I am not sure about that detail.' (so our fallback system can route it to a human)."
    )
    
    prompt = f"""
System Instructions:
You are the FlowZint AI Concierge, a polite and professional customer support assistant.
Your goal is to answer the user question using the provided facts.
Guidelines:
1. Speak naturally as a customer support representative talking directly to a customer.
2. Do NOT use phrases like "based on the provided context", "according to the text", "context", "given documents", or similar. Just answer the question directly.
3. Do not invent details. If the provided facts do not contain the answer, respond EXACTLY with: "I am not sure about that detail."

Provided Facts:
{context_str}

Conversation History:
{history_str}

User Question: {message}

Answer:
"""
    
    try:
        response_text = call_ollama(prompt, system_prompt=system_prompt, format_json=False)
        response_text = response_text.strip()
        
        # Check if LLM indicates it doesn't know
        lower_resp = response_text.lower()
        if "don't know" in lower_resp or "do not know" in lower_resp or "cannot find" in lower_resp or "not sure" in lower_resp or not response_text:
            print("RAG: LLM indicated it doesn't know. Triggering fallback.")
            return generate_heuristic_response(message, analysis)
            
        return response_text
    except Exception as e:
        print(f"RAG generation failed: {e}. Triggering fallback.")
        return generate_heuristic_response(message, analysis)


def rewrite_query_with_history(query: str, history: list[dict]) -> str:
    """
    Given a user's latest query and the conversation history,
    resolves any coreferences and context dependencies to rewrite
    the query into a standalone, search-friendly search query.
    """
    if not history:
        return query
        
    # Format history for the prompt
    history_str = ""
    for msg in history:
        role = "User" if msg.get("sender") == "user" else "Assistant"
        history_str += f"{role}: {msg.get('text')}\n"
        
    system_prompt = (
        "You are an expert conversational AI search assistant. Your job is to read the chat history "
        "and the user's latest message, and determine if the latest message refers to previous topics (coreference). "
        "If it does, rewrite the latest message to be a standalone search query that contains all necessary context. "
        "If the latest message is already a standalone search query or is unrelated to the history, return it EXACTLY as-is. "
        "Respond ONLY with the rewritten message (or the original message if no rewrite is needed). Do not include any explanations or quotes."
    )
    
    prompt = f"""
Chat History:
{history_str}

User's Latest Message: {query}

Standalone Search Query:
"""
    try:
        rewritten = call_ollama(prompt, system_prompt=system_prompt, format_json=False)
        rewritten = rewritten.strip()
        # Clean up any quotes the model might have returned
        if rewritten.startswith('"') and rewritten.endswith('"'):
            rewritten = rewritten[1:-1].strip()
        if rewritten.startswith("'") and rewritten.endswith("'"):
            rewritten = rewritten[1:-1].strip()
        print(f"Query Rewriter: Original: '{query}' -> Rewritten: '{rewritten}'")
        return rewritten if rewritten else query
    except Exception as e:
        print(f"Query rewriting failed: {e}. Using original query.")
        return query
