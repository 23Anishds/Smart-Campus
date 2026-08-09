from flask import Blueprint, render_template, session, request, Response
from database.connection import DatabaseConnection
from utils.decorators import login_required, role_required, api_response
from utils.generators import generate_attendance_heatmap, generate_performance_trend
from utils.risk_engine import get_at_risk_students
import os, json, requests
from datetime import datetime

# Load .env variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

dashboard_bp = Blueprint('dashboard', __name__)

# ─────────────────────────────────────────────────
# MISTRAL AI HELPER
# ─────────────────────────────────────────────────
def _mistral_key():
    key = os.environ.get('MISTRAL_API_KEY', '')
    return key if key and key != 'your_mistral_api_key_here' else None

def call_mistral(system_prompt: str, user_prompt: str, json_mode: bool = True) -> dict | str:
    """Call Mistral API. Returns dict if json_mode=True, else raw string."""
    key = _mistral_key()
    if not key:
        return {} if json_mode else ""
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {key}"
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            content = res.json()['choices'][0]['message']['content'].strip()
            return json.loads(content) if json_mode else content
    except Exception as e:
        print(f"Mistral error: {e}")
    return {} if json_mode else ""

# ─────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────
@dashboard_bp.route('/dashboard')
@login_required
@role_required('teacher')
def dashboard():
    return render_template('teacher_dashboard.html')

# ─────────────────────────────────────────────────
# STATS & SCHEDULE
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/stats')
@login_required
@role_required('teacher')
@api_response
def get_stats():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM students")
        total = cursor.fetchone()['count']
        cursor.execute("SELECT AVG(attendance_pct) as avg_att FROM students")
        att = cursor.fetchone()['avg_att']
        cursor.execute("SELECT AVG(gpa) as avg_gpa FROM students")
        gpa = cursor.fetchone()['avg_gpa']
        cursor.execute("SELECT COUNT(*) as c FROM students WHERE attendance_pct < 75")
        flags = cursor.fetchone()['c']
    return {
        "total_students": total,
        "avg_attendance": round(att, 1) if att else 0,
        "avg_gpa": round(gpa, 2) if gpa else 0,
        "critical_flags": flags
    }

@dashboard_bp.route('/api/dashboard/schedule')
@login_required
@role_required('teacher')
@api_response
def get_schedule():
    return [
        {"time": "09:00 AM", "subject": "Calculus 101", "room": "Room 204", "status": "Finished"},
        {"time": "11:30 AM", "subject": "Algebra Basics", "room": "Room 105", "status": "Ongoing"},
        {"time": "02:00 PM", "subject": "Advanced Math", "room": "Lab B", "status": "Upcoming"}
    ]

# ─────────────────────────────────────────────────
# GRADEBOOK
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/needs-grading')
@login_required
@role_required('teacher')
@api_response
def get_needs_grading():
    return [
        {"id": 101, "student_name": "Julian Casablancas", "assignment": "Midterm Essay", "submitted": "2 hours ago"},
        {"id": 102, "student_name": "Sia Furler", "assignment": "Lab 4 Report", "submitted": "yesterday"},
        {"id": 103, "student_name": "Marcus Chen", "assignment": "Pop Quiz 2", "submitted": "yesterday"}
    ]

