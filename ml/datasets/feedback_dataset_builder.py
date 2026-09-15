import os
import csv
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Ensure backend root can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

BASE_DIR = Path(__file__).resolve().parent
RAW_CSV = BASE_DIR / "raw" / "complaints_raw.csv"
AUGMENTED_CSV = BASE_DIR / "raw" / "complaints_feedback_augmented.csv"

def extract_feedback_records() -> List[Dict[str, str]]:
    """
    Extracts human-corrected complaint feedback records from PostgreSQL/SQLite database
    to construct augmented training datasets for model retraining.
    """
    feedback_samples = []
    try:
        from app.core.database import SessionLocal
        from app.models.complaint import Complaint, ComplaintFeedback
        
        db = SessionLocal()
        try:
            records = db.query(ComplaintFeedback).all()
            for fb in records:
                # Retrieve complaint text
                complaint_text = fb.complaint_text
                if not complaint_text and fb.complaint:
                    complaint_text = f"{fb.complaint.subject} {fb.complaint.description}"

                if not complaint_text:
                    continue

                # Default values from original complaint if present
                orig_cat = fb.complaint.category if fb.complaint else "General Inquiry"
                orig_dept = fb.complaint.department.name if (fb.complaint and fb.complaint.department) else "Customer Support"
                orig_prio = fb.complaint.priority if fb.complaint else "P3"
                orig_sent = fb.complaint.sentiment if fb.complaint else "Neutral"
                orig_sub = fb.complaint.sub_category if fb.complaint else "General"

                # Apply human corrections to construct high-value labeled samples
                corrected_dept = fb.corrected_value if fb.field_name == "department" else orig_dept
                corrected_cat = fb.corrected_category or (fb.corrected_value if fb.field_name == "category" else orig_cat)
                corrected_prio = fb.corrected_value if fb.field_name == "priority" else orig_prio

                feedback_samples.append({
                    "complaint_text": complaint_text.strip(),
                    "category": corrected_cat,
                    "department": corrected_dept,
                    "subcategory": orig_sub,
                    "priority": corrected_prio,
                    "sentiment": orig_sent,
                    "is_human_corrected": True,
                    "original_prediction": fb.prediction,
                    "corrected_by": fb.corrected_by or "Manager",
                    "correction_reason": fb.reason or "Manager override"
                })
        finally:
            db.close()
    except Exception as e:
        print(f"Notice: Database feedback extraction encountered: {e}. Proceeding with base data.")

    return feedback_samples

def build_augmented_dataset(base_csv_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Merges human feedback into the base raw dataset to form an up-to-date retraining corpus.
    """
    src = base_csv_path or RAW_CSV
    dest = output_path or AUGMENTED_CSV

    if not src.exists():
        from ml.datasets.dataset_generator import generate_dataset
        src = generate_dataset()

    # Read base records
    base_rows = []
    with open(src, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            base_rows.append(row)

    # Extract feedback corrections
    feedback_rows = extract_feedback_records()

    combined_rows = []
    for r in base_rows:
        combined_rows.append({
            "complaint_text": r["complaint_text"],
            "category": r["category"],
            "department": r["department"],
            "subcategory": r.get("subcategory", "General"),
            "priority": r["priority"],
            "sentiment": r["sentiment"]
        })

    # Append human feedback samples
    for fb in feedback_rows:
        combined_rows.append({
            "complaint_text": fb["complaint_text"],
            "category": fb["category"],
            "department": fb["department"],
            "subcategory": fb.get("subcategory", "General"),
            "priority": fb["priority"],
            "sentiment": fb["sentiment"]
        })

    # Save augmented dataset
    fieldnames = ["complaint_text", "category", "department", "subcategory", "priority", "sentiment"]
    with open(dest, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)

    print(f"Built augmented dataset ({len(combined_rows)} total records, {len(feedback_rows)} human feedback corrections) -> {dest}")
    return dest

if __name__ == "__main__":
    build_augmented_dataset()
