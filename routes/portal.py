from flask import Blueprint, render_template, request, session
from database.connection import DatabaseConnection
from utils.decorators import login_required, role_required, api_response
import json
import os
from datetime import datetime, timedelta

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── MISTRAL AI SETUP ──────────────────────────────────────────
import requests

def has_mistral_key():
    """Check if Mistral API key is set."""
    api_key = os.environ.get('MISTRAL_API_KEY', '')
    if api_key and api_key != 'your_mistral_api_key_here':
        return api_key
    return None

def call_mistral_json(system_prompt: str, user_prompt: str) -> dict:
    """Calls Mistral API requesting JSON output."""
    api_key = has_mistral_key()
    if not api_key:
        return {}
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "mistral-small-latest",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=15)
        if res.status_code == 200:
            return json.loads(res.json()['choices'][0]['message']['content'].strip())
    except Exception as e:
        print(f"Mistral API error: {e}")
    return {}

portal_bp = Blueprint('portal', __name__)

@portal_bp.route('/portal')
@login_required
@role_required('student')
def portal_page():
    return render_template('student_portal.html')

# ─── USER PROFILE ─────────────────────────────────────────────
@portal_bp.route('/api/portal/profile')
@login_required
@role_required('student')
@api_response
def get_profile():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, u.email, s.student_id, s.grade, s.section, s.gpa, s.attendance_pct
            FROM users u JOIN students s ON s.user_id = u.id
            WHERE u.id = ?
        """, (session['user_id'],))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"full_name": "Student", "email": "", "student_id": "", "grade": "", "section": ""}

# ─── CLASSES ──────────────────────────────────────────────────
@portal_bp.route('/api/portal/classes')
@login_required
@role_required('student')
@api_response
def get_classes():
    return [
        {
            "id": 1, "name": "Mathematics", "teacher": "Dr. Sarah Jenkins", "progress": 85, "attendance": 92,
            "materials": ["Algebra 101.pdf", "Calculus Notes.ppt"], "upcoming": "Quiz next Tuesday"
        },
        {
            "id": 2, "name": "Physics", "teacher": "Ms. Sarah Vance", "progress": 68, "attendance": 75,
            "materials": ["Kinematics.pdf"], "upcoming": "Lab Report Due Friday"
        },
        {
            "id": 3, "name": "Chemistry", "teacher": "Prof. Michael Chen", "progress": 90, "attendance": 98,
            "materials": ["Periodic Table.png", "Organic Chem Basics.pdf"], "upcoming": "Group Project"
        }
    ]

# ─── CLASSMATES ───────────────────────────────────────────────
@portal_bp.route('/api/portal/classmates')
@login_required
@role_required('student')
@api_response
def get_classmates():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT u.full_name, s.student_id, s.section, s.gpa, s.attendance_pct
            FROM students s JOIN users u ON s.user_id = u.id
            ORDER BY s.gpa DESC
        """)
        all_students = [dict(row) for row in cursor.fetchall()]
        
    for idx, s in enumerate(all_students):
        s['rank'] = idx + 1
        # Assign badges deterministically based on student stats
        badges = []
        if s.get('attendance_pct', 0) >= 90:
            badges.append("Top Attendance")
        if s.get('gpa', 0) >= 3.5:
            badges.append("Honor Roll")
        if s.get('gpa', 0) >= 3.8:
            badges.append("Math Whiz")
        if idx == 0:
            badges.append("🏆 Class Topper")
        s['badges'] = badges
        
    return all_students

