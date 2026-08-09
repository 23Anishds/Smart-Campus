from dataclasses import dataclass
from typing import Optional

@dataclass
class TimetableSlot:
    """
    Demonstration of Data Classes (Concept #11).
    Represents a specific class period slot.
    """
    id: Optional[int]
    day: str
    period: int
    start_time: str
    end_time: str
    subject: str
    teacher_id: int
    room: str
    section: str

    def has_conflict(self, other: 'TimetableSlot') -> bool:
        """Helper method to determine room/time conflicts."""
        return (
            self.day == other.day and 
            self.period == other.period and 
            self.room == other.room
        )
