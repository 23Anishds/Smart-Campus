from flask import Blueprint, render_template
from database.connection import DatabaseConnection
from utils.decorators import login_required, role_required, api_response
from utils.risk_engine import get_at_risk_students
import random

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
@role_required('teacher')
def analytics_page():
    return render_template('analytics.html')

@analytics_bp.route('/api/analytics/class-performance')
@login_required
@api_response
def class_performance():
    # Mock data for Class vs Student Avg
    labels = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]
    class_avg = [78, 80, 82, 79, 81, 85]
    student_avg = [85, 86, 88, 85, 87, 90]
    return {"labels": labels, "class_avg": class_avg, "student_avg": student_avg}

@analytics_bp.route('/api/analytics/engagement')
@login_required
@api_response
def engagement_scatter():
    # Mock scatter plot data points {x: attendance, y: score}
    points = [{"x": random.uniform(60, 100), "y": random.uniform(50, 100)} for _ in range(30)]
    return points

@analytics_bp.route('/api/analytics/risk-radar')
@login_required
@api_response
def risk_radar():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.id, u.full_name, s.gpa, s.attendance_pct, s.risk_score 
            FROM students s 
            JOIN users u ON s.user_id = u.id
        """)
        students = [dict(row) for row in cursor.fetchall()]
        
    at_risk = get_at_risk_students(students)
    return at_risk[:5] # Return top 5

@analytics_bp.route('/api/analytics/insights')
@login_required
@api_response
def insights():
    return {
        "insight_text": "Class 10B shows a 23% drop in Math scores over 3 weeks. Possible cause: Chapter 5 concept gap detected."
    }
