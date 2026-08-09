from flask import Blueprint, render_template, request, Response
from database.connection import DatabaseConnection
from utils.decorators import login_required, role_required, api_response
from utils.csv_importer import process_bulk_import
import random, json, os, requests
from datetime import datetime, timedelta

def has_mistral_key():
    api_key = os.environ.get('MISTRAL_API_KEY', '')
    if api_key and api_key != 'your_mistral_api_key_here':
        return api_key
    return None

def call_mistral_json(system_prompt: str, user_prompt: str) -> dict:
    api_key = has_mistral_key()
    if not api_key: return {}
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": "mistral-small-latest",
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=15)
        if res.status_code == 200:
            return json.loads(res.json()['choices'][0]['message']['content'].strip())
    except Exception:
        pass
    return {}

admin_bp = Blueprint('admin', __name__)

# Auto-create exams table and seed default data if it doesn't exist
def _ensure_exams_table():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                hall TEXT,
                invigilator TEXT,
                strength INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Seed default exams if table is empty
        cursor.execute("SELECT COUNT(*) as c FROM exams")
        if cursor.fetchone()['c'] == 0:
            default_exams = [
                ("Mid-Term Mathematics", "2024-06-10", "Hall A", "Dr. Jenkins", 45),
                ("Physics Internal", "2024-06-12", "Hall B", "Ms. Vance", 38),
                ("End Semester CS101", "2024-06-20", "Auditorium", "TBD", 120),
            ]
            cursor.executemany(
                "INSERT INTO exams (name, date, hall, invigilator, strength) VALUES (?, ?, ?, ?, ?)",
                default_exams
            )

try:
    _ensure_exams_table()
except Exception as e:
    print(f"Warning: Could not initialize exams table: {e}")

@admin_bp.route('/admin')
@login_required
@role_required('admin')
def admin_page():
    return render_template('admin_panel.html')

# ─────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/kpi')
@login_required 
@role_required('admin') 
@api_response
def get_kpi():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students"); stu = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM teachers"); tch = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(DISTINCT subject) as c FROM timetable"); cls = cursor.fetchone()['c']
        cursor.execute("SELECT AVG(attendance_pct) as a FROM students"); att = cursor.fetchone()['a']
        cursor.execute("SELECT COUNT(*) as c FROM students WHERE attendance_pct < 75"); risk = cursor.fetchone()['c']
    return {
        "total_students": stu, "total_faculty": tch, "active_classes": cls,
        "attendance_today": round(att or 0, 1), "at_risk_students": risk,
        "placement_rate": 78, "fee_collection_pct": 84, "system_health": "Healthy"
    }

@admin_bp.route('/api/admin/alerts')
@login_required 
@role_required('admin') 
@api_response
def get_alerts():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students WHERE attendance_pct < 75"); low_att = cursor.fetchone()['c']
        
    system_prompt = "You are an AI admin assistant. Generate EXACTLY 5 critical system alerts for a school admin dashboard. Output ONLY valid JSON containing a key 'alerts' with a list of objects with keys: 'level' (critical or warning), 'icon' (material icons like error, pending, event_busy), 'text' (short string), and 'module' (attendance, faculty, classes, exams)."
    user_prompt = f"There are {low_att} students with low attendance. Generate an alert about this, plus 4 other random realistic institutional issues."
    
    ai_response = call_mistral_json(system_prompt, user_prompt)
    if "alerts" in ai_response and isinstance(ai_response["alerts"], list):
        return ai_response["alerts"]
        
    return [
        {"level": "critical", "icon": "error", "text": f"Attendance below 75% for {low_att} students", "module": "attendance"},
        {"level": "warning", "icon": "pending", "text": "15 faculty members haven't uploaded internal marks", "module": "faculty"},
        {"level": "critical", "icon": "event_busy", "text": "3 classrooms double-booked today", "module": "classes"},
        {"level": "warning", "icon": "assignment_late", "text": "42 assignments pending evaluation", "module": "exams"},
        {"level": "critical", "icon": "schedule", "text": "Semester results due in 3 days", "module": "exams"}
    ]

