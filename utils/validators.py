import re

class ValidationError(Exception):
    """
    Custom exception for validation errors (Concept #6).
    """
    pass

def validate_email(email: str) -> bool:
    """
    Validates email format using Regular Expressions (Concept #8).
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")
    return True

def validate_phone(phone: str) -> bool:
    """
    Validates phone number format using Regular Expressions (Concept #8).
    Allows optional +, spaces, dashes, and digits.
    """
    pattern = r"^\+?[0-9\s-]+$"
    if not re.match(pattern, phone):
        raise ValidationError(f"Invalid phone format: {phone}")
    return True

def validate_student_id(sid: str) -> bool:
    """
    Validates student ID format (STU-YYYY-NNNN) (Concept #8).
    """
    pattern = r"^STU-\d{4}-\d{4}$"
    if not re.match(pattern, sid):
        raise ValidationError(f"Invalid student ID format. Expected STU-YYYY-NNNN. Got: {sid}")
    return True
