from typing import List, Dict, Any
from .base import User

class Teacher(User):
    """
    Teacher class inheriting from User (Concept #1).
    """
    def __init__(
        self, 
        id: int, 
        username: str, 
        full_name: str, 
        email: str,
        department: str,
        subjects: List[str],
        is_available: bool = True
    ):
        super().__init__(id, username, full_name, email, role="teacher")
        self.department = department
        self.subjects = subjects
        self.is_available = is_available

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        return {
            **base_dict,
            "department": self.department,
            "subjects": self.subjects,
            "is_available": self.is_available
        }
