<div align="center">

# 🎓 GradingPro

### AI-Powered Answer Sheet Evaluation Platform

*Automate exam grading with Google Gemini AI — from handwritten answer sheets to instant, detailed student reports.*

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org)
[![Gemini AI](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-orange?logo=google)](https://ai.google.dev)

</div>

---

## 📖 Table of Contents

1. [What is GradingPro?](#-what-is-gradingpro)
2. [Features & Functionalities](#-features--functionalities)
3. [Tech Stack](#-tech-stack)
4. [Project Structure](#-project-structure)
5. [Setup Guide](#-setup-guide)
6. [How the Website Works](#-how-the-website-works-user-flows)
7. [API Endpoints](#-key-api-endpoints)
8. [Screenshots](#-screenshots)

---

## 🚀 What is GradingPro?

**GradingPro** is an end-to-end AI-powered exam grading system built for teachers and students. Teachers upload question papers and answer keys; GradingPro uses **Google Gemini 2.5 Flash** to perform OCR on handwritten student answer sheets, compare them against the master answer key, and generate per-question marks with detailed AI feedback — all in seconds.

Students can then log in with their enrollment number to view their scores, question-by-question breakdown, and personalised AI feedback. The entire cycle, from exam creation to result delivery, is managed within GradingPro.

---

## ✨ Features & Functionalities

### 👩‍🏫 Teacher Features

| Feature | Description |
|---|---|
| **Classroom Management** | Create and manage multiple classrooms. Each classroom is isolated with its own students and exams. |
| **Exam Creation** | Upload question papers and master answer keys as PDF or multiple image files. |
| **Multi-File Evaluation** | Upload multi-page student answer booklets (PDF or image sets) for evaluation in one step. |
| **Gemini AI Grading** | Gemini 2.5 Flash performs OCR on handwritten sheets, grades question-by-question, and returns structured JSON results. |
| **Auto Student Onboarding** | If a student doesn't exist, GradingPro auto-creates their login account using the classroom's default password. |
| **Per-Classroom Default Password** | Teachers set a class-wide default password students use for first login, ensuring privacy and control. |
| **Results Dashboard** | High-level results table per exam: student name, score, pass/fail status. |
| **Submission Drill-Down** | Detailed per-student report: extracted answer text, AI feedback, marks per question. |
| **Analytics Dashboard** | Classroom-centric analytics with 4 chart types: avg score bar chart, performance trend line, pass/fail grouped bar, and score grade band distribution. |
| **Per-Exam Analytics** | Drill into a single exam: grade band histogram, pass/fail doughnut, per-question difficulty chart. |
| **At-Risk Detection** | Automatically identifies students averaging below 40% for early intervention. |
| **CSV Export** | One-click download of all submission records with scores, percentages, and AI feedback. |
| **AI Assistant** | Built-in chatbot powered by AI for teaching assistance and Q&A. |

### 🎓 Student Features

| Feature | Description |
|---|---|
| **Enrollment Login** | Log in with enrollment number + class default password — no manual signup required. |
| **Forced Password Change** | On first login, students are required to set a private password before accessing their portal. |
| **Performance Portal** | View all evaluated exams with total scores and pass/fail status. |
| **Detailed Report** | Accordion-style drill-down per exam: AI feedback, per-question breakdown, and marks awarded. |
| **Privacy** | After the mandatory password change, only the student knows their login credentials. |

### 🔒 Security Features

- All passwords hashed with **bcrypt** — original passwords are never stored.
- `.env` file for secrets — never committed to version control.
- Role-based access control (`teacher` / `student`) on all routes.
- `must_change_password` flag enforced at the route level — students cannot bypass the wall.
- AJAX-based student creation — uploaded files are never lost during the enrollment check.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, Flask 3.x |
| **Database** | PostgreSQL 16, SQLAlchemy ORM, Flask-Migrate (Alembic) |
| **AI / ML** | Google Gemini 2.5 Flash (multimodal OCR + grading) |
| **Authentication** | Flask-Login, Flask-Bcrypt |
| **Frontend** | Bootstrap 5, Bootstrap Icons, Chart.js 4 |
| **File Handling** | Werkzeug secure_filename, Google Files API |

---

## 📁 Project Structure

```
gradingpro/
│
├── app/
│   ├── __init__.py              # App factory, extensions
│   ├── models/
│   │   ├── models.py            # User, Classroom, Student, Assignment, Submission
│   │   └── grading.py           # GradingResult model
│   ├── routes/
│   │   ├── auth.py              # Login, signup, logout
│   │   ├── teacher.py           # Dashboard, evaluate, results, classroom mgmt
│   │   ├── student.py           # Student portal, change-password wall
│   │   ├── analytics.py         # Charts API and analytics pages
│   │   ├── main.py              # Landing page
│   │   └── chat.py              # AI assistant chatbot
│   ├── services/
│   │   ├── gemini_service.py    # Gemini API integration (OCR + grading)
│   │   └── grading_service.py   # Legacy NLP grading service
│   ├── templates/
│   │   ├── base.html            # Base layout with sidebar navigation
│   │   ├── analytics.html       # Classroom-level analytics landing
│   │   ├── auth/                # login.html, signup.html
│   │   ├── teacher/             # dashboard, evaluate, results, classroom views
│   │   └── student/             # portal.html, change_password.html
│   ├── static/                  # CSS, JS, images
│   └── uploads/                 # Temporary file storage (gitignored)
│
├── migrations/                  # Alembic migration scripts
├── tests/                       # QA test scripts
├── .env.example                 # Template for environment variables
├── .gitignore
├── requirements.txt
├── init_db.py                   # One-time DB creation utility
├── grading_model.py             # Prototype NLP grading script (historical)
└── run.py                       # App entry point
```

---

## ⚙️ Setup Guide

### Prerequisites
- Python 3.11+
- PostgreSQL 16 (running locally or remotely)
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### 1. Clone the Repository

```bash
git clone https://github.com/AnandBhaskarx/Answer-grading-System.git
cd Answer-grading-System
```

### 2. Create a Virtual Environment

```bash
python -m venv myenv

# Windows
myenv\Scripts\activate

# Mac/Linux
source myenv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/gradingpro
SECRET_KEY=your-very-long-random-secret-key
GEMINI_API_KEY=your-gemini-api-key-here
```

### 5. Create the PostgreSQL Database

```bash
python init_db.py
```

### 6. Run Database Migrations

```bash
flask db upgrade
```

### 7. Start the Server

```bash
python run.py
```

Open your browser at **http://localhost:5000**

---

## 🔄 How the Website Works — User Flows

### Teacher Flow

```
1. Sign up as Teacher → Create a Classroom
2. Manage Classes → Set a Default Student Password for the classroom
3. Create Exam → Upload Question Paper + Answer Key (PDF or images)
4. Evaluate → Enter student enrollment number + upload answer sheet
   └─ If student doesn't exist → auto-created with default password
5. Gemini AI analyzes the handwritten sheet → returns JSON scores
6. View Results → See all students' scores for that exam
7. Drill Down → Per-student: extracted answers, feedback, per-question marks
8. Analytics → Charts: avg score, trend, pass/fail, grade bands, at-risk students
```

### Student Flow

```
1. Teacher evaluates their copy → account auto-created
2. Student logs in with: Enrollment Number + Default Class Password
3. Forced Password Change Wall → must set a new private password (min 8 chars)
4. Lands on Student Portal → sees all evaluated exams
5. Clicks on an exam → accordion drill-down with AI feedback per question
```

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/teacher/dashboard` | Teacher home with KPIs |
| `GET` | `/teacher/classes` | All classrooms |
| `GET` | `/teacher/classes/<id>` | Classroom detail + students |
| `POST` | `/teacher/classes/<id>/set-default-password` | Set classroom default password |
| `POST` | `/teacher/classroom/new` | Create a classroom |
| `GET/POST` | `/teacher/quick-grade` | Create an exam (upload Q paper + answer key) |
| `GET/POST` | `/teacher/evaluate/<id>` | Evaluate a student's answer sheet |
| `POST` | `/teacher/api/student/check-or-create` | AJAX: check/create student account |
| `GET` | `/teacher/assignment/<id>/results` | All results for an exam |
| `GET` | `/teacher/submission/<id>` | Detailed submission drill-down |
| `GET` | `/analytics/` | Analytics landing (classroom cards) |
| `GET` | `/analytics/classroom/<id>` | Classroom-level charts |
| `GET` | `/analytics/classroom/<id>/data` | JSON for classroom charts |
| `GET` | `/analytics/assignment/<id>` | Per-exam analytics |
| `GET` | `/analytics/export` | Download CSV of all results |
| `GET` | `/student/portal` | Student performance portal |
| `GET/POST` | `/student/change-password` | Forced first-login password change |

---

## 🖼 Screenshots

> Screenshots coming soon — the application is fully functional and can be run locally following the setup guide above.

---

## 👥 Contributors

- **Anand Bhaskar** — Final Year Project, 2024–2026

---

## 📄 License

This project is for academic purposes. All rights reserved.
