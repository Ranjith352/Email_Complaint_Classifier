import pytest
from app.ai.ner import (
    BaseNERExtractor,
    HybridNERExtractor,
    EntityExtractor,
    ner_extractor,
    TARGET_ENTITY_TYPES
)

def test_user_exact_example_ner():
    # User's exact prompt specification:
    # "I paid ₹4500 for order ORD92831 but it was charged twice."
    # Extract:
    # AMOUNT = ₹4500
    # ORDER_ID = ORD92831
    text = "I paid ₹4500 for order ORD92831 but it was charged twice."
    entities = ner_extractor.extract_entities(text)

    entity_map = {e["entity_type"]: e["entity_value"] for e in entities}

    assert "AMOUNT" in entity_map
    assert entity_map["AMOUNT"] == "₹4500"

    assert "ORDER_ID" in entity_map
    assert entity_map["ORDER_ID"] == "ORD92831"

def test_extract_all_10_target_entity_types():
    assert set(TARGET_ENTITY_TYPES) == {
        "PERSON",
        "EMAIL",
        "PHONE",
        "ORDER_ID",
        "TRANSACTION_ID",
        "AMOUNT",
        "DATE",
        "PRODUCT",
        "COMPANY",
        "LOCATION"
    }

    full_text = (
        "My name is Sarah Connor. I am writing to report an issue with Stripe in New York. "
        "On March 2nd, 2026, I purchased a cloud storage subscription for $199.00 using email sarah@example.com. "
        "The transaction TXN-99812 for order #ORD-44919 failed twice. Please call me at +1-555-0199."
    )
    entities = ner_extractor.extract_entities(full_text)
    found_types = {e["entity_type"] for e in entities}

    # Verify all extracted categories
    assert "PERSON" in found_types
    assert "EMAIL" in found_types
    assert "PHONE" in found_types
    assert "ORDER_ID" in found_types
    assert "TRANSACTION_ID" in found_types
    assert "AMOUNT" in found_types
    assert "DATE" in found_types
    assert "PRODUCT" in found_types
    assert "COMPANY" in found_types
    assert "LOCATION" in found_types

def test_entities_stored_in_complaint_entities_table(client):
    # Intake a complaint containing exact user example
    res = client.post("/api/complaints/", json={
        "subject": "Double charged on my order",
        "description": "I paid ₹4500 for order ORD92831 but it was charged twice.",
        "customer_email": "customer@example.com",
        "customer_name": "Ranjith Kumar",
        "source": "WEB"
    })
    assert res.status_code == 201
    c_data = res.json()
    c_id = c_data["id"]

    # Verify entities stored in complaint_entities via API
    ent_res = client.get(f"/api/complaints/{c_id}/entities")
    assert ent_res.status_code == 200
    stored_entities = ent_res.json()

    stored_map = {e["entity_type"]: e["entity_value"] for e in stored_entities}

    # Must verify storage of AMOUNT and ORDER_ID in complaint_entities
    assert "AMOUNT" in stored_map
    assert stored_map["AMOUNT"] == "₹4500"

    assert "ORDER_ID" in stored_map
    assert stored_map["ORDER_ID"] == "ORD92831"
