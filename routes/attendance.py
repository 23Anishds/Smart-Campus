from flask import Blueprint, render_template, request, current_app
from database.connection import DatabaseConnection
from utils.decorators import login_required, role_required, api_response
from utils.qr_manager import QRManager
import os

attendance_bp = Blueprint('attendance', __name__)

qr_manager = None

def get_qr_manager():
    global qr_manager
    if qr_manager is None:
        output_dir = os.path.join(current_app.static_folder, 'qr_codes')
        from config import AppConfig
        qr_manager = QRManager(output_dir, expiry_seconds=AppConfig.get_config().QR_EXPIRY_SECONDS)
    return qr_manager

@attendance_bp.route('/attendance')
@login_required
@role_required('teacher')
def attendance_page():
    return render_template('attendance.html')

@attendance_bp.route('/api/attendance/qr/generate', methods=['POST'])
@login_required
@api_response
def generate_qr():
    data = request.json or {}
    class_id = data.get('class_id', 'general')
    manager = get_qr_manager()
    filename = manager.generate_qr(class_id)
    return {
        "qr_image_url": f"/static/qr_codes/{filename}",
        "expires_in": manager.expiry_seconds
    }

@attendance_bp.route('/api/attendance/qr/validate', methods=['POST'])
@login_required
@api_response
def validate_qr():
    data = request.json or {}
    code = data.get('code')
    manager = get_qr_manager()
    
    if manager.validate_code(code):
        # In real app, verify geofence here
        # Log attendance
        with DatabaseConnection() as cursor:
             # get student id for logged in user
             # user_id -> student_id
             # For mockup, we just return success
             pass
        return {"validated": True, "message": "Attendance marked successfully"}
    return {"validated": False, "error": "Invalid or expired code"}, 400

@attendance_bp.route('/api/attendance/mark', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def mark_attendance():
    data = request.json
    student_id = data.get('student_id')
    status = data.get('status')
    
    with DatabaseConnection() as cursor:
        cursor.execute(
            "INSERT INTO attendance (student_id, class_name, date, period, status, marked_by) VALUES (?, ?, date('now'), ?, ?, ?)",
            (student_id, "Advanced Physics", 1, status, 'manual')
        )
    return {"message": "Updated"}

@attendance_bp.route('/api/attendance/roster/<class_id>')
@login_required
@api_response
def get_roster(class_id):
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.id, u.full_name, a.status 
            FROM students s 
            JOIN users u ON s.user_id = u.id
            LEFT JOIN (SELECT * FROM attendance WHERE date = date('now') ORDER BY timestamp DESC) a ON s.id = a.student_id
            GROUP BY s.id
        """)
        return [dict(row) for row in cursor.fetchall()]
        
@attendance_bp.route('/api/attendance/recent')
@login_required
@api_response
def recent_scans():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT a.timestamp, u.full_name, a.status, a.marked_by
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN users u ON s.user_id = u.id
            ORDER BY a.timestamp DESC LIMIT 5
        """)
        return [dict(row) for row in cursor.fetchall()]
