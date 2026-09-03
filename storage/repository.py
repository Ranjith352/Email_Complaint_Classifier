from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ComplaintRepository(ABC):
    """Abstract storage interface for complaints management."""

    @abstractmethod
    def get_all(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Retrieve all complaints, ordered by created_at descending."""
        pass

    @abstractmethod
    def get_by_id(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific complaint by its ID."""
        pass

    @abstractmethod
    def create(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new complaint and return the created record."""
        pass

    @abstractmethod
    def update(self, complaint_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields of an existing complaint."""
        pass

    @abstractmethod
    def filter(self, **kwargs) -> List[Dict[str, Any]]:
        """Filter complaints by parameters (department, status, urgency, priority, search)."""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Aggregate high-level metrics for executive dashboard and analytics."""
        pass