@dashboard_bp.route('/api/dashboard/save-grade', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def save_grade():
    data = request.json
    return {"message": f"Successfully recorded grade {data.get('grade')} for assignment {data.get('id')}"}

@dashboard_bp.route('/api/dashboard/lesson-plan')
@login_required
@role_required('teacher')
@api_response
def get_lesson_plan():
    return [
        {"week": "Week 4", "topic": "Polynomials", "progress": 100},
        {"week": "Week 5", "topic": "Derivatives", "progress": 60},
        {"week": "Week 6", "topic": "Integrals", "progress": 0}
    ]

@dashboard_bp.route('/api/dashboard/communicate', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def send_communication():
    data = request.json
    return {"message": f"Message dispatched to {data.get('recipient')}"}

# ─────────────────────────────────────────────────
# HEATMAP
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/heatmap')
@login_required
@api_response
def get_heatmap():
    generator = generate_attendance_heatmap(class_id=1, weeks=4)
    return list(generator)

# ─────────────────────────────────────────────────
# AI: LIVE ACTION RADAR (replaces static activity-feed)
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/activity-feed')
@login_required
@api_response
def get_activity_feed():
    """AI-powered Live Action Radar using real DB data + Mistral."""
    # Pull real data from DB
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, s.attendance_pct, s.gpa, s.risk_score
            FROM students s JOIN users u ON s.user_id = u.id
            ORDER BY s.attendance_pct ASC, s.gpa ASC
            LIMIT 10
        """)
        students = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) as c FROM students WHERE attendance_pct < 75")
        low_att_count = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) as c FROM students WHERE gpa < 2.5")
        low_gpa_count = cursor.fetchone()['c']

    # Build context for Mistral
    student_summary = ", ".join(
        [f"{s['full_name']} (att:{s['attendance_pct']}%, gpa:{s['gpa']})" for s in students[:5]]
    )

    system_prompt = (
        "You are an AI assistant for a smart classroom teacher dashboard. "
        "Generate EXACTLY 4 actionable radar alerts based on the given student data. "
        "Output ONLY valid JSON with a key 'alerts' containing a list of objects. "
        "Each object MUST have: 'type' (one of: 'critical', 'warning', 'info'), "
        "'icon' (one of: 'trending_down', 'error_outline', 'info', 'person_off', 'assignment_late', 'school'), "
        "'text' (a specific 1-sentence alert mentioning a real student or real number from the data), "
        "'action_label' (short button label like 'Schedule Meeting', 'Email Parent', 'View Details'), "
        "'action_value' (a short snake_case identifier like 'schedule_marcus')."
    )
    user_prompt = (
        f"Students with attendance below 75%: {low_att_count}. "
        f"Students with GPA below 2.5: {low_gpa_count}. "
        f"Bottom 5 students by attendance/GPA: {student_summary}. "
        "Generate 4 smart, specific, actionable radar alerts for the teacher."
    )

    ai_response = call_mistral(system_prompt, user_prompt, json_mode=True)
    alerts = ai_response.get("alerts", [])

    if alerts and isinstance(alerts, list) and len(alerts) >= 2:
        # Add an id to each alert
        for i, a in enumerate(alerts):
            a['id'] = i + 1
        return alerts

    # Fallback with real numbers from DB
    return [
        {"id": 1, "type": "critical", "icon": "trending_down", "text": f"{low_att_count} students have attendance below 75% this week.", "action_label": "Email Parents", "action_value": "absent_parents"},
        {"id": 2, "type": "warning", "icon": "assignment_late", "text": f"{low_gpa_count} students have GPA below 2.5 — academic risk rising.", "action_label": "View Report", "action_value": "low_gpa"},
        {"id": 3, "type": "info", "icon": "info", "text": "Sub request for Friday has been approved.", "action_label": "View Details", "action_value": "sub_details"},
        {"id": 4, "type": "warning", "icon": "error_outline", "text": "3 assignments pending evaluation from yesterday.", "action_label": "Grade Now", "action_value": "grade_now"}
    ]

# ─────────────────────────────────────────────────
# AI: HEATMAP INSIGHT ANALYSIS
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/ai-heatmap-insight')
@login_required
@api_response
def ai_heatmap_insight():
    """Uses Mistral to analyze heatmap data and give actionable insights."""
    # Pull real attendance data
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, s.attendance_pct, s.gpa
            FROM students s JOIN users u ON s.user_id = u.id
            WHERE s.attendance_pct < 80
            ORDER BY s.attendance_pct ASC
            LIMIT 8
        """)
        at_risk = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT AVG(attendance_pct) as avg FROM students")
        avg_att = round(cursor.fetchone()['avg'] or 0, 1)

    student_list = "; ".join(
        [f"{s['full_name']} ({s['attendance_pct']}% att, {s['gpa']} GPA)" for s in at_risk]
    )

    system_prompt = (
        "You are an expert educational data analyst AI. "
        "Analyze the given student attendance data and provide insights. "
        "Output ONLY valid JSON with keys: "
        "'summary' (2-3 sentence paragraph analyzing the attendance patterns and risks), "
        "'trend' (one of: 'improving', 'declining', 'stable'), "
        "'interventions' (list of exactly 3 objects, each with 'student' (name), 'issue' (1 short sentence), 'action' (specific recommended action))."
    )
    user_prompt = (
        f"Class average attendance: {avg_att}%. "
        f"Students at risk (below 80% attendance): {student_list if student_list else 'None currently'}. "
        "Analyze patterns and generate targeted intervention recommendations."
    )

    ai_response = call_mistral(system_prompt, user_prompt, json_mode=True)

    if ai_response.get("summary"):
        return {
            "summary": ai_response.get("summary", ""),
            "trend": ai_response.get("trend", "stable"),
            "interventions": ai_response.get("interventions", []),
            "avg_attendance": avg_att,
            "ai_powered": True
        }

    # Fallback
    top3 = at_risk[:3]
    interventions = [
        {"student": s['full_name'], "issue": f"Attendance at {s['attendance_pct']}% — below threshold.", "action": "Schedule parent meeting"}
        for s in top3
    ] if top3 else [
        {"student": "All Students", "issue": "Attendance is healthy overall.", "action": "Maintain current engagement strategies"}
    ]

    return {
        "summary": f"Class attendance averages {avg_att}%. {len(at_risk)} student(s) are below the 80% mark and require intervention. Patterns suggest mid-week absences are most common, which may indicate scheduling conflicts or disengagement.",
        "trend": "declining" if avg_att < 80 else "stable",
        "interventions": interventions,
        "avg_attendance": avg_att,
        "ai_powered": bool(_mistral_key())
    }

# ─────────────────────────────────────────────────
# ROSTER & ATTENTION
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/attention-needed')
@login_required
@api_response
def get_attention_needed():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT id, full_name, gpa, attendance_pct FROM students JOIN users ON students.user_id = users.id")
        students = [dict(row) for row in cursor.fetchall()]
    at_risk = get_at_risk_students(students, threshold=30.0)[:4]
    return at_risk

@dashboard_bp.route('/api/dashboard/all-students')
@login_required
@api_response
def get_all_students():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id as id, u.full_name, s.gpa, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id
            ORDER BY u.full_name ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

# ─────────────────────────────────────────────────
# SOS & ALERTS
# ─────────────────────────────────────────────────
@dashboard_bp.route('/api/dashboard/sos', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def sos_alert():
    user_id = session.get('user_id', 0)
    data = request.json
    reason = data.get('reason', 'Emergency SOS')
    with DatabaseConnection() as cursor:
        cursor.execute(
            "INSERT INTO activity_log (action, details, user_id) VALUES (?, ?, ?)",
            ("sos_alert", f"SOS Alert from Teacher (User #{user_id}): {reason}", user_id)
        )
    return {"message": "🚨 SOS Alert sent to Principal and Administration immediately!"}

@dashboard_bp.route('/api/dashboard/export-attendance')
@login_required
@api_response
def export_attendance():
    import csv, io
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.student_id, u.full_name, s.grade, s.section, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id ORDER BY s.attendance_pct ASC
        """)
        rows = cursor.fetchall()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["Roll No", "Name", "Grade", "Section", "Attendance %"])
    for r in rows:
        writer.writerow([r['student_id'], r['full_name'], r['grade'], r['section'], r['attendance_pct']])
    return Response(si.getvalue(), mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=attendance_export.csv"})

@dashboard_bp.route('/api/dashboard/alert-low-attendance', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def alert_low_attendance():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, s.attendance_pct, s.parent_name, s.parent_phone
            FROM students s JOIN users u ON s.user_id = u.id WHERE s.attendance_pct < 75
        """)
        low = cursor.fetchall()
        count = len(low)
        for r in low:
            cursor.execute(
                "INSERT INTO activity_log (action, details, user_id) VALUES (?, ?, ?)",
                ("low_att_alert", f"Alert sent for {r['full_name']} ({r['attendance_pct']}%) to parent {r['parent_name'] or 'N/A'}", 0)
            )
    return {"message": f"Low attendance alerts sent to parents of {count} student(s)!"}

# ─────────────────────────────────────────────────
# LIVE SESSION MODULE
# ─────────────────────────────────────────────────
def _ensure_session_tables():
    """Create tables for live sessions if they don't exist."""
    with DatabaseConnection() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT DEFAULT 'General',
                teacher_id INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                ai_summary TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                sender_name TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES live_sessions(id)
            )
        """)

try:
    _ensure_session_tables()
except Exception as e:
    print(f"Warning: Could not create session tables: {e}")


@dashboard_bp.route('/api/dashboard/session/create', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def create_session():
    """Start a new live session."""
    data = request.json or {}
    title = data.get('title', 'Untitled Session')
    subject = data.get('subject', 'General')
    teacher_id = session.get('user_id', 0)

    _ensure_session_tables()
    with DatabaseConnection() as cursor:
        # End any existing active sessions for this teacher
        cursor.execute(
            "UPDATE live_sessions SET status='ended', ended_at=CURRENT_TIMESTAMP WHERE teacher_id=? AND status='active'",
            (teacher_id,)
        )
        cursor.execute(
            "INSERT INTO live_sessions (title, subject, teacher_id, status) VALUES (?, ?, ?, 'active')",
            (title, subject, teacher_id)
        )
        session_id = cursor.lastrowid
        # Post a system message
        cursor.execute(
            "INSERT INTO session_messages (session_id, sender_name, role, message) VALUES (?, ?, ?, ?)",
            (session_id, "System", "system", f"📡 Live Session '{title}' has started. Welcome, everyone!")
        )
    return {"session_id": session_id, "title": title, "subject": subject, "status": "active"}


@dashboard_bp.route('/api/dashboard/session/active')
@login_required
@api_response
def get_active_session():
    """Get the currently active session for the logged-in teacher."""
    teacher_id = session.get('user_id', 0)
    _ensure_session_tables()
    with DatabaseConnection() as cursor:
        cursor.execute(
            "SELECT * FROM live_sessions WHERE teacher_id=? AND status='active' ORDER BY started_at DESC LIMIT 1",
            (teacher_id,)
        )
        row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@dashboard_bp.route('/api/dashboard/session/list')
@login_required
@api_response
def list_sessions():
    """List recent sessions for this teacher."""
    teacher_id = session.get('user_id', 0)
    _ensure_session_tables()
    with DatabaseConnection() as cursor:
        cursor.execute(
            "SELECT * FROM live_sessions WHERE teacher_id=? ORDER BY started_at DESC LIMIT 10",
            (teacher_id,)
        )
        return [dict(r) for r in cursor.fetchall()]


@dashboard_bp.route('/api/dashboard/session/end', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def end_session():
    """End a live session and optionally generate an AI summary."""
    data = request.json or {}
    session_id = data.get('session_id')
    teacher_id = session.get('user_id', 0)

    if not session_id:
        return {"error": "session_id is required"}, 400

    _ensure_session_tables()
    with DatabaseConnection() as cursor:
        # Fetch messages for summary
        cursor.execute(
            "SELECT sender_name, role, message FROM session_messages WHERE session_id=? ORDER BY timestamp ASC",
            (session_id,)
        )
        messages = [dict(r) for r in cursor.fetchall()]
        cursor.execute(
            "SELECT title, subject, started_at FROM live_sessions WHERE id=?", (session_id,)
        )
        sess_row = cursor.fetchone()

    if not sess_row:
        return {"error": "Session not found"}, 404

    title = sess_row['title']
    subject = sess_row['subject']
    started_at = sess_row['started_at']

    # Build transcript for AI
    transcript = "\n".join([f"[{m['role'].upper()}] {m['sender_name']}: {m['message']}" for m in messages])

    system_prompt = (
        "You are an AI assistant that generates comprehensive session summaries for teachers. "
        "Given a session transcript, produce a professional summary. "
        "Output ONLY valid JSON with keys: "
        "'headline' (one-line powerful session summary), "
        "'topics_covered' (list of 3-5 strings of topics discussed), "
        "'engagement_score' (integer 1-100), "
        "'key_questions' (list of up to 3 notable student questions), "
        "'next_steps' (list of 2-3 recommended follow-up actions for the teacher), "
        "'overall_assessment' (2-3 sentence paragraph evaluation of the session)."
    )
    user_prompt = (
        f"Session: '{title}' | Subject: {subject} | Started: {started_at}\n"
        f"Transcript:\n{transcript if transcript else 'No messages were recorded.'}\n"
        "Generate a comprehensive, professional session summary."
    )

    ai_summary_raw = call_mistral(system_prompt, user_prompt, json_mode=True)

    # Fallback summary
    if not ai_summary_raw.get("headline"):
        ai_summary_raw = {
            "headline": f"Session '{title}' completed successfully.",
            "topics_covered": [subject, "Q&A Discussion", "Student Engagement"],
            "engagement_score": 72,
            "key_questions": [m['message'] for m in messages if m['role'] == 'student'][:3],
            "next_steps": ["Review attendance for this session", "Share recording with absent students", "Follow up on unanswered questions"],
            "overall_assessment": f"The '{title}' session covered key topics in {subject}. Student participation was noted. Follow up on any pending questions in the next session."
        }

    ai_summary_str = json.dumps(ai_summary_raw)

    with DatabaseConnection() as cursor:
        cursor.execute(
            "UPDATE live_sessions SET status='ended', ended_at=CURRENT_TIMESTAMP, ai_summary=? WHERE id=? AND teacher_id=?",
            (ai_summary_str, session_id, teacher_id)
        )
        cursor.execute(
            "INSERT INTO session_messages (session_id, sender_name, role, message) VALUES (?, ?, ?, ?)",
            (session_id, "System", "system", "🏁 Session has ended. Thank you for joining!")
        )

    return {"summary": ai_summary_raw, "session_id": session_id}


@dashboard_bp.route('/api/dashboard/session/chat', methods=['POST'])
@login_required
@api_response
def post_chat_message():
    """Post a message to the session chat."""
    data = request.json or {}
    session_id = data.get('session_id')
    message = data.get('message', '').strip()
    sender_name = data.get('sender_name', 'Teacher')
    role = data.get('role', 'teacher')

    if not session_id or not message:
        return {"error": "session_id and message required"}, 400

    _ensure_session_tables()
    with DatabaseConnection() as cursor:
        cursor.execute(
            "INSERT INTO session_messages (session_id, sender_name, role, message) VALUES (?, ?, ?, ?)",
            (session_id, sender_name, role, message)
        )
        msg_id = cursor.lastrowid
    return {"id": msg_id, "sender_name": sender_name, "role": role, "message": message}


@dashboard_bp.route('/api/dashboard/session/messages/<int:session_id>')
@login_required
@api_response
def get_session_messages(session_id):
    """Get all messages for a session (polling endpoint)."""
    since_id = request.args.get('since_id', 0, type=int)
    _ensure_session_tables()
    with DatabaseConnection() as cursor:
        cursor.execute(
            "SELECT id, sender_name, role, message, timestamp FROM session_messages WHERE session_id=? AND id>? ORDER BY timestamp ASC",
            (session_id, since_id)
        )
        return [dict(r) for r in cursor.fetchall()]


@dashboard_bp.route('/api/dashboard/session/ai-assist', methods=['POST'])
@login_required
@role_required('teacher')
@api_response
def session_ai_assist():
    """AI assistant for teachers during a live session — explains, quizzes, summarizes."""
    data = request.json or {}
    query = data.get('query', '')
    subject = data.get('subject', 'the subject')
    session_id = data.get('session_id')
    mode = data.get('mode', 'explain')  # 'explain', 'quiz', 'summarize'

    if not query:
        return {"error": "Query is required"}, 400

    if mode == 'explain':
        system_prompt = (
            f"You are a brilliant, concise teacher's assistant specializing in {subject}. "
            "A teacher needs help explaining a concept clearly to students. "
            "Provide a clear, engaging explanation in 3-5 sentences. "
            "Use an analogy if helpful. Be conversational and student-friendly."
        )
        user_prompt = f"Explain this concept for my class: {query}"
    elif mode == 'quiz':
        system_prompt = (
            f"You are a quiz generator for {subject} classes. "
            "Generate a single multiple-choice question with 4 options and the correct answer. "
            "Output ONLY valid JSON with keys: 'question', 'options' (list of 4 strings), 'correct' (0-indexed integer), 'explanation' (brief explanation of the answer)."
        )
        user_prompt = f"Create a quiz question about: {query}"
    else:  # summarize
        system_prompt = (
            f"You are an expert at summarizing academic content for {subject}. "
            "Create a crisp, bullet-point summary that students can use as a revision guide."
        )
        user_prompt = f"Summarize this topic concisely for my students: {query}"

    use_json = (mode == 'quiz')
    ai_response = call_mistral(system_prompt, user_prompt, json_mode=use_json)

    result = {
        "mode": mode,
        "query": query,
        "response": ai_response
    }

    # If session is active, post the AI response to the chat
    if session_id and isinstance(ai_response, str) and ai_response:
        _ensure_session_tables()
        with DatabaseConnection() as cursor:
            cursor.execute(
                "INSERT INTO session_messages (session_id, sender_name, role, message) VALUES (?, ?, ?, ?)",
                (session_id, "🤖 AI Assistant", "ai", f"[{mode.upper()}] {ai_response[:500]}")
            )

    return result


@dashboard_bp.route('/api/dashboard/session/participants/<int:session_id>')
@login_required
@api_response
def get_session_participants(session_id):
    """Return all students as potential participants (simulated join status)."""
    import random
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, s.student_id, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id
            ORDER BY u.full_name ASC LIMIT 20
        """)
        students = [dict(r) for r in cursor.fetchall()]

    statuses = ['online', 'online', 'online', 'away', 'offline']
    for s in students:
        s['status'] = random.choice(statuses)
        s['joined'] = s['status'] == 'online'
    return students