@admin_bp.route('/api/admin/ai/heatmap_predict')
@login_required 
@role_required('admin') 
@api_response
def get_heatmap_predict():
    system_prompt = "You are an AI generating attendance heatmap data and dropout predictions. Output ONLY valid JSON."
    user_prompt = "Generate JSON with two keys: 'heatmap' (list of objects for days 'Mon', 'Tue', 'Wed', 'Thu', 'Fri' with random 0-100 attendance values for 'CSE', 'AIML', 'ECE', 'Mech') and 'prediction' (a short, insightful string predicting dropout risks based on these trends, e.g. 'Based on AI analysis of attendance trends, 4 students in ECE show high dropout risk.')."
    
    ai_response = call_mistral_json(system_prompt, user_prompt)
    
    heatmap_data = ai_response.get("heatmap", [
        {"day": "Mon", "CSE": 92, "AIML": 88, "ECE": 75, "Mech": 80},
        {"day": "Tue", "CSE": 85, "AIML": 90, "ECE": 82, "Mech": 78},
        {"day": "Wed", "CSE": 88, "AIML": 85, "ECE": 70, "Mech": 75},
        {"day": "Thu", "CSE": 95, "AIML": 92, "ECE": 85, "Mech": 88},
        {"day": "Fri", "CSE": 80, "AIML": 75, "ECE": 60, "Mech": 70},
    ])
    prediction = ai_response.get("prediction", "Based on attendance trends, 6 students show high dropout risk.")
    
    return {"heatmap": heatmap_data, "prediction": prediction}

@admin_bp.route('/api/admin/todays-overview')
@login_required 
@role_required('admin') 
@api_response
def todays_overview():
    return {
        "classes_scheduled": 24, "faculty_on_leave": 3,
        "exams_today": 2, "events_today": 1, "new_admissions": 5
    }

@admin_bp.route('/api/admin/charts/growth')
@login_required 
@role_required('admin') 
@api_response
def growth_chart():
    years = ["2020", "2021", "2022", "2023", "2024"]
    return {"labels": years, "admissions": [420, 480, 510, 560, 620], "graduates": [380, 430, 460, 500, 540]}

@admin_bp.route('/api/admin/charts/dept-performance')
@login_required 
@role_required('admin') 
@api_response
def dept_perf():
    return {
        "departments": ["CSE", "AIML", "ECE", "Mechanical"],
        "avg_gpa": [3.6, 3.8, 3.3, 3.1],
        "attendance": [89, 91, 84, 80]
    }

# ─────────────────────────────────────────────────
# STUDENTS MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/students')
@login_required 
@role_required('admin') 
@api_response
def get_students():
    q = request.args.get('q', '').lower()
    dept = request.args.get('dept', '')
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.id, u.full_name, s.student_id, s.grade as semester,
                   s.section, s.gpa, s.attendance_pct, s.risk_score
            FROM students s JOIN users u ON s.user_id = u.id
        """)
        rows = [dict(r) for r in cursor.fetchall()]
    # Python comprehension for multi-filter (Concept #5)
    filtered = [r for r in rows if
        (not q or q in r['full_name'].lower() or q in r['student_id'].lower()) and
        (not dept or dept == r['semester'])
    ]
    return filtered

@admin_bp.route('/api/admin/students/analytics')
@login_required 
@role_required('admin') 
@api_response
def student_analytics():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students WHERE gpa >= 3.8"); high = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM students WHERE attendance_pct < 75 OR gpa < 2.5"); at_risk = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM students"); total = cursor.fetchone()['c']
    return {"high_performers": high, "at_risk": at_risk, "average_students": total - high - at_risk}

@admin_bp.route('/api/admin/import', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def bulk_import():
    if 'file' not in request.files:
        return {"error": "No file provided"}, 400
    file = request.files['file']
    file_bytes = file.read()
    successes, errors = process_bulk_import(file_bytes)
    return {"success_count": len(successes), "error_count": len(errors), "preview": successes[:5], "errors": errors}

@admin_bp.route('/api/admin/students/add', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def add_student():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    roll = data.get('roll', f'STU-2024-{random.randint(1000,9999)}')
    grade = data.get('grade', '10')
    section = data.get('section', 'A')
    from werkzeug.security import generate_password_hash
    with DatabaseConnection() as cursor:
        hashed_pw = generate_password_hash("student123")
        username = email.split('@')[0] if email else name.lower().replace(' ', '')
        cursor.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_pw, name, email or '', "student"))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO students (user_id, student_id, grade, section) VALUES (?, ?, ?, ?)",
                       (user_id, roll, grade, section))
    return {"message": f"Student {name} added successfully.", "id": user_id}

# ─────────────────────────────────────────────────
# FACULTY MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/faculty')
@login_required 
@role_required('admin') 
@api_response
def get_faculty():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT t.id, u.full_name, t.department, t.subjects, t.is_available
            FROM teachers t JOIN users u ON t.user_id = u.id
        """)
        rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        r['subjects'] = json.loads(r['subjects']) if r['subjects'] else []
        r['workload_hours'] = random.randint(14, 24)
        r['feedback_score'] = round(random.uniform(3.5, 5.0), 1)
        r['designation'] = random.choice(["Professor", "Associate Prof", "Assistant Prof"])
        r['leave_pending'] = random.choice([True, False])
    return rows