# ─── ATTENDANCE ───────────────────────────────────────────────
@portal_bp.route('/api/portal/attendance_dashboard')
@login_required
@role_required('student')
@api_response
def attendance_dashboard():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT attendance_pct FROM students WHERE user_id = ?", (session['user_id'],))
        row = cursor.fetchone()
        overall = row['attendance_pct'] if row else 80.0

        # Get real attendance records if any
        cursor.execute("""
            SELECT a.date, a.class_name, a.status 
            FROM attendance a 
            JOIN students s ON a.student_id = s.id

            WHERE s.user_id = ?
            ORDER BY a.date DESC LIMIT 10
        """, (session['user_id'],))
        records = [dict(r) for r in cursor.fetchall()]
        
    # If no attendance records, use sample data
    if not records:
        history = [
            {"date": "04 Jun", "subject": "Physics", "status": "Present"},
            {"date": "03 Jun", "subject": "Math", "status": "Present"},
            {"date": "02 Jun", "subject": "Chemistry", "status": "Absent"},
            {"date": "01 Jun", "subject": "Math", "status": "Present"},
            {"date": "31 May", "subject": "Physics", "status": "Present"},
        ]
    else:
        history = [{"date": r['date'], "subject": r['class_name'], "status": r['status'].capitalize()} for r in records]
    
    # AI Prediction Logic
    pred = ""
    if overall < 75:
        pred = f"⚠️ Critical: Your attendance is below 75%. You risk being debarred from exams. Attend every class from now!"
    elif overall < 80:
        pred = f"AI Prediction: If you miss 3 more classes, your attendance will fall to {max(0, overall - 4.5):.1f}%. Stay consistent!"
    elif overall < 90:
        pred = f"AI Prediction: You're doing okay! You can safely miss 2 more classes this month without dropping below 80%."
    else:
        pred = "🌟 Excellent attendance! You have a comfortable buffer. Keep up the amazing work!"
        
    return {
        "overall": overall,
        "history": history,
        "prediction": pred,
        "subjects": {"Math": 92.5, "Physics": 75.0, "Chemistry": 98.0}
    }

# ─── REPORTS ──────────────────────────────────────────────────
@portal_bp.route('/api/portal/reports')
@login_required
@role_required('student')
@api_response
def reports():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.gpa, s.attendance_pct, s.class_rank
            FROM students s WHERE s.user_id = ?
        """, (session['user_id'],))
        row = cursor.fetchone()
        gpa = row['gpa'] if row else 3.0
        attendance = row['attendance_pct'] if row else 80.0
        rank = row['class_rank'] if row else 0

    # AI deep dive via Mistral
    system_prompt = "You are an AI learning assistant analyzing a student's performance. Output ONLY valid JSON."
    user_prompt = f"The student has a GPA of {gpa} and attendance of {attendance}%. Analyze their performance and generate JSON with: 'strength' (string, e.g. 'Mathematics (92%)'), 'needs_improvement' (string, e.g. 'Physics (60%)'), 'gap' (string, one sentence advice), and 'recommendations' (list of 4 short actionable study tasks)."
    
    ai_response = call_mistral_json(system_prompt, user_prompt)
    
    # Fallback to defaults if API fails
    insights = {
        "strength": ai_response.get("strength", f"Chemistry ({min(int(gpa * 22), 85)}%)"),
        "needs_improvement": ai_response.get("needs_improvement", f"Mathematics ({max(int(gpa * 14), 38)}%)"),
        "gap": ai_response.get("gap", "Focus on solving more practice problems and reviewing weak chapters.")
    }
    recs = ai_response.get("recommendations", [
        "Watch 'Vector Mathematics Guide' (15 min)",
        "Complete Practice Quiz: Physics Chapters 4-5",
        "Review class notes for the last 3 weeks",
        "Form or join a study group for peer learning"
    ])

    return {
        "gpa": gpa,
        "attendance": attendance,
        "rank": rank,
        "ai_insights": insights,
        "recommendations": recs
    }

# ─── ASSIGNMENTS ──────────────────────────────────────────────
@portal_bp.route('/api/portal/assignments')
@login_required
@role_required('student')
@api_response
def get_assignments():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT a.* FROM assignments a
            JOIN students s ON a.student_id = s.id
            WHERE s.user_id = ?
        """, (session['user_id'],))
        return [dict(row) for row in cursor.fetchall()]

@portal_bp.route('/api/portal/assignments/<int:assignment_id>/submit', methods=['POST'])
@login_required
@role_required('student')
@api_response
def submit_assignment(assignment_id):
    with DatabaseConnection() as cursor:
        # Verify the assignment belongs to this student
        cursor.execute("""
            UPDATE assignments SET status = 'completed'
            WHERE id = ? AND student_id IN (
                SELECT s.id FROM students s WHERE s.user_id = ?
            )
        """, (assignment_id, session['user_id']))
    return {"message": "Assignment submitted successfully!", "assignment_id": assignment_id}

