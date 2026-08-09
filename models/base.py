from typing import Any, Dict, Optional
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    """
    Base User class showcasing OOP inheritance and encapsulation (Concept #1).
    All methods use Type Hinting (Concept #12).
    """
    def __init__(self, id: int, username: str, full_name: str, email: str, role: str):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.role = role
        self._password_hash = "" # Protected attribute

    def set_password(self, password: str) -> None:
        self._password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self._password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.username}>"
