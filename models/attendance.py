from dataclasses import dataclass
from typing import Optional

@dataclass
class AttendanceRecord:
    """
    Demonstration of Data Classes (Concept #11).
    Represents a single attendance event.
    """
    id: Optional[int]
    student_id: int
    class_name: str
    date: str
    period: int
    status: str  # 'present', 'absent', 'late'
    marked_by: str # 'qr' or 'manual'
    timestamp: Optional[str] = None
