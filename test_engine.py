import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from ai_engine import process_complaint
from storage import get_repository

def run_tests():
    print("--- 1. Testing AI Engine Pipeline ---")
    complaint_title = "Charged ₹5,000 twice for order ORD-8812"
    complaint_body = "Hi, I was charged ₹5,000 twice for the same order. Please resolve this immediately."
    
    result = process_complaint(
        title=complaint_title,
        description=complaint_body,
        sender_name="Ranjith",
        sender_email="ranjith@example.com"
    )
    
    print(f"Complaint Category: {result['category']}")
    print(f"Department: {result['department']}")
    print(f"Sub-Department: {result['sub_department']}")
    print(f"Sentiment: {result['sentiment']} ({result['sentiment_score']})")
    print(f"Emotion: {result['emotion']}")
    print(f"Urgency: {result['urgency']}")
    print(f"Priority: {result['priority']}")
    print(f"Confidence: {result['confidence_percent']}%")
    print(f"Entities: {result['entities']}")
    print(f"Recommended Action: {result['recommended_action']}")
    print(f"Routing: {result['routing_path']}")
    print(f"SLA: {result['sla_hours']} hours")
    
    # Assertions
    assert result["department"] == "Finance", f"Expected Finance, got {result['department']}"
    assert "Payments" in result["sub_department"], f"Expected Payments, got {result['sub_department']}"
    assert result["sentiment"] == "Negative"
    assert result["urgency"] in ("High", "Critical")
    assert result["priority"] in ("High", "Critical")
    assert "5,000" in str(result["entities"])
    
    print("\n--- 2. Testing SQLite Repository ---")
    repo = get_repository()
    saved = repo.create(result)
    print(f"Created Complaint ID: {saved['id']}")
    assert saved["id"].startswith("CMP-")
    
    # Test duplicate detection
    print("\n--- 3. Testing Duplicate Detection ---")
    dup_body = "Hello, you deducted ₹5,000 twice from my account for the same order! Please resolve this immediately."
    dup_result = process_complaint(
        title="Duplicate charge ₹5000",
        description=dup_body,
        existing_complaints=[saved]
    )
    print(f"Is Duplicate: {dup_result['is_duplicate']}")
    print(f"Matched Complaint ID: {dup_result['duplicate_of_id']}")
    print(f"Similarity Score: {dup_result['duplicate_similarity']}")
    assert dup_result["is_duplicate"] is True
    assert dup_result["duplicate_of_id"] == saved["id"]
    
    print("\n--- 4. Testing Statistics Aggregation ---")
    stats = repo.get_statistics()
    print(f"Total: {stats['total']}, Open: {stats['open_count']}, Risk Level: {stats['risk_level']}")
    
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