# ─── EXAMS ────────────────────────────────────────────────────
@portal_bp.route('/api/portal/exams')
@login_required
@role_required('student')
@api_response
def get_exams():
    # Build exam data from timetable and student context
    now = datetime.now()
    exams = {
        "upcoming": [
            {
                "id": 1,
                "subject": "Mathematics",
                "type": "Mid-Term",
                "date": (now + timedelta(days=14)).strftime("%d %b %Y"),
                "time": "09:00 AM - 12:00 PM",
                "room": "Hall A",
                "syllabus": ["Algebra (Ch 1-4)", "Calculus (Ch 5-7)", "Trigonometry (Ch 8)"],
                "days_left": 14
            },
            {
                "id": 2,
                "subject": "Physics",
                "type": "Mid-Term",
                "date": (now + timedelta(days=16)).strftime("%d %b %Y"),
                "time": "09:00 AM - 12:00 PM",
                "room": "Hall B",
                "syllabus": ["Kinematics (Ch 1-3)", "Newton's Laws (Ch 4-5)"],
                "days_left": 16
            },
            {
                "id": 3,
                "subject": "Chemistry",
                "type": "Mid-Term",
                "date": (now + timedelta(days=18)).strftime("%d %b %Y"),
                "time": "02:00 PM - 05:00 PM",
                "room": "Hall A",
                "syllabus": ["Organic Chemistry (Ch 1-6)", "Periodic Table"],
                "days_left": 18
            }
        ],
        "mock_tests": [
            {"id": 1, "subject": "Physics Chapters 1-3", "questions": 30, "duration": "45 min", "difficulty": "Medium"},
            {"id": 2, "subject": "Math: Algebra Basics", "questions": 25, "duration": "30 min", "difficulty": "Easy"},
            {"id": 3, "subject": "Chemistry: Organic", "questions": 40, "duration": "60 min", "difficulty": "Hard"},
        ],
        "past_results": [
            {"subject": "Mathematics", "type": "Unit Test 1", "score": 87, "max_score": 100, "grade": "A"},
            {"subject": "Physics", "type": "Unit Test 1", "score": 72, "max_score": 100, "grade": "B+"},
            {"subject": "Chemistry", "type": "Unit Test 1", "score": 91, "max_score": 100, "grade": "A+"},
        ]
    }
    return exams

@portal_bp.route('/api/portal/mock_test/generate', methods=['POST'])
@login_required
@role_required('student')
@api_response
def generate_mock_test():
    data = request.json
    subject = data.get('subject', 'General Knowledge')
    
    system_prompt = "You are an expert test creator. Output ONLY valid JSON containing an array of exactly 10 multiple choice questions."
    user_prompt = f"Create a 10-question multiple choice test for '{subject}'. Format as a JSON object with a 'questions' key. Each question in the array should have 'question' (string), 'options' (array of 4 strings), and 'correct_index' (integer 0-3)."
    
    ai_response = call_mistral_json(system_prompt, user_prompt)
    questions = ai_response.get('questions', [])
    
    if not questions:
        # Fallback if API fails
        questions = [
            {
                "question": f"Sample question about {subject}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": 0
            } for _ in range(10)
        ]
        
    return {"subject": subject, "questions": questions}

# ─── ACHIEVEMENTS ─────────────────────────────────────────────
@portal_bp.route('/api/portal/achievements')
@login_required
@role_required('student')
@api_response
def get_achievements():
    with DatabaseConnection() as cursor:
        cursor.execute("SELECT gpa, attendance_pct FROM students WHERE user_id = ?", (session['user_id'],))
        row = cursor.fetchone()
        gpa = row['gpa'] if row else 0.0
        att = row['attendance_pct'] if row else 0.0

    achievements = []
    # Earned based on actual stats
    if att >= 90:
        achievements.append({"icon": "workspace_premium", "color": "yellow", "title": "Perfect Attendance", "desc": "90%+ attendance rate", "earned": True})
    if gpa >= 3.5:
        achievements.append({"icon": "military_tech", "color": "indigo", "title": "Honor Roll", "desc": "GPA above 3.5", "earned": True})
    if gpa >= 3.8:
        achievements.append({"icon": "emoji_events", "color": "amber", "title": "Academic Star", "desc": "GPA above 3.8", "earned": True})
    
    # Static achievements everyone can have
    achievements.append({"icon": "science", "color": "blue", "title": "Science Fair Pro", "desc": "First Place Winner", "earned": True})
    achievements.append({"icon": "groups", "color": "green", "title": "Team Player", "desc": "Active in 3+ study groups", "earned": True})
    
    # Locked achievements
    achievements.append({"icon": "local_fire_department", "color": "red", "title": "7-Day Streak", "desc": "Login 7 days in a row", "earned": False})
    achievements.append({"icon": "auto_awesome", "color": "purple", "title": "AI Explorer", "desc": "Use AI Buddy 50 times", "earned": False})
    achievements.append({"icon": "speed", "color": "orange", "title": "Speed Solver", "desc": "Complete quiz under 5 min", "earned": False})
    
    # Stats
    stats = {
        "total_earned": len([a for a in achievements if a['earned']]),
        "total_available": len(achievements),
        "xp_points": int(gpa * 250 + att * 5),
        "level": max(1, int(gpa * 2.5))
    }
    
    return {"achievements": achievements, "stats": stats}

