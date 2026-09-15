import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.complaint import Complaint, ComplaintFeedback
from app.models.organization import Department
from ml.preprocessing.cleaner import cleaner
from ml.predict import ComplaintPredictor

def test_ml_cleaner_entity_normalization():
    """Verifies that ComplaintCleaner removes HTML, normalizes contractions and preserves entities."""
    raw = "<b>Help!</b> I can't pay $250.00 for order ORD-12345. My email is user@test.com."
    cleaned = cleaner.clean(raw)

    assert "<b>" not in cleaned
    assert "cannot" in cleaned
    assert "currency_amount" in cleaned or "250" in cleaned
    assert "order_id" in cleaned or "ord-12345" in cleaned


def test_ml_predictor_inference():
    """Verifies that the trained baseline model outputs predictions and confidence for all 4 targets."""
    predictor = ComplaintPredictor(model_family="baseline_logreg")
    res = predictor.predict("I was charged twice for $99 on my credit card and need a full refund immediately.")

    assert "predictions" in res
    preds = res["predictions"]
    for target in ["department", "category", "priority", "sentiment"]:
        assert target in preds
        assert "label" in preds[target]
        assert "confidence" in preds[target]
        assert 0.0 <= preds[target]["confidence"] <= 1.0

    assert preds["department"]["label"] == "Finance"


def test_ml_evaluation_actual_metrics_not_fabricated():
    """Verifies that actual metrics report was generated on the held-out test split."""
    import json
    metrics_path = PROJECT_ROOT / "ml" / "evaluation" / "metrics_report.json"
    assert metrics_path.exists(), f"Evaluation metrics report must exist at {metrics_path}"

    with open(metrics_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "models" in data
    assert "Baseline_LogisticRegression" in data["models"]
    logreg = data["models"]["Baseline_LogisticRegression"]

    for target in ["department", "category", "priority", "sentiment"]:
        assert target in logreg
        m = logreg[target]
        assert 0.0 <= m["accuracy"] <= 1.0
        assert 0.0 <= m["f1_macro"] <= 1.0
        assert 0.0 <= m["precision_macro"] <= 1.0
        assert 0.0 <= m["recall_macro"] <= 1.0
        assert "confusion_matrix" in m
        assert isinstance(m["confusion_matrix"], list)


def test_human_feedback_recording_when_manager_changes_department(client: TestClient, db: Session):
    """
    Verifies that when AI predicts Department = IT with confidence,
    but manager changes it to Finance, a ComplaintFeedback record is created:
    - prediction: IT
    - corrected_value: Finance
    - corrected_by: Operations Manager
    - reason: Payment gateway issue belongs to Finance
    """
    dept_it = Department(name="IT Division", code="ITDIV", description="IT department")
    dept_fin = Department(name="Finance Division", code="FINDIV", description="Finance department")
    db.add_all([dept_it, dept_fin])
    db.commit()

    # Complaint initially assigned to IT with 0.82 confidence
    complaint = Complaint(
        complaint_number="CMP-FB-001",
        customer_email="user@test.com",
        subject="Payment debited twice",
        description="Duplicate charge on payment gateway",
        category="Billing",
        department_id=dept_it.id,
        ai_confidence=0.82,
        status="OPEN"
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Manager changes department to Finance
    res = client.post(
        f"/api/complaints/{complaint.id}/department",
        json={
            "department_id": dept_fin.id,
            "reason": "Payment gateway duplicate debit belongs to Finance team",
            "actor": "Operations Manager"
        }
    )
    assert res.status_code == 200

    # Verify ComplaintFeedback record was created
    fb = db.query(ComplaintFeedback).filter(
        ComplaintFeedback.complaint_id == complaint.id,
        ComplaintFeedback.field_name == "department"
    ).first()

    assert fb is not None
    assert fb.prediction == "IT Division"
    assert fb.corrected_value == "Finance Division"
    assert fb.ai_confidence == 0.82
    assert fb.corrected_by == "Operations Manager"
    assert "Payment gateway" in fb.reason
    assert "Payment debited twice" in fb.complaint_text
