import re
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import Config

# ==============================================================================
# TAXONOMY & KEYWORD PATTERNS
# ==============================================================================

CATEGORY_MAPPING = {
    "Billing / Payment": {
        "department": "Finance",
        "keywords": [
            "charged", "charge", "refund", "paid", "payment", "bank", "credit card", "debit card",
            "transaction", "invoice", "receipt", "deducted", "double charged", "twice", "overcharged",
            "fee", "billing", "money", "rupees", "inr", "usd", "dollar", "emi", "wallet", "subscription",
            "pricing", "unauthorized charge", "cashback", "tax", "gst"
        ],
        "sub_departments": {
            "Payments & Refunds": ["refund", "double", "twice", "twice for", "duplicate", "deducted", "reversal", "failed transaction"],
            "Billing & Invoicing": ["invoice", "receipt", "gst", "tax", "statement", "bill", "overcharge"],
            "Subscription Services": ["subscription", "renew", "renewal", "membership", "plan", "cancel subscription"],
            "Fraud & Chargebacks": ["fraud", "unauthorized", "stolen", "scam", "compromised card"]
        }
    },
    "Technical Problem": {
        "department": "IT",
        "keywords": [
            "bug", "error", "crash", "glitch", "broken", "down", "outage", "slow", "server", "loading",
            "failed", "connection", "offline", "api", "app", "database", "login failed", "not working",
            "500", "404", "freeze", "white screen", "timeout", "latency", "dns"
        ],
        "sub_departments": {
            "System & Server Outages": ["down", "outage", "offline", "server", "maintenance", "unreachable", "500"],
            "Software Bug & Glitch": ["bug", "glitch", "crash", "error", "freeze", "button not working", "exception"],
            "Account Access & Login": ["login", "signin", "password", "reset", "otp", "2fa", "blocked account", "lockout"],
            "Network & Connectivity": ["slow", "latency", "timeout", "bandwidth", "disconnecting", "dns", "wifi"]
        }
    },
    "Security Issue": {
        "department": "Security",
        "keywords": [
            "hack", "hacked", "breach", "security", "vulnerability", "phishing", "spam", "malware",
            "unauthorized access", "suspicious", "leak", "compromised", "identity theft", "attacker",
            "stolen credentials", "data privacy", "gdpr", "permission"
        ],
        "sub_departments": {
            "Account Compromise": ["hacked", "unauthorized access", "compromised", "intruder", "hijacked"],
            "Data Privacy & Compliance": ["privacy", "gdpr", "leak", "personal data", "exposed", "confidential"],
            "Phishing & Suspicious Activity": ["phishing", "suspicious", "fake email", "spoof", "malware"],
            "Permission & Identity": ["permission", "identity", "privilege", "impersonation", "credentials"]
        }
    },
    "Customer Support": {
        "department": "Support",
        "keywords": [
            "delivery", "shipping", "order", "product", "damaged", "delayed", "tracking", "courier",
            "package", "item", "wrong item", "return", "exchange", "support", "help", "agent",
            "service", "customer care", "warranty", "missing"
        ],
        "sub_departments": {
            "Order Tracking & Shipping": ["tracking", "where is", "dispatch", "courier", "delayed delivery", "transit"],
            "Returns & Replacements": ["return", "replacement", "damaged", "broken item", "exchange", "wrong item"],
            "Product Inquiries": ["product", "specifications", "manual", "warranty", "feature", "availability"],
            "General Customer Service": ["help", "representative", "contact", "assistance", "inquiry"]
        }
    },
    "Operations & Admin": {
        "department": "Operations",
        "keywords": [
            "academic", "admission", "grade", "university", "faculty", "policy", "terms", "contract",
            "legal", "management", "escalation", "campus", "course", "facility", "staff", "behavior",
            "complaint against", "unprofessional", "manager"
        ],
        "sub_departments": {
            "Academic / Campus Admin": ["academic", "admission", "grade", "faculty", "course", "exam", "campus"],
            "Service Escalations": ["manager", "supervisor", "escalation", "escalate", "unacceptable behavior"],
            "Policy & Terms Enforcement": ["policy", "terms", "agreement", "rules", "contract", "compliance"],
            "Vendor Management": ["vendor", "contractor", "third-party", "partner", "facility"]
        }
    }
}