# ─── ANALYTICS ────────────────────────────────────────────────
@portal_bp.route('/api/portal/analytics')
@login_required
@role_required('student')
@api_response
def get_analytics():
    with DatabaseConnection() as cursor:
        cursor.execute("""
            SELECT s.gpa, s.attendance_pct, s.risk_score
            FROM students s WHERE s.user_id = ?
        """, (session['user_id'],))
        row = cursor.fetchone()
        gpa = row['gpa'] if row else 3.0
        att = row['attendance_pct'] if row else 80.0
        risk = row['risk_score'] if row else 50.0

    focus_score = min(100, int(gpa * 20 + att * 0.2))
    
    # AI learning tips via Mistral
    system_prompt = "You are an AI tutor generating short personalized study tips. Output ONLY valid JSON."
    user_prompt = f"Student GPA: {gpa}, Attendance: {att}%, Risk Score: {risk}/100. Peak hours: 4-6:30 PM. Generate JSON with a key 'tips' containing a list of exactly 3 short, personalized, encouraging learning tips."
    
    ai_response = call_mistral_json(system_prompt, user_prompt)
    tips = ai_response.get("tips", [
        "Your peak focus hours are between 4-6:30 PM. Schedule hard subjects then.",
        "You spend the most time on Math — your strongest subject. Consider reallocating 30 min to Physics.",
        f"{'Your risk score is low. Keep it up!' if risk < 30 else 'Your risk score is elevated. Focus on attendance and assignments.'}"
    ])

    return {
        "focus_score": focus_score,
        "study_pattern": {
            "peak_hours": "4:00 PM - 6:30 PM",
            "avg_daily_hours": round(gpa * 1.2, 1),
            "most_productive_day": "Wednesday",
            "streak_days": max(1, int(att / 15))
        },
        "subject_time": {
            "Mathematics": 35,
            "Physics": 25,
            "Chemistry": 20,
            "History": 12,
            "Other": 8
        },
        "weekly_progress": [
            {"week": "Week 1", "score": max(40, int(gpa * 18))},
            {"week": "Week 2", "score": max(45, int(gpa * 20))},
            {"week": "Week 3", "score": max(50, int(gpa * 22))},
            {"week": "Week 4", "score": max(55, int(gpa * 24))},
        ],
        "risk_score": risk,
        "ai_tips": tips
    }

# ─── NOTIFICATIONS ────────────────────────────────────────────
@portal_bp.route('/api/portal/notifications')
@login_required
@role_required('student')
@api_response
def get_notifications():
    now = datetime.now()
    notifications = [
        {"id": 1, "type": "assignment", "icon": "assignment", "title": "Lab Report Due", "message": "Physics Lab Report due today at 11:59 PM", "time": "2 hours ago", "read": False},
        {"id": 2, "type": "exam", "icon": "description", "title": "Mid-Term Schedule Released", "message": "Check the Exams tab for your mid-term exam dates", "time": "1 day ago", "read": False},
        {"id": 3, "type": "achievement", "icon": "emoji_events", "title": "New Badge Unlocked!", "message": "You earned the 'Team Player' badge", "time": "2 days ago", "read": True},
        {"id": 4, "type": "class", "icon": "class", "title": "New Material Uploaded", "message": "Calculus Notes.ppt added to Mathematics", "time": "3 days ago", "read": True},
        {"id": 5, "type": "attendance", "icon": "how_to_reg", "title": "Attendance Reminder", "message": "Your Physics attendance is at 75%. Attend the next class!", "time": "4 days ago", "read": True},
    ]
    unread_count = len([n for n in notifications if not n['read']])
    return {"notifications": notifications, "unread_count": unread_count}

