from flask import Blueprint, render_template, request
from database.connection import DatabaseConnection
from utils.decorators import login_required, api_response

students_bp = Blueprint('students', __name__)

@students_bp.route('/api/students')
@login_required
@api_response
def list_students():
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.id, u.full_name, s.student_id, s.grade, s.section, s.gpa, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        return [dict(row) for row in cursor.fetchall()]

@students_bp.route('/api/students/<int:id>/profile')
@login_required
def student_profile_page(id):
    # This renders the Stitch Profile HTML
    return render_template('student_profile.html', student_id=id)

@students_bp.route('/api/students/<int:id>')
@login_required
@api_response
def get_student(id):
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.*, u.full_name, u.email 
            FROM students s JOIN users u ON s.user_id = u.id 
            WHERE s.id = ?
        """, (id,))
        student = cursor.fetchone()
        if not student:
            return {"error": "Student not found"}, 404
        return dict(student)

@students_bp.route('/api/students/search')
@login_required
@api_response
def search():
    query = request.args.get('q', '').lower()
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.id, u.full_name, s.student_id, s.grade
            FROM students s JOIN users u ON s.user_id = u.id
        """)
        all_students = [dict(row) for row in cursor.fetchall()]
        
    # Comprehension for search (Concept #5)
    matched = [s for s in all_students if query in s['full_name'].lower() or query in s['student_id'].lower()]
    return matched