EMOTION_KEYWORDS = {
    "Anger": ["angry", "furious", "outrageous", "pathetic", "ridiculous", "unacceptable", "lawsuit", "sue", "terrible", "worst", "hate"],
    "Frustration": ["frustrated", "annoying", "tired of", "again", "still not", "twice", "repeatedly", "waste of time", "useless", "immediately"],
    "Anxiety": ["worried", "urgent", "emergency", "scared", "panicking", "afraid", "critical", "loss", "stolen"],
    "Disappointment": ["disappointed", "expected better", "let down", "unhappy", "poor quality", "regret", "bad experience"],
    "Gratitude": ["thank you", "appreciate", "helpful", "grateful", "glad"],
}

URGENCY_KEYWORDS = {
    "Critical": ["immediately", "asap", "emergency", "urgent", "critical", "blocked", "hacked", "breach", "legal action", "unauthorized", "right now", "severe"],
    "High": ["soon", "priority", "important", "double charged", "twice", "not working", "cannot access", "deadline", "fast", "today"],
    "Medium": ["please look into", "check", "issue", "problem", "inconvenience", "waiting"],
    "Low": ["whenever possible", "general question", "just wondering", "feedback", "suggestion", "inquiry"]
}

# ==============================================================================
# 1. ENTITY EXTRACTION
# ==============================================================================

def extract_entities(text: str) -> Dict[str, Any]:
    """Extracts structured entities such as Monetary Amounts, Order/Transaction IDs, and Dates."""
    entities: Dict[str, Any] = {}

    # Monetary Amounts (₹, $, €, INR, USD, Rs)
    currency_pattern = r"(?:(?:₹|rs\.?|inr|\$|usd|eur|€)\s*[\d,]+(?:\.\d{2})?|[\d,]+(?:\.\d{2})?\s*(?:rupees|inr|rs|dollars|usd))"
    amount_matches = re.findall(currency_pattern, text, re.IGNORECASE)
    if amount_matches:
        raw_amt = amount_matches[0].strip()
        clean_num = re.sub(r"[^\d.]", "", raw_amt)
        currency_sym = re.sub(r"[\d.,\s]", "", raw_amt) or "₹"
        entities["amount"] = raw_amt
        entities["normalized_amount"] = f"{currency_sym}{clean_num}"

    # Order IDs (e.g. ORD-12345, Order #98765)
    order_pattern = r"(?:order|ord)[\s#:-]*([A-Z0-9_-]{4,15})"
    order_matches = re.findall(order_pattern, text, re.IGNORECASE)
    if order_matches:
        raw_val = order_matches[0].upper().strip(" -#:")
        if raw_val.startswith("ORD-"):
            entities["order_id"] = raw_val
        elif raw_val.startswith("ORD"):
            entities["order_id"] = f"ORD-{raw_val[3:].lstrip('-_')}"
        else:
            entities["order_id"] = f"ORD-{raw_val}"

    # Transaction / Reference IDs (e.g. TXN-998877, Ref: 123456)
    txn_pattern = r"(?:txn|transaction|ref|reference|utr)[\s#:-]*([A-Z0-9_-]{5,20})"
    txn_matches = re.findall(txn_pattern, text, re.IGNORECASE)
    if txn_matches:
        entities["transaction_id"] = txn_matches[0].upper()

    # Email addresses
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        entities["detected_email"] = email_matches[0]

    # Specific issues
    text_lower = text.lower()
    if "twice" in text_lower or "duplicate" in text_lower or "double" in text_lower:
        entities["issue"] = "Duplicate Payment / Double Charge"
    elif "hacked" in text_lower or "unauthorized" in text_lower:
        entities["issue"] = "Unauthorized Security Incident"
    elif "outage" in text_lower or "down" in text_lower or "server error" in text_lower:
        entities["issue"] = "System Downtime / Outage"
    elif "refund" in text_lower:
        entities["issue"] = "Refund Request"
    elif "not received" in text_lower or "delayed" in text_lower:
        entities["issue"] = "Delivery Delay"

    return entities

# ==============================================================================
# 2. SENTIMENT & EMOTION CLASSIFICATION
# ==============================================================================

