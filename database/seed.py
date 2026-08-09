import sqlite3
import json
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import DatabaseConnection
from werkzeug.security import generate_password_hash

SCHEMA = """
-- Users table (base for OOP inheritance)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin','teacher','student')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table (extends users)
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    student_id TEXT UNIQUE NOT NULL,
    grade TEXT,
    section TEXT,
    gpa REAL DEFAULT 0.0,
    attendance_pct REAL DEFAULT 100.0,
    class_rank INTEGER,
    risk_score REAL DEFAULT 0.0,
    parent_name TEXT,
    parent_phone TEXT,
    parent_email TEXT,
    status TEXT DEFAULT 'active'
);

-- Teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    department TEXT,
    subjects TEXT,
    is_available INTEGER DEFAULT 1
);

-- Attendance records
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    class_name TEXT,
    date TEXT,
    period INTEGER,
    status TEXT CHECK(status IN ('present','absent','late')) NOT NULL,
    marked_by TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignments
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT,
    due_date TEXT,
    status TEXT DEFAULT 'pending',
    student_id INTEGER REFERENCES students(id)
);

-- Timetable slots
CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    period INTEGER NOT NULL,
    start_time TEXT,
    end_time TEXT,
    subject TEXT,
    teacher_id INTEGER REFERENCES teachers(id),
    room TEXT,
    section TEXT
);

-- Registration drafts (multi-step form)
CREATE TABLE IF NOT EXISTS registration_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_id TEXT UNIQUE,
    step INTEGER DEFAULT 1,
    personal_info TEXT,
    academic_info TEXT,
    guardian_info TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity log
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages (AI Study Buddy)
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES students(id),
    message TEXT,
    response TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def seed_database():
    """Drops existing tables and seeds with fresh sample data."""
    try:
        from config import AppConfig
        config = AppConfig.get_config()
        # Remove old db if exists for clean seed
        if os.path.exists(config.DATABASE_PATH):
            os.remove(config.DATABASE_PATH)
            print(f"Deleted old database at {config.DATABASE_PATH}")
    except Exception as e:
        print(f"Error handling old db: {e}")

    with DatabaseConnection() as cursor:
        print("Creating tables...")
        # Execute schema script
        for statement in SCHEMA.split(';'):
            if statement.strip():
                cursor.execute(statement)

        print("Seeding Administrators...")
        hashed_pw = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
            ("admin", hashed_pw, "System Admin", "admin@edusync.com", "admin")
        )

        print("Seeding Teachers...")
        teacher_pw = generate_password_hash("teacher123")
        teachers_data = [
            ("teacher", teacher_pw, "Dr. Sarah Jenkins", "s.jenkins@edusync.com", "Mathematics", ["Algebra", "Calculus"]),
            ("mchen", teacher_pw, "Prof. Michael Chen", "m.chen@edusync.com", "Science", ["Biology", "Chemistry"]),
            ("erodriguez", teacher_pw, "Ms. Elena Rodriguez", "e.rodriguez@edusync.com", "History", ["Modern History"]),
            ("jsterling", teacher_pw, "Mr. John Sterling", "j.sterling@edusync.com", "Mathematics", ["Geometry"]),
            ("svance", teacher_pw, "Ms. Sarah Vance", "s.vance@edusync.com", "Science", ["Physics"])
        ]
        
        for t in teachers_data:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                (t[0], t[1], t[2], t[3], "teacher")
            )
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO teachers (user_id, department, subjects) VALUES (?, ?, ?)",
                (user_id, t[4], json.dumps(t[5]))
            )

        print("Seeding Students...")
        student_pw = generate_password_hash("student123")
        students_data = [
            ("student", "Rahul Sharma", "rahul@student.edusync.com", "STU-2024-0001", "11", "A", 3.8, 92.5, 5, 15.0, "Anil Sharma", "555-0101"),
            ("jcasablancas", "Julian Casablancas", "julian@student.edusync.com", "STU-2024-0002", "11", "B", 3.42, 82.0, 14, 45.0, "Elena Reed", "+1 234 567 890"),
            ("mchen_stu", "Marcus Chen", "marcus@student.edusync.com", "STU-2024-0003", "12", "A", 2.9, 78.0, 32, 65.0, "David Chen", "555-0102"),
            ("channappa", "Channappa", "channappa@student.edusync.com", "STU-2024-0004", "10", "B", 2.5, 75.0, 40, 80.0, "Parent C", "555-0103"),
            ("geethanjali", "Geethanjali", "geethanjali@student.edusync.com", "STU-2024-0005", "10", "B", 3.9, 98.0, 2, 5.0, "Parent G", "555-0104"),
            ("mazan", "Mohammed Azan", "mazan@student.edusync.com", "STU-2024-0006", "10", "B", 2.2, 65.0, 45, 90.0, "Parent M", "555-0105"),
            ("manish", "Manish", "manish@student.edusync.com", "STU-2024-0007", "11", "C", 2.1, 70.0, 42, 85.0, "Parent Man", "555-0106"),
            ("menal", "Menal", "menal@student.edusync.com", "STU-2024-0008", "11", "C", 2.4, 72.0, 38, 75.0, "Parent Men", "555-0107"),
            ("shamaz", "Shamaz", "shamaz@student.edusync.com", "STU-2024-0009", "12", "B", 2.6, 68.0, 35, 82.0, "Parent S", "555-0108"),
            ("lchen", "Leo Chen", "lchen@student.edusync.com", "STU-2024-0010", "12", "B", 2.8, 80.0, 28, 60.0, "Parent LC", "555-0109"),
            ("manvith", "Manvith", "manvith@student.edusync.com", "STU-2024-0011", "11", "B", 3.5, 95.0, 10, 10.0, "Parent Manv", "555-0110"),
            ("shawn", "Shawn", "shawn@student.edusync.com", "STU-2024-0012", "11", "B", 3.2, 88.0, 20, 25.0, "Parent Shw", "555-0111"),
            ("neil", "Neil", "neil@student.edusync.com", "STU-2024-0013", "11", "B", 3.6, 96.0, 8, 8.0, "Parent N", "555-0112"),
            ("sfurler", "Sia Furler", "sia@student.edusync.com", "STU-2024-0014", "11", "B", 3.7, 94.0, 6, 12.0, "Parent Sia", "555-0113"),
        ]

        for s in students_data:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                (s[0], student_pw, s[1], s[2], "student")
            )
            user_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO students 
                (user_id, student_id, grade, section, gpa, attendance_pct, class_rank, risk_score, parent_name, parent_phone) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11])
            )

        print("Seeding Assignments for Rahul...")
        # Get Rahul's student_id
        cursor.execute("SELECT id FROM students WHERE student_id = 'STU-2024-0001'")
        rahul_id = cursor.fetchone()['id']
        
        assignments = [
            ("Lab Report: Circuits", "Physics", "Today 11:59 PM", "pending", rahul_id),
            ("WWI Essay Draft", "History", "In 3 days", "pending", rahul_id),
            ("Color Theory Canvas", "Art", "Yesterday", "completed", rahul_id)
        ]
        for a in assignments:
            cursor.execute(
                "INSERT INTO assignments (title, subject, due_date, status, student_id) VALUES (?, ?, ?, ?, ?)",
                a
            )
            
        print("Seeding Activity Log...")
        activities = [
            ("alert", "AI Nudge: Marcus Chen's score dropped 15% in Lab 4.", 2), # admin user_id
            ("info", "Weekly Quiz auto-graded for Class 12A.", 2),
            ("warning", "3 students flagged for low attendance this month.", 2),
            ("success", "New student registration: Julian Voss.", 2)
        ]
        for act in activities:
            cursor.execute("INSERT INTO activity_log (action, details, user_id) VALUES (?, ?, ?)", act)
            
        print("Seeding Timetable...")
        # Let's add a conflict in room 204
        timetable = [
            ("Wednesday", 1, "09:00", "09:50", "Mathematics", 1, "Room 102", "11A"),
            ("Wednesday", 2, "10:00", "10:50", "History", 3, "Room 205", "11A"),
            # Conflict: Two classes in Room 204 at the same time
            ("Wednesday", 5, "14:00", "14:50", "Advanced Physics", 2, "Room 204", "12A"),
            ("Wednesday", 5, "14:00", "14:50", "Literature", 4, "Room 204", "11B"), 
        ]
        for ts in timetable:
            cursor.execute(
                """INSERT INTO timetable 
                (day, period, start_time, end_time, subject, teacher_id, room, section) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ts
            )

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