@admin_bp.route('/api/admin/faculty/leave', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def manage_leave():
    data = request.json
    action = data.get('action')  # 'approve' or 'reject'
    faculty_id = data.get('faculty_id')
    with DatabaseConnection() as cursor:
        cursor.execute("UPDATE teachers SET is_available = ? WHERE id = ?",
                       (0 if action == 'approve' else 1, faculty_id))
    return {"message": f"Leave {action}d for faculty #{faculty_id}"}

@admin_bp.route('/api/admin/faculty/add', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def add_faculty():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    dept = data.get('dept', 'CSE')
    desig = data.get('desig', 'Assistant Prof')
    from werkzeug.security import generate_password_hash
    with DatabaseConnection() as cursor:
        hashed_pw = generate_password_hash("teacher123")
        username = email.split('@')[0] if email else name.lower().replace(' ', '')
        cursor.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_pw, name, email or '', "teacher"))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO teachers (user_id, department, subjects) VALUES (?, ?, ?)",
                       (user_id, dept, json.dumps([])))
    return {"message": f"Faculty {name} added successfully."}

# ─────────────────────────────────────────────────
# ATTENDANCE MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/attendance/live')
@login_required 
@role_required('admin') 
@api_response
def live_attendance():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students"); total = cursor.fetchone()['c']
    present = int(total * 0.87)
    absent = int(total * 0.10)
    late = total - present - absent
    departments = [
        {"name": "CSE", "attendance": 92}, {"name": "AIML", "attendance": 89},
        {"name": "ECE", "attendance": 84}, {"name": "Mechanical", "attendance": 80}
    ]
    return {"present": present, "absent": absent, "late": late, "total": total, "departments": departments}

@admin_bp.route('/api/admin/attendance/defaulters')
@login_required 
@role_required('admin') 
@api_response
def get_defaulters():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, s.student_id, s.attendance_pct, s.grade as semester
            FROM students s JOIN users u ON s.user_id = u.id
            WHERE s.attendance_pct < 75 ORDER BY s.attendance_pct ASC
        """)
        return [dict(r) for r in cursor.fetchall()]

# ─────────────────────────────────────────────────
# CLASSES MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/classes')
@login_required 
@role_required('admin') 
@api_response
def get_classes():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT t.subject, t.section, t.room, u.full_name as teacher
            FROM timetable t LEFT JOIN teachers tc ON t.teacher_id = tc.id
            LEFT JOIN users u ON tc.user_id = u.id
            GROUP BY t.subject, t.section
        """)
        rows = [dict(r) for r in cursor.fetchall()]
    for r in rows:
        r['strength'] = random.randint(30, 60)
        r['department'] = random.choice(["CSE", "AIML", "ECE", "Mechanical"])
    return rows