def analyze_sentiment_and_emotion(text: str) -> Tuple[str, float, str]:
    """Analyzes text to determine Sentiment (Positive, Neutral, Negative), confidence score, and primary Emotion."""
    text_lower = text.lower()

    # Detect Emotion
    detected_emotion = "Neutral"
    max_emotion_matches = 0
    for emotion, keywords in EMOTION_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > max_emotion_matches:
            max_emotion_matches = count
            detected_emotion = emotion

    # Detect Sentiment
    negative_words = [
        "not", "bad", "terrible", "horrible", "awful", "worst", "poor", "fail", "failed", "broken",
        "error", "bug", "glitch", "crash", "wrong", "charged", "loss", "stolen", "unauthorized",
        "useless", "pathetic", "frustrated", "angry", "disappointed", "hate", "issue", "problem"
    ]
    positive_words = [
        "great", "good", "excellent", "awesome", "fixed", "resolved", "thanks", "thank",
        "appreciate", "helpful", "satisfied", "pleased", "wonderful"
    ]

    words = re.findall(r"\w+", text_lower)
    neg_count = sum(1 for w in words if w in negative_words)
    pos_count = sum(1 for w in words if w in positive_words)

    if detected_emotion in ("Anger", "Frustration", "Anxiety", "Disappointment"):
        sentiment = "Negative"
        score = min(0.98, 0.70 + (neg_count * 0.05))
    elif neg_count > pos_count:
        sentiment = "Negative"
        score = min(0.95, 0.60 + ((neg_count - pos_count) * 0.07))
    elif pos_count > neg_count:
        sentiment = "Positive"
        score = min(0.95, 0.65 + ((pos_count - neg_count) * 0.08))
    else:
        sentiment = "Neutral"
        score = 0.55

    return sentiment, round(score, 2), detected_emotion

# ==============================================================================
# 3. MULTI-TIER CATEGORY & DEPARTMENT CLASSIFICATION
# ==============================================================================

def classify_complaint(text: str) -> Tuple[str, str, str, float]:
    """Classifies text into Category, Department, Sub-department, and computes confidence score."""
    text_lower = text.lower()

    best_category = "Customer Support"
    best_dept = "Support"
    max_matches = 0
    total_tokens_checked = 0

    scores = {}
    for cat_name, cat_data in CATEGORY_MAPPING.items():
        match_count = 0
        for kw in cat_data["keywords"]:
            if kw in text_lower:
                # Weight phrases higher than single words
                weight = 2 if " " in kw else 1
                match_count += weight
        scores[cat_name] = match_count
        if match_count > max_matches:
            max_matches = match_count
            best_category = cat_name
            best_dept = cat_data["department"]

    # Sub-department classification
    sub_depts = CATEGORY_MAPPING[best_category]["sub_departments"]
    best_sub = list(sub_depts.keys())[0]
    sub_max = 0
    for sub_name, sub_kws in sub_depts.items():
        sc = sum(2 if kw in text_lower else 0 for kw in sub_kws)
        if sc > sub_max:
            sub_max = sc
            best_sub = sub_name

    # Calculate Confidence
    if max_matches >= 3:
        confidence = min(0.96, 0.82 + (max_matches * 0.03))
    elif max_matches >= 1:
        confidence = 0.76 + (max_matches * 0.04)
    else:
        confidence = 0.62  # Low confidence, triggers human review

    return best_category, best_dept, best_sub, round(confidence, 2)

# ==============================================================================
# 4. URGENCY & DYNAMIC PRIORITY ENGINE
# ==============================================================================

