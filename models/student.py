from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .base import User

@dataclass
class StudentProfile:
    """
    Demonstration of Data Classes (Concept #11).
    Structured way to hold student specific data.
    """
    student_id: str
    grade: str
    section: str
    gpa: float = 0.0
    attendance_pct: float = 100.0
    class_rank: Optional[int] = None
    risk_score: float = 0.0
    parent_name: str = ""
    parent_phone: str = ""
    parent_email: str = ""
    status: str = "active"

class Student(User):
    """
    Student class inheriting from User (Concept #1).
    """
    def __init__(
        self, 
        id: int, 
        username: str, 
        full_name: str, 
        email: str, 
        profile: StudentProfile
    ):
        super().__init__(id, username, full_name, email, role="student")
        self.profile = profile

    def to_dict(self) -> Dict[str, Any]:
        """Override base dictionary representation to include profile."""
        base_dict = super().to_dict()
        profile_dict = {
            k: v for k, v in self.profile.__dict__.items()
        }
        return {**base_dict, **profile_dict}

    def update_risk_score(self, new_score: float) -> None:
        """Encapsulated method to modify internal state safely."""
        self.profile.risk_score = min(max(new_score, 0.0), 100.0)
