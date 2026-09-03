import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from storage.repository import ComplaintRepository
from firebase_config import db

class FirebaseComplaintRepository(ComplaintRepository):
    """Firestore implementation of ComplaintRepository for cloud persistence."""

    def __init__(self):
        if not db:
            raise RuntimeError("Firebase is not initialized. Check your FIREBASE_KEY_PATH in .env")
        self.collection = db.collection("complaints")

    def get_all(self, limit: int = 200) -> List[Dict[str, Any]]:
        docs = self.collection.order_by("created_at", direction="DESCENDING").limit(limit).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results

    def get_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.document(complaint_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def create(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        cid = complaint_data.get("id") or f"CMP-{int(datetime.now().timestamp())}"
        complaint_data["id"] = cid
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        complaint_data["created_at"] = complaint_data.get("created_at") or now
        complaint_data["updated_at"] = now
        self.collection.document(cid).set(complaint_data)
        return complaint_data

    def update(self, complaint_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.collection.document(complaint_id).update(updates)
        return self.get_by_id(complaint_id)

    def filter(self, search: str = "", department: str = "", urgency: str = "",
               category: str = "", status: str = "", priority: str = "",
               review_required: Optional[bool] = None) -> List[Dict[str, Any]]:
        all_docs = self.get_all(limit=500)
        filtered = []
        for c in all_docs:
            if search:
                s = search.lower()
                if (s not in c.get("title", "").lower() and
                    s not in c.get("description", "").lower() and
                    s not in c.get("sender_name", "").lower() and
                    s not in c.get("id", "").lower()):
                    continue
            if department and department.lower() not in c.get("department", "").lower():
                continue
            if urgency and c.get("urgency") != urgency:
                continue
            if priority and c.get("priority") != priority:
                continue
            if category and category.lower() not in c.get("category", "").lower():
                continue
            if status and c.get("status") != status:
                continue
            if review_required is not None and bool(c.get("review_required")) != review_required:
                continue
            filtered.append(c)
        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        complaints = self.get_all(limit=1000)
        total = len(complaints)
        if total == 0:
            return {
                "total": 0, "open_count": 0, "resolved_count": 0, "review_count": 0,
                "high_urgency_count": 0, "high_percentage": 0.0, "resolution_rate": 0.0,
                "risk_level": "Stable", "top_category": "None", "avg_confidence": 0,
                "categories": {}, "departments": {}, "sla_breached": 0,
                "trend_dates": [], "trend_values": []
            }
        open_cases = [c for c in complaints if c.get("status") in ("Open", "In Review", "In Progress")]
        resolved_cases = [c for c in complaints if c.get("status") == "Resolved"]
        review_cases = [c for c in complaints if c.get("review_required") and c.get("status") != "Resolved"]
        high_urgency = [c for c in complaints if c.get("urgency") in ("High", "Critical")]

        cat_counts = {}
        for c in complaints:
            cat = c.get("category", "Other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        top_cat = max(cat_counts.items(), key=lambda x: x[1])[0] if cat_counts else "None"

        dept_counts = {}
        for c in complaints:
            dept = c.get("department", "Support")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        return {
            "total": total,
            "open_count": len(open_cases),
            "resolved_count": len(resolved_cases),
            "review_count": len(review_cases),
            "high_urgency_count": len(high_urgency),
            "high_percentage": round(len(high_urgency) / total * 100, 1),
            "resolution_rate": round(len(resolved_cases) / total * 100, 1),
            "risk_level": "Critical" if (len(high_urgency) / total > 0.35) else "Stable",
            "top_category": top_cat,
            "avg_confidence": 85,
            "categories": cat_counts,
            "departments": dept_counts,
            "sla_breached": 0,
            "trend_dates": [],
            "trend_values": []
        }