def calculate_urgency_and_priority(
    text: str, category: str, entities: Dict[str, Any], sentiment: str, emotion: str
) -> Tuple[str, str, int, str]:
    """Computes Urgency, Dynamic Priority, SLA target hours, and human-review flag."""
    text_lower = text.lower()

    # Evaluate Urgency
    urgency = "Medium"
    for level, keywords in URGENCY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            urgency = level
            break

    # If duplicate charge or large financial amount, force at least High urgency
    if "amount" in entities or entities.get("issue") == "Duplicate Payment / Double Charge":
        if urgency in ("Low", "Medium"):
            urgency = "High"

    # Dynamic Priority calculation
    priority = urgency
    if category in ("Security Issue",) or emotion in ("Anger",):
        priority = "Critical"
    elif urgency == "Critical" or (urgency == "High" and sentiment == "Negative"):
        priority = "Critical"
    elif urgency == "High" or (sentiment == "Negative" and emotion == "Frustration"):
        priority = "High"
    elif urgency == "Low" and sentiment != "Negative":
        priority = "Low"

    sla_hours = Config.SLA_HOURS.get(priority, 24)
    deadline = (datetime.now() + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S")

    return urgency, priority, sla_hours, deadline

# ==============================================================================
# 5. RECOMMENDED ACTION GENERATOR
# ==============================================================================

def generate_recommended_action(
    category: str, sub_department: str, entities: Dict[str, Any], urgency: str
) -> str:
    """Generates concrete departmental action recommendations based on classification and entities."""
    amount = entities.get("amount", "")
    issue = entities.get("issue", "")
    order_id = entities.get("order_id", "")

    if "Duplicate" in issue or ("Payments" in sub_department and amount):
        amt_str = f" of {amount}" if amount else ""
        return f"Verify duplicate transaction logs in payment gateway and initiate refund workflow{amt_str}. Notify customer with bank reference UTR once processed."

    if category == "Billing / Payment":
        return "Inspect billing ledger, verify invoice discrepancies with the merchant gateway, and provide an updated statement."

    if category == "Security Issue":
        return "Initiate security containment protocol immediately: invalidate active sessions, check IP audit logs, and trigger mandatory credential reset."

    if "Server Outages" in sub_department:
        return "Dispatch incident to on-call Site Reliability Engineering (SRE) team. Check telemetry dashboards and update public status page."

    if category == "Technical Problem":
        return "Review application error logs, reproduce the issue in staging environment, and assign developer ticket for immediate patch."

    if "Order Tracking" in sub_department or order_id:
        ord_str = f" for {order_id}" if order_id else ""
        return f"Contact logistics partner to trace shipment status{ord_str}. Update tracking link and notify customer of revised ETA."

    return "Review complaint details, reach out to customer to verify requirements, and provide resolution within assigned SLA."

# ==============================================================================
# 6. AI-ASSISTED CUSTOMER RESPONSE GENERATOR
# ==============================================================================

def generate_ai_response_draft(
    sender_name: str,
    title: str,
    description: str,
    category: str,
    department: str,
    sub_department: str,
    entities: Dict[str, Any],
    priority: str,
    sla_hours: int
) -> str:
    """Generates an empathetic, professional customer response draft tailored to the complaint details."""
    name = sender_name or "Valued Customer"
    amount = entities.get("amount")
    issue = entities.get("issue")
    order_id = entities.get("order_id")

    # Specific response templates based on issue
    if "Duplicate" in str(issue) or (amount and category == "Billing / Payment"):
        draft = (
            f"Dear {name},\n\n"
            f"Thank you for contacting our support team. We sincerely apologize for the inconvenience "
            f"caused by the duplicate charge{f' of {amount}' if amount else ''}.\n\n"
            f"Our {department} team ({sub_department}) has flagged your case as {priority} priority. "
            f"We are actively reviewing our payment gateway transaction records to locate the duplicate deduction. "
            f"Once verified, the refund will be initiated directly back to your original payment method, "
            f"typically reflecting within 3–5 business days depending on your issuing bank.\n\n"
            f"We will provide a follow-up confirmation with the transaction reference number within {sla_hours} hours.\n\n"
            f"Warm regards,\n"
            f"{department} Operations Team"
        )
    elif category == "Security Issue":
        draft = (
            f"Dear {name},\n\n"
            f"We take the security and privacy of your account with utmost seriousness. Your report regarding "
            f"suspicious activity has been routed immediately to our {department} team ({sub_department}).\n\n"
            f"As a precautionary measure, our security engineers are inspecting active sessions and verifying access logs. "
            f"If you suspect unauthorized access, we recommend resetting your password immediately and enabling 2-factor authentication.\n\n"
            f"Our security officers will reach out with findings and remediation steps within {sla_hours} hours.\n\n"
            f"Sincerely,\n"
            f"Information Security & Privacy Team"
        )
    elif category == "Technical Problem":
        draft = (
            f"Dear {name},\n\n"
            f"Thank you for alerting us to this technical issue: \"{title}\".\n\n"
            f"Our {department} team has logged this incident under {priority} priority. Our engineering staff "
            f"is diagnosing the error logs and working on deploying a resolution. "
            f"We are committed to resolving this within our {sla_hours}-hour SLA window and will keep you updated on our progress.\n\n"
            f"Best regards,\n"
            f"Technical Support Operations"
        )
    else:
        ref_part = f" regarding {order_id}" if order_id else ""
        draft = (
            f"Dear {name},\n\n"
            f"Thank you for reaching out to us{ref_part}. We have received your complaint regarding: \"{title}\".\n\n"
            f"Your request has been routed to our {department} team ({sub_department}) under {priority} priority. "
            f"A dedicated representative has been assigned to investigate your issue and will provide a complete "
            f"resolution within {sla_hours} hours.\n\n"
            f"Thank you for your patience and understanding.\n\n"
            f"Sincerely,\n"
            f"{department} Customer Care"
        )

    return draft

# ==============================================================================
# 7. DUPLICATE COMPLAINT DETECTION
# ==============================================================================

def check_duplicate(
    new_text: str,
    existing_complaints: List[Dict[str, Any]],
    new_entities: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[str], float]:
    """Calculates TF-IDF cosine similarity and entity overlap against existing complaints to flag duplicates."""
    if not existing_complaints or not new_text.strip():
        return False, None, 0.0

    valid_existing = [c for c in existing_complaints if c.get("description") or c.get("title")]
    if not valid_existing:
        return False, None, 0.0

    corpus = [f"{c.get('title', '')} {c.get('description', '')}" for c in valid_existing]

    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)
        tfidf_matrix = vectorizer.fit_transform([new_text] + corpus)
        similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        max_idx = int(similarity_scores.argmax())
        base_score = float(similarity_scores[max_idx])
        matched_complaint = valid_existing[max_idx]

        # Entity correlation boost
        boost = 0.0
        if new_entities:
            existing_entities = matched_complaint.get("entities") or {}
            if isinstance(existing_entities, str):
                import json
                try:
                    existing_entities = json.loads(existing_entities)
                except Exception:
                    existing_entities = {}

            # Compare Order ID
            new_oid = new_entities.get("order_id")
            old_oid = existing_entities.get("order_id")
            if new_oid and old_oid and new_oid == old_oid:
                boost += 0.35

            # Compare Normalized Monetary Amount
            new_amt = new_entities.get("normalized_amount") or re.sub(r"[^\d]", "", str(new_entities.get("amount", "")))
            old_amt = existing_entities.get("normalized_amount") or re.sub(r"[^\d]", "", str(existing_entities.get("amount", "")))
            if new_amt and old_amt and new_amt == old_amt:
                boost += 0.30

            # Compare Specific Issue
            new_iss = new_entities.get("issue")
            old_iss = existing_entities.get("issue")
            if new_iss and old_iss and new_iss == old_iss:
                boost += 0.20

        final_score = min(0.99, base_score + boost)
        threshold = Config.DUPLICATE_SIMILARITY_THRESHOLD

        if final_score >= threshold:
            matched_id = matched_complaint.get("id")
            return True, matched_id, round(final_score, 2)

        return False, None, round(final_score, 2)
    except Exception:
        return False, None, 0.0