@portal_bp.route('/api/portal/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
@role_required('student')
@api_response
def mark_notification_read(notif_id):
    return {"message": "Notification marked as read", "id": notif_id}

# ─── AI TUTOR (Powered by Google Gemini) ─────────────────────
@portal_bp.route('/api/portal/chat', methods=['POST'])
@login_required
@role_required('student')
@api_response
def chatbot():
    data = request.json
    user_message = data.get('message', '').strip()
    chat_history = data.get('history', [])  # optional conversation history

    if not user_message:
        return {"message": "Please type a message!"}

    # ── Get student context ──────────────────────────────────
    context = {}
    try:
        with DatabaseConnection() as cursor:
            cursor.execute("""
                SELECT u.full_name, s.gpa, s.attendance_pct, s.grade, s.section
                FROM users u JOIN students s ON s.user_id = u.id
                WHERE u.id = ?
            """, (session['user_id'],))
            row = cursor.fetchone()
            if row:
                context = dict(row)
    except Exception:
        pass

    name = context.get('full_name', 'Student').split()[0]
    gpa  = context.get('gpa', 3.0)
    att  = context.get('attendance_pct', 80.0)
    grade   = context.get('grade', 'N/A')
    section = context.get('section', 'N/A')

    # ── Build system prompt ──────────────────────────────────
    today = datetime.now().strftime("%A, %d %B %Y")
    system_prompt = f"""You are an expert AI Tutor embedded in EduSync, a smart classroom platform. 
You are currently helping a student named {name}.

Student Profile:
- Name: {name}
- Grade: {grade}, Section: {section}
- Current GPA: {gpa}/4.0
- Attendance: {att}%
- Today's Date: {today}
- Enrolled subjects: Mathematics, Physics, Chemistry, History

Your Role and Rules:
1. ALWAYS give complete, accurate, and helpful answers. Never say you cannot answer academic questions.
2. For subject questions (math, physics, chemistry, etc.) — solve them step by step and explain clearly.
3. For timetable/schedule requests — generate a detailed, realistic day-by-day study timetable in a nicely formatted table.
4. Personalize responses using the student's data above when relevant (e.g., "Since your Physics attendance is {att}%...").
5. Be encouraging, friendly, and concise. Use emojis sparingly to stay engaging.
6. Format math equations clearly (use ^ for powers, sqrt() for roots).
7. For multi-step problems, number each step.
8. If asked to create a study plan or timetable, always include: subjects, time slots, breaks, and daily goals.
9. Keep responses focused and well-structured. Use bullet points and headers where helpful.
10. NEVER refuse to answer a legitimate academic question. You are a tutor — teaching is your purpose.

Examples of what you can do:
- Solve equations step by step
- Explain any concept in any subject  
- Create personalized study timetables
- Give exam preparation strategies
- Motivate and guide the student based on their performance"""

    # ── Try Mistral AI ────────────────────────────────────────
    response_text = ""
    api_key = has_mistral_key()

    if api_key:
        try:
            # Build conversation with system context
            messages = [{"role": "system", "content": system_prompt}]

            # Include recent chat history for context (last 6 exchanges)
            if chat_history:
                for h in chat_history[-6:]:
                    messages.append({"role": h['role'], "content": h['content']})
            
            messages.append({"role": "user", "content": user_message})

            # Call Mistral API using requests
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            data = {
                "model": "mistral-small-latest",
                "messages": messages
            }
            
            res = requests.post(url, headers=headers, json=data)
            
            if res.status_code == 200:
                response_text = res.json()['choices'][0]['message']['content'].strip()
            else:
                response_text = f"⚠️ I'm having trouble connecting right now, {name}. (Error {res.status_code})"
                
        except Exception as e:
            response_text = (
                f"⚠️ I'm having trouble connecting right now, {name}. "
                "Please try again in a moment."
            )
    else:
        # ── Friendly fallback when no API key is set ─────────
        response_text = (
            f"🔑 **AI Tutor needs a Mistral API Key!**\n\n"
            f"Hi {name}! I'm your AI Tutor, but I need an API key to activate.\n\n"
            f"**Get your key:**\n"
            f"1. Go to [console.mistral.ai](https://console.mistral.ai/)\n"
            f"2. Sign in → Create an API Key\n"
            f"3. Copy the key\n"
            f"4. Open the `.env` file in your project and replace `your_mistral_api_key_here` with your key\n"
            f"5. Restart the server\n\n"
            f"Once set up, I can answer any question, solve problems, and create study timetables for you! 🎓"
        )

    # ── Save to chat history ─────────────────────────────────
    try:
        with DatabaseConnection() as cursor:
            cursor.execute("SELECT id FROM students WHERE user_id = ?", (session['user_id'],))
            student = cursor.fetchone()
            if student:
                cursor.execute(
                    "INSERT INTO chat_messages (student_id, message, response) VALUES (?, ?, ?)",
                    (student['id'], user_message, response_text)
                )
    except Exception:
        pass

    return {"message": response_text}

