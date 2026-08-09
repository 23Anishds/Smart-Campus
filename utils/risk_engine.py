from typing import List, Dict, Any

def calculate_risk(attendance: float, gpa: float) -> float:
    """
    Calculates a risk score out of 100 based on attendance and GPA.
    Higher score means higher risk.
    """
    # Inverse relationship: low attendance -> high risk
    att_risk = (100 - attendance) * 1.5 
    # Max GPA is typically 4.0. Low GPA -> high risk
    gpa_risk = max(0, (3.0 - gpa) * 20) 
    
    return min(100.0, att_risk + gpa_risk)

def get_at_risk_students(students_data: List[Dict[str, Any]], threshold: float = 40.0) -> List[Dict[str, Any]]:
    """
    Analyzes a list of students and determines their risk scores.
    Demonstrates Lambda, Higher-Order Functions (Concept #9) and 
    List Comprehensions (Concept #5).
    """
    
    # 1. Map: Calculate risk score for everyone using comprehension
    scored_students = [
        {**s, "computed_risk": calculate_risk(s.get("attendance_pct", 100), s.get("gpa", 4.0))}
        for s in students_data
    ]
    
    # 2. Filter: Only keeping students above the risk threshold
    filtered_students = list(filter(lambda s: s["computed_risk"] >= threshold, scored_students))
    
    # 3. Sort: Highest risk first
    sorted_risk = sorted(filtered_students, key=lambda s: s["computed_risk"], reverse=True)
    
    return sorted_risk
