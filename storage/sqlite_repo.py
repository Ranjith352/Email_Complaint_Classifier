import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from config import Config, BASE_DIR
from storage.repository import ComplaintRepository

class SQLiteComplaintRepository(ComplaintRepository):
    """SQLite implementation of ComplaintRepository for reliable zero-configuration local persistence."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = str(db_path)
        else:
            self.db_path = str(BASE_DIR / Config.SQLITE_DB_PATH)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id TEXT PRIMARY KEY,
                    source TEXT DEFAULT 'Web Form',
                    sender_name TEXT,
                    sender_email TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    department TEXT NOT NULL,
                    sub_department TEXT,
                    sentiment TEXT,
                    sentiment_score REAL DEFAULT 0.0,
                    emotion TEXT,
                    urgency TEXT,
                    priority TEXT,
                    confidence REAL DEFAULT 0.0,
                    confidence_percent INTEGER DEFAULT 0,
                    review_required INTEGER DEFAULT 0,
                    entities TEXT DEFAULT '{}',
                    recommended_action TEXT,
                    routing_path TEXT,
                    assigned_agent TEXT,
                    sla_hours INTEGER DEFAULT 24,
                    sla_deadline TEXT,
                    sla_status TEXT DEFAULT 'Active',
                    is_duplicate INTEGER DEFAULT 0,
                    duplicate_of_id TEXT,
                    duplicate_similarity REAL DEFAULT 0.0,
                    ai_response_draft TEXT,
                    status TEXT DEFAULT 'Open',
                    resolution_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    notification_sent INTEGER DEFAULT 0
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_department ON complaints(department)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON complaints(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON complaints(priority)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON complaints(created_at)")
            conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        d["review_required"] = bool(d.get("review_required"))
        d["is_duplicate"] = bool(d.get("is_duplicate"))
        d["notification_sent"] = bool(d.get("notification_sent"))
        if isinstance(d.get("entities"), str):
            try:
                d["entities"] = json.loads(d["entities"])
            except Exception:
                d["entities"] = {}
        return d

    def get_all(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM complaints ORDER BY datetime(created_at) DESC LIMIT ?",
                (limit,)
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def get_next_id(self) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM complaints")
            count = cursor.fetchone()[0]
            return f"CMP-{10001 + count}"

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data.get("id"):
            data["id"] = self.get_next_id()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["created_at"] = data.get("created_at") or now
        data["updated_at"] = now

        entities_json = json.dumps(data.get("entities") or {}) if isinstance(data.get("entities"), dict) else (data.get("entities") or "{}")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO complaints (
                    id, source, sender_name, sender_email, title, description,
                    category, department, sub_department, sentiment, sentiment_score,
                    emotion, urgency, priority, confidence, confidence_percent,
                    review_required, entities, recommended_action, routing_path,
                    assigned_agent, sla_hours, sla_deadline, sla_status,
                    is_duplicate, duplicate_of_id, duplicate_similarity,
                    ai_response_draft, status, resolution_notes, created_at,
                    updated_at, notification_sent
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?
                )
            """, (
                data.get("id"),
                data.get("source", "Web Form"),
                data.get("sender_name", ""),
                data.get("sender_email", ""),
                data.get("title", "Untitled Complaint"),
                data.get("description", ""),
                data.get("category", "General Inquiry"),
                data.get("department", "Support"),
                data.get("sub_department", ""),
                data.get("sentiment", "Neutral"),
                float(data.get("sentiment_score", 0.0)),
                data.get("emotion", "Neutral"),
                data.get("urgency", "Medium"),
                data.get("priority", "Medium"),
                float(data.get("confidence", 0.85)),
                int(data.get("confidence_percent", 85)),
                1 if data.get("review_required") else 0,
                entities_json,
                data.get("recommended_action", ""),
                data.get("routing_path", ""),
                data.get("assigned_agent", "Unassigned"),
                int(data.get("sla_hours", 24)),
                data.get("sla_deadline", ""),
                data.get("sla_status", "Active"),
                1 if data.get("is_duplicate") else 0,
                data.get("duplicate_of_id"),
                float(data.get("duplicate_similarity", 0.0)),
                data.get("ai_response_draft", ""),
                data.get("status", "Open"),
                data.get("resolution_notes", ""),
                data.get("created_at"),
                data.get("updated_at"),
                1 if data.get("notification_sent") else 0
            ))
            conn.commit()

        return self.get_by_id(data["id"])

    def update(self, complaint_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fields = []
        values = []
        for k, v in updates.items():
            if k in ("entities",) and isinstance(v, dict):
                v = json.dumps(v)
            elif k in ("review_required", "is_duplicate", "notification_sent") and isinstance(v, bool):
                v = 1 if v else 0
            fields.append(f"{k} = ?")
            values.append(v)

        values.append(complaint_id)
        sql = f"UPDATE complaints SET {', '.join(fields)} WHERE id = ?"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(values))
            conn.commit()

        return self.get_by_id(complaint_id)

    def filter(self, search: str = "", department: str = "", urgency: str = "",
               category: str = "", status: str = "", priority: str = "",
               review_required: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM complaints WHERE 1=1"
        params = []

        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR sender_name LIKE ? OR sender_email LIKE ? OR id LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term, term])

        if department:
            query += " AND department LIKE ?"
            params.append(f"%{department}%")

        if urgency:
            query += " AND urgency = ?"
            params.append(urgency)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        if category:
            query += " AND category LIKE ?"
            params.append(f"%{category}%")

        if status:
            query += " AND status = ?"
            params.append(status)

        if review_required is not None:
            query += " AND review_required = ?"
            params.append(1 if review_required else 0)

        query += " ORDER BY datetime(created_at) DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return [self._row_to_dict(row) for row in cursor.fetchall()]

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
        breached_cases = [c for c in complaints if c.get("sla_status") == "Breached" or (c.get("status") != "Resolved" and c.get("sla_deadline") and c.get("sla_deadline") < datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]

        high_percentage = round((len(high_urgency) / total * 100), 1)
        resolution_rate = round((len(resolved_cases) / total * 100), 1)
        avg_conf = round(sum(c.get("confidence_percent", 80) for c in complaints) / total)

        if high_percentage > 35 or len(breached_cases) >= 3:
            risk = "Critical"
        elif high_percentage > 15 or len(breached_cases) >= 1:
            risk = "Warning"
        else:
            risk = "Stable"

        cat_counts = {}
        for c in complaints:
            cat = c.get("category", "Other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        top_cat = max(cat_counts.items(), key=lambda x: x[1])[0] if cat_counts else "None"

        dept_counts = {}
        for c in complaints:
            dept = c.get("department", "Support")
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # Trend calculation
        date_counts = {}
        for c in complaints:
            dt = str(c.get("created_at", ""))[:10]
            if dt:
                date_counts[dt] = date_counts.get(dt, 0) + 1

        sorted_dates = sorted(date_counts.keys())[-7:]
        trend_dates = sorted_dates
        trend_values = [date_counts[d] for d in sorted_dates]

        return {
            "total": total,
            "open_count": len(open_cases),
            "resolved_count": len(resolved_cases),
            "review_count": len(review_cases),
            "high_urgency_count": len(high_urgency),
            "high_percentage": high_percentage,
            "resolution_rate": resolution_rate,
            "risk_level": risk,
            "top_category": top_cat,
            "avg_confidence": avg_conf,
            "categories": cat_counts,
            "departments": dept_counts,
            "sla_breached": len(breached_cases),
            "trend_dates": trend_dates,
            "trend_values": trend_values
        }
