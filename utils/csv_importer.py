import csv
import io
from typing import Generator, Dict, Any, List, Tuple
from .validators import validate_email, validate_phone, validate_student_id, ValidationError

class CSVImportError(Exception):
    """Custom exception for CSV import failures (Concept #6)."""
    pass

def read_csv_in_chunks(file_obj: io.TextIOWrapper) -> Generator[Dict[str, str], None, None]:
    """
    Reads a CSV file row by row and yields dictionaries (Concept #3 - Generators).
    Helps with memory efficiency for large file imports (Concept #7 - File I/O).
    """
    reader = csv.DictReader(file_obj)
    for row in reader:
        yield row

def validate_and_parse_student_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Validates a single row from the CSV (Concept #8 - Regex via validators, Concept #6 - Exceptions).
    """
    try:
        # Mandatory fields
        student_id = row.get('Student ID', '').strip()
        validate_student_id(student_id)
        
        name = row.get('Name', '').strip()
        if not name:
            raise ValidationError("Name cannot be empty")
            
        email = row.get('Email', '').strip()
        validate_email(email)
        
        parent_phone = row.get('Parent Phone', '').strip()
        if parent_phone:
           validate_phone(parent_phone)
           
        return {
            "student_id": student_id,
            "name": name,
            "email": email,
            "grade": row.get('Grade', '').strip(),
            "section": row.get('Section', '').strip(),
            "parent_phone": parent_phone
        }
    except ValidationError as e:
        raise CSVImportError(f"Validation failed: {str(e)}")
    except Exception as e:
        raise CSVImportError(f"Unexpected error parsing row: {str(e)}")

def process_bulk_import(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Main entry point for processing a CSV file upload.
    Returns (success_list, error_list)
    """
    successes = []
    errors = []
    
    try:
        # File I/O (Concept #7)
        text_stream = io.TextIOWrapper(io.BytesIO(file_content), encoding='utf-8-sig')
        
        # Generator usage (Concept #3)
        row_generator = read_csv_in_chunks(text_stream)
        
        for idx, row in enumerate(row_generator, start=2): # Start 2 for header + 1-indexed
            try:
                parsed_data = validate_and_parse_student_row(row)
                successes.append(parsed_data)
            except CSVImportError as e:
                errors.append({
                    "row": idx,
                    "data": row,
                    "error": str(e)
                })
    except Exception as e:
        # Catch file parsing issues (e.g. not a proper CSV)
        errors.append({"row": 0, "error": f"Failed to read file format: {str(e)}"})
        
    return successes, errors