# ==============================================================================
# 8. MASTER COMPLAINT PROCESSOR
# ==============================================================================

def process_complaint(
    title: str,
    description: str,
    sender_name: str = "",
    sender_email: str = "",
    source: str = "Web Form",
    existing_complaints: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Comprehensive end-to-end NLP processing pipeline for incoming complaints."""
    combined_text = f"{title} {description}"

    # 1. Entity Extraction
    entities = extract_entities(combined_text)

    # 2. Category & Department Routing
    category, department, sub_department, cat_confidence = classify_complaint(combined_text)

    # 3. Sentiment & Emotion Analysis
    sentiment, sentiment_score, emotion = analyze_sentiment_and_emotion(combined_text)

    # 4. Urgency & Dynamic Priority
    urgency, priority, sla_hours, sla_deadline = calculate_urgency_and_priority(
        combined_text, category, entities, sentiment, emotion
    )

    # 5. Composite AI Confidence
    entity_bonus = 0.05 if entities else 0.0
    composite_confidence = min(0.98, max(0.40, cat_confidence + entity_bonus))
    confidence_percent = int(composite_confidence * 100)
    review_required = composite_confidence < Config.AI_CONFIDENCE_THRESHOLD

    # 6. Duplicate Detection
    is_dup, dup_id, dup_sim = check_duplicate(
        combined_text, existing_complaints or [], new_entities=entities
    )

    # 7. Recommended Action
    recommended_action = generate_recommended_action(category, sub_department, entities, urgency)

    # 8. Routing Path
    routing_path = f"{department} → {sub_department}"
    assigned_agent = f"{sub_department} Specialist"

    # 9. AI Response Draft
    ai_response_draft = generate_ai_response_draft(
        sender_name=sender_name,
        title=title,
        description=description,
        category=category,
        department=department,
        sub_department=sub_department,
        entities=entities,
        priority=priority,
        sla_hours=sla_hours
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "source": source,
        "sender_name": sender_name or "Anonymous",
        "sender_email": sender_email,
        "title": title,
        "description": description,
        "category": category,
        "department": department,
        "sub_department": sub_department,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "emotion": emotion,
        "urgency": urgency,
        "priority": priority,
        "confidence": composite_confidence,
        "confidence_percent": confidence_percent,
        "review_required": review_required,
        "entities": entities,
        "recommended_action": recommended_action,
        "routing_path": routing_path,
        "assigned_agent": assigned_agent,
        "sla_hours": sla_hours,
        "sla_deadline": sla_deadline,
        "sla_status": "Active",
        "is_duplicate": is_dup,
        "duplicate_of_id": dup_id,
        "duplicate_similarity": dup_sim,
        "ai_response_draft": ai_response_draft,
        "status": "In Review" if review_required else "Open",
        "resolution_notes": "",
        "created_at": now_str,
        "updated_at": now_str,
        "notification_sent": True
    }