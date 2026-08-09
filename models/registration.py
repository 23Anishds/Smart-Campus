from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class RegistrationDraft:
    """
    Demonstration of Data Classes (Concept #11).
    State model for the 4-step registration wizard.
    """
    id: Optional[int] = None
    reference_id: Optional[str] = None
    step: int = 1
    personal_info: Dict[str, Any] = field(default_factory=dict)
    academic_info: Dict[str, Any] = field(default_factory=dict)
    guardian_info: Dict[str, Any] = field(default_factory=dict)
    status: str = 'draft'
