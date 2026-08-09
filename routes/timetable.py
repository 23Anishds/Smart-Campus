from flask import Blueprint, render_template, request
from database.connection import DatabaseConnection
from utils.decorators import login_required, api_response
from models.timetable import TimetableSlot

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/timetable')
@login_required
def timetable_page():
    return render_template('timetable.html')

@timetable_bp.route('/api/timetable/weekly')
@login_required
@api_response
def get_weekly():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT t.*, u.full_name as teacher_name 
            FROM timetable t JOIN teachers tc ON t.teacher_id = tc.id
            JOIN users u ON tc.user_id = u.id
            ORDER BY t.day, t.period
        """)
        return [dict(row) for row in cursor.fetchall()]

@timetable_bp.route('/api/timetable/conflicts')
@login_required
@api_response
def check_conflicts():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT * FROM timetable")
        rows = cursor.fetchall()
        
    slots = [TimetableSlot(
        r['id'], r['day'], r['period'], r['start_time'], r['end_time'], 
        r['subject'], r['teacher_id'], r['room'], r['section']
    ) for r in rows]
    
    conflicts = []
    # Simple O(n^2) conflict check for demonstration
    for i, slot1 in enumerate(slots):
        for slot2 in slots[i+1:]:
            if slot1.has_conflict(slot2):
                conflicts.append({
                    "room": slot1.room, "day": slot1.day, "period": slot1.period,
                    "classes": [slot1.subject, slot2.subject]
                })
    return conflicts

@timetable_bp.route('/api/timetable/substitutes/available')
@login_required
@api_response
def get_available_subs():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT tc.id, tc.department, u.full_name, u.email 
            FROM teachers tc JOIN users u ON tc.user_id = u.id
            WHERE tc.is_available = 1
        """)
        return [dict(row) for row in cursor.fetchall()]

@timetable_bp.route('/api/timetable/substitute', methods=['POST'])
@login_required
@api_response
def assign_substitute():
    data = request.json
    slot_id = data.get('slot_id')
    teacher_id = data.get('teacher_id')
    
    with DatabaseConnection() as cursor:
        cursor.execute("UPDATE timetable SET teacher_id = ? WHERE id = ?", (teacher_id, slot_id))
    return {"message": "Substitute assigned successfully"}