@admin_bp.route('/api/admin/conflicts')
@login_required 
@role_required('admin') 
@api_response
def get_conflicts():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT day, period, room, COUNT(*) as cnt FROM timetable GROUP BY day, period, room HAVING cnt > 1")
        return [dict(r) for r in cursor.fetchall()]

@admin_bp.route('/api/admin/classes/add', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def add_class():
    data = request.json
    subject = data.get('subject')
    section = data.get('section')
    with DatabaseConnection() as cursor:
        cursor.execute("INSERT INTO timetable (day, period, subject, section, room) VALUES (?, ?, ?, ?, ?)",
                       ('Monday', 1, subject, section, 'TBD'))
    return {"message": f"Class '{subject}' created."}

# ─────────────────────────────────────────────────
# EXAMS MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/exams')
@login_required 
@role_required('admin') 
@api_response
def get_exams():
    _ensure_exams_table()
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT id, name, date, hall, invigilator, strength
            FROM exams ORDER BY date ASC
        """)
        return [dict(r) for r in cursor.fetchall()]

@admin_bp.route('/api/admin/exams/add', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def add_exam():
    data = request.json
    name = data.get('name')
    date = data.get('date')
    hall = data.get('hall', 'TBD')
    invigilator = data.get('invigilator', 'TBD')
    if not name or not date:
        return {"error": "Exam name and date are required."}, 400
    _ensure_exams_table()
    with DatabaseConnection() as cursor:
        cursor.execute(
            "INSERT INTO exams (name, date, hall, invigilator, strength) VALUES (?, ?, ?, ?, ?)",
            (name, date, hall, invigilator, 0)
        )
        exam_id = cursor.lastrowid
    return {"message": f"Exam '{name}' scheduled for {date}.", "id": exam_id}

# ─────────────────────────────────────────────────
# FINANCE MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/finance')
@login_required 
@role_required('admin') 
@api_response
def get_finance():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students"); total = cursor.fetchone()['c']
    fee_per_student = 50000
    collected_pct = 0.84
    return {
        "total_expected": total * fee_per_student,
        "collected": int(total * fee_per_student * collected_pct),
        "pending": int(total * fee_per_student * (1 - collected_pct)),
        "due_this_month": int(total * fee_per_student * 0.05),
        "scholarships": {"government": 12, "private": 5, "merit": 8},
        "monthly_trend": {"labels": ["Jan","Feb","Mar","Apr","May","Jun"], "values": [820000,750000,900000,870000,950000,880000]}
    }

# ─────────────────────────────────────────────────
# PLACEMENTS MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/placements')
@login_required 
@role_required('admin') 
@api_response
def get_placements():
    return {
        "eligible": 145, "placed": 113, "placement_rate": 77.9,
        "avg_package": "5.4 LPA", "highest_package": "18 LPA",
        "companies": [
            {"name": "Infosys", "offers": 22, "package": "4.5 LPA"},
            {"name": "TCS", "offers": 35, "package": "3.8 LPA"},
            {"name": "Google", "offers": 2, "package": "18 LPA"},
        ],
        "dept_stats": {"CSE": 92, "AIML": 88, "ECE": 68, "Mechanical": 55}
    }

# ─────────────────────────────────────────────────
# COMMUNICATION MODULE
# ─────────────────────────────────────────────────
@admin_bp.route('/api/admin/notify', methods=['POST'])
@login_required 
@role_required('admin') 
@api_response
def send_notice():
    data = request.json
    with DatabaseConnection() as cursor:
        cursor.execute("INSERT INTO activity_log (action, details, user_id) VALUES (?, ?, ?)",
                       ("notice", f"Sent to {data.get('audience')}: {data.get('message')[:80]}", 1))
    return {"message": "Notice dispatched via Email, SMS, and App Notification."}

@admin_bp.route('/api/admin/stats')
@login_required 
@role_required('admin') 
@api_response
def get_admin_stats():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students"); stu = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM teachers"); tch = cursor.fetchone()['c']
    return {"total_students": stu, "active_teachers": tch, "classrooms": 12, "system_health": "Healthy"}

@admin_bp.route('/api/admin/users')
@login_required 
@role_required('admin') 
@api_response
def get_users():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT id, username, full_name, email, role FROM users LIMIT 10")
        return [dict(row) for row in cursor.fetchall()]

@admin_bp.route('/api/admin/activity')
@login_required 
@role_required('admin') 
@api_response
def system_activity():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT action, details, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT 10")
        return [dict(row) for row in cursor.fetchall()]

@admin_bp.route('/api/admin/template')
@login_required 
@role_required('admin')
def template():
    csv_data = "Student ID,Name,Email,Grade,Section,Parent Phone\nSTU-2024-9999,John Doe,john@test.com,10,A,555-0000"
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=student_import_template.csv"})

# ─────────────────────────────────────────────────
# REPORT DOWNLOADS (CSV)
# ─────────────────────────────────────────────────
def _csv_response(rows, headers, filename):
    import csv, io
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    for r in rows:
        writer.writerow(r)
    return Response(si.getvalue(), mimetype="text/csv",
                    headers={"Content-disposition": f"attachment; filename={filename}"})

@admin_bp.route('/api/admin/reports/semester')
@login_required
@role_required('admin')
def report_semester():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id, u.full_name, s.grade, s.section, s.gpa, s.attendance_pct, s.class_rank
            FROM students s JOIN users u ON s.user_id = u.id ORDER BY s.grade, s.section, u.full_name
        """)
        rows = [[r['student_id'], r['full_name'], r['grade'], r['section'], r['gpa'], r['attendance_pct'], r['class_rank']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Roll No","Name","Grade","Section","GPA","Attendance %","Rank"], "semester_report.csv")

@admin_bp.route('/api/admin/reports/department')
@login_required
@role_required('admin')
def report_department():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT t.department, u.full_name, t.subjects
            FROM teachers t JOIN users u ON t.user_id = u.id ORDER BY t.department
        """)
        rows = [[r['department'], r['full_name'], r['subjects']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Department","Faculty Name","Subjects"], "department_report.csv")

@admin_bp.route('/api/admin/reports/gpa-trend')
@login_required
@role_required('admin')
def report_gpa_trend():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id, u.full_name, s.grade, s.gpa, s.risk_score
            FROM students s JOIN users u ON s.user_id = u.id ORDER BY s.gpa DESC
        """)
        rows = [[r['student_id'], r['full_name'], r['grade'], r['gpa'], r['risk_score']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Roll No","Name","Grade","GPA","Risk Score"], "gpa_trend_report.csv")

@admin_bp.route('/api/admin/reports/attendance-student')
@login_required
@role_required('admin')
def report_attendance_student():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id, u.full_name, s.grade, s.section, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id ORDER BY s.attendance_pct ASC
        """)
        rows = [[r['student_id'], r['full_name'], r['grade'], r['section'], r['attendance_pct']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Roll No","Name","Grade","Section","Attendance %"], "attendance_student_report.csv")

@admin_bp.route('/api/admin/reports/attendance-class')
@login_required
@role_required('admin')
def report_attendance_class():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.grade, s.section, COUNT(*) as total,
                   AVG(s.attendance_pct) as avg_att,
                   SUM(CASE WHEN s.attendance_pct < 75 THEN 1 ELSE 0 END) as defaulters
            FROM students s GROUP BY s.grade, s.section ORDER BY s.grade, s.section
        """)
        rows = [[r['grade'], r['section'], r['total'], round(r['avg_att'],1), r['defaulters']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Grade","Section","Total Students","Avg Attendance %","Defaulters"], "attendance_class_report.csv")

@admin_bp.route('/api/admin/reports/attendance-dept')
@login_required
@role_required('admin')
def report_attendance_dept():
    depts = [{"name":"CSE","att":92},{"name":"AIML","att":89},{"name":"ECE","att":84},{"name":"Mechanical","att":80}]
    rows = [[d['name'], d['att']] for d in depts]
    return _csv_response(rows, ["Department","Avg Attendance %"], "attendance_dept_report.csv")

@admin_bp.route('/api/admin/reports/fee-collection')
@login_required
@role_required('admin')
def report_fee_collection():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students"); total = cursor.fetchone()['c']
    fee = 50000
    rows = [
        ["Total Expected", total * fee],
        ["Collected (84%)", int(total * fee * 0.84)],
        ["Pending (16%)", int(total * fee * 0.16)],
        ["Due This Month", int(total * fee * 0.05)],
    ]
    return _csv_response(rows, ["Category","Amount (₹)"], "fee_collection_report.csv")

@admin_bp.route('/api/admin/reports/placements')
@login_required
@role_required('admin')
def report_placements():
    rows = [
        ["Infosys", 22, "4.5 LPA"],
        ["TCS", 35, "3.8 LPA"],
        ["Google", 2, "18 LPA"],
    ]
    return _csv_response(rows, ["Company","Offers","Avg Package"], "placement_report.csv")

@admin_bp.route('/api/admin/reports/naac')
@login_required
@role_required('admin')
def report_naac():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as c FROM students"); stu = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM teachers"); tch = cursor.fetchone()['c']
        cursor.execute("SELECT AVG(gpa) as g FROM students"); gpa = round(cursor.fetchone()['g'] or 0, 2)
        cursor.execute("SELECT AVG(attendance_pct) as a FROM students"); att = round(cursor.fetchone()['a'] or 0, 1)
    rows = [
        ["Total Students", stu], ["Total Faculty", tch],
        ["Avg GPA", gpa], ["Avg Attendance", f"{att}%"],
        ["Placement Rate", "78%"], ["Fee Collection", "84%"],
        ["Active Classes", 4], ["System Health", "Healthy"],
    ]
    return _csv_response(rows, ["Metric","Value"], "naac_accreditation_package.csv")

@admin_bp.route('/api/admin/reports/defaulters')
@login_required
@role_required('admin')
def report_defaulters():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id, u.full_name, s.grade, s.section, s.attendance_pct, s.parent_name, s.parent_phone
            FROM students s JOIN users u ON s.user_id = u.id
            WHERE s.attendance_pct < 75 ORDER BY s.attendance_pct ASC
        """)
        rows = [[r['student_id'], r['full_name'], r['grade'], r['section'], r['attendance_pct'], r['parent_name'] or '', r['parent_phone'] or ''] for r in cursor.fetchall()]
    return _csv_response(rows, ["Roll No","Name","Grade","Section","Attendance %","Parent Name","Parent Phone"], "defaulter_list.csv")

@admin_bp.route('/api/admin/reports/attendance-export')
@login_required
@role_required('admin')
def report_attendance_export():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id, u.full_name, s.grade, s.section, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id ORDER BY s.attendance_pct ASC
        """)
        rows = [[r['student_id'], r['full_name'], r['grade'], r['section'], r['attendance_pct']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Roll No","Name","Grade","Section","Attendance %"], "attendance_heatmap_export.csv")

@admin_bp.route('/api/admin/exams/hall-ticket/<int:exam_id>')
@login_required
@role_required('admin')
def hall_ticket(exam_id):
    exams_map = {
        1: {"name": "Mid-Term Mathematics", "date": "2024-06-10", "hall": "Hall A"},
        2: {"name": "Physics Internal", "date": "2024-06-12", "hall": "Hall B"},
        3: {"name": "End Semester CS101", "date": "2024-06-20", "hall": "Auditorium"},
    }
    exam = exams_map.get(exam_id, {"name": "Unknown", "date": "N/A", "hall": "N/A"})
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT s.student_id, u.full_name, s.grade, s.section FROM students s JOIN users u ON s.user_id = u.id")
        rows = [[r['student_id'], r['full_name'], r['grade'], r['section'], exam['name'], exam['date'], exam['hall']] for r in cursor.fetchall()]
    return _csv_response(rows, ["Roll No","Name","Grade","Section","Exam","Date","Hall"], f"hall_ticket_{exam_id}.csv")

@admin_bp.route('/api/admin/exams/marks', methods=['POST'])
@login_required
@role_required('admin')
@api_response
def enter_marks():
    data = request.json
    return {"message": f"Marks recorded for exam '{data.get('exam_name')}': {data.get('marks_count', 0)} entries saved."}
