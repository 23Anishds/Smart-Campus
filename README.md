# Smart-Campus
# EduSync — Smart Classroom Management System

A comprehensive web-based **Smart Classroom Management System** built with **Python, Flask, SQLite, HTML5, CSS, and JavaScript**. EduSync provides dedicated workflows for **Students, Teachers, and Administrators**, bringing attendance, academics, examinations, timetables, analytics, finance, and placements into a single platform.

## Features

* **Role-Based Access** — Dedicated dashboards and permissions for Students, Teachers, and Admins
* **Student Portal** — View assignments, attendance statistics, timetable, academic information, and AI Study Buddy
* **Student Registration** — Four-step registration covering personal, academic, guardian, and document information
* **Teacher Dashboard** — Manage classes, mark attendance using QR codes, manage assignments, and view timetables
* **Admin Panel** — Centralized management of students, faculty, classes, examinations, finance, placements, and reports
* **Academic Analytics** — Visualize performance trends, attendance statistics, department comparisons, and student risk indicators
* **Timetable Management** — Weekly timetable with schedule and conflict detection
* **Examination Management** — Schedule examinations, assign halls and invigilators, generate hall tickets, and persist examination data
* **Attendance Management** — Live attendance overview, defaulter identification, and exportable reports
* **AI Study Buddy** — Chat-based academic assistance for students
* **Finance Management** — Track fee collection and generate financial reports
* **Placement Management** — Maintain and track student placement records
* **Bulk Import** — Upload student and faculty data through CSV files
* **Secure Authentication** — Password hashing and session-based authentication with role-based authorization

## Tech Stack

| Layer              | Technology                             |
| ------------------ | -------------------------------------- |
| Backend            | Python 3, Flask 3.0                    |
| Authentication     | Flask Sessions, Werkzeug               |
| Database           | SQLite                                 |
| Frontend           | HTML5, Vanilla CSS, Vanilla JavaScript |
| UI Styling         | Vanilla CSS, Tailwind CSS CDN          |
| Data Visualization | Chart.js                               |                                 |
| Templating         | Jinja2                                 |
| Architecture       | Flask Blueprints + OOP                 |
| Data Import        | CSV                                    |

## Architecture

EduSync follows a modular **Flask Blueprint architecture** where each major system module is separated into its own routing layer.

### Backend Architecture

* **Blueprint-Based Routing** — Authentication, Admin, Students, Teachers, Portal, and other modules are implemented as independent Flask Blueprints
* **OOP-Based Models** — Student, Teacher, and other entities are represented using reusable Python classes and inheritance
* **Database Layer** — Centralized SQLite connection management through `database/connection.py`
* **Database Seeding** — `database/seed.py` creates the schema and populates initial/sample data
* **Authentication & Authorization** — Decorators control authenticated access and role-specific permissions
* **API Responses** — Common API response handling is centralized through reusable decorators/utilities

## Setup

### Prerequisites

* Python 3.10+
* pip
* Git
* Modern web browser

### Backend

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project
cd smart-classroom

# Create a virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Database

Initialize the SQLite database and sample data:

```bash
python database/seed.py
```

### Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Project Structure

```text
smart-classroom/
├── app.py                       # Application entry point and blueprint registration
├── config.py                    # Application configuration
├── requirements.txt             # Python dependencies
│
├── database/
│   ├── connection.py            # SQLite connection manager
│   └── seed.py                  # Database schema and sample data
│
├── models/
│   ├── base.py                  # Base model
│   ├── student.py               # Student model
│   ├── teacher.py               # Teacher model
│   └── ...                      # Other OOP models
│
├── routes/
│   ├── auth.py                  # Authentication routes
│   ├── admin.py                 # Admin routes
│   ├── students.py              # Student management
│   ├── teachers.py              # Teacher management
│   ├── portal.py                # Student/teacher portal
│   └── ...                      # Other feature blueprints
│
├── templates/
│   ├── ...                      # Jinja2 HTML templates
│
├── static/
│   ├── js/                      # Frontend JavaScript
│   └── ...                      # CSS and static assets
│
└── uploads/
    └── ...                      # Uploaded CSVs and documents
```

## User Roles

### 👨‍🎓 Student

Students can:

* View their dashboard
* Check attendance
* View assignments
* Access their timetable
* View academic performance
* Check their risk indicators
* Interact with the AI Study Buddy
* Complete/update their profile

### 👩‍🏫 Teacher

Teachers can:

* Manage assigned classes
* Manage assignments
* View student attendance
* Access timetables
* Monitor class performance

### 🛡️ Admin

Administrators can:

* Manage students and faculty
* Manage classes and departments
* Schedule examinations
* Assign examination halls and invigilators
* Generate hall tickets
* Manage finances
* Track placements
* View institutional analytics
* Generate reports
* Perform bulk CSV imports

## Core Modules

| Module             | Function                                              |
| ------------------ | ----------------------------------------------------- |
| Authentication     | Login, sessions, password hashing, role authorization |
| Student Management | Student registration, profiles, academics             |
| Teacher Management | Faculty records and class management                  |            |
| Timetable          | Weekly scheduling and conflict detection              |
| Examinations       | Exam scheduling, halls, invigilators, hall tickets    |
| Analytics          | Academic and attendance visualization                 |
| AI Study Buddy     | Interactive academic assistance                       |
| Finance            | Fee management and financial reporting                |
| Placements         | Student placement tracking                            |
| Bulk Import        | CSV-based student/faculty registration                |
| Administration     | Centralized institutional management                  |

## Security

EduSync implements several application-level security mechanisms:

* Password hashing using **Werkzeug**
* Session-based authentication
* Role-based authorization
* Protected routes using custom decorators
* Controlled file uploads
* Configurable upload limits
* Centralized application configuration

## Key Technologies & Libraries

### Flask

Used as the primary backend framework for routing, session management, request handling, and modular Blueprint architecture.

### SQLite

Provides a lightweight relational database suitable for development, demonstration, and educational deployments.

### Chart.js

Used to create interactive analytics dashboards and visualize attendance and academic performance.


## Future Enhancements

Potential improvements for EduSync include:

* **AI-Based At-Risk Student Prediction**
* **Mobile Application**
* **Parent Portal**
* **Real-Time Notifications**
* **Email/SMS Alerts**
* **Advanced Learning Analytics**
* **Cloud Database Deployment**
* **Online Examination System**
* **AI-Powered Personalized Learning Recommendations**

## License

This project is developed for **educational and demonstration purposes**.
