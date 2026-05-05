<div align="center">

# 🎓 GradingPro

### Multi-Layer AI Answer Evaluation Platform

*A hybrid NLP + multimodal AI system that combines OCR-powered text extraction, semantic sentence embeddings, vector similarity scoring, and keyword analysis to evaluate student answers with precision and depth.*

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org)
[![Gemini AI](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-orange?logo=google)](https://ai.google.dev)
[![Sentence Transformers](https://img.shields.io/badge/Sentence--Transformers-SBERT-green?logo=huggingface)](https://www.sbert.net)
[![NLP](https://img.shields.io/badge/NLP-Cosine%20Similarity-purple)](https://scikit-learn.org)

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

**GradingPro** is an end-to-end AI-powered exam grading platform built for teachers and students. At its core, it uses a **two-layer hybrid evaluation pipeline** that goes well beyond a simple API call:

**Layer 1 — Multimodal OCR & Contextual Grading (Google Gemini 2.5 Flash):**  
Handwritten or typed student answer sheets are uploaded alongside the question paper and master answer key. Gemini performs deep multimodal reasoning — it reads all pages of the answer booklet, understands the context of each question, and extracts the student's written responses through OCR. It then evaluates each answer question-by-question against the master key, returning structured JSON scores and per-question feedback.

**Layer 2 — Semantic NLP Evaluation Pipeline (Local SBERT + Vector Similarity):**  
Extracted answers are further processed through a local NLP pipeline:
1. **Text Chunking** — Answers are segmented into meaningful units for granular comparison.
2. **Sentence Embeddings** — Each chunk is encoded into a high-dimensional vector using **`all-MiniLM-L6-v2`** from the `sentence-transformers` library (SBERT), capturing the *semantic meaning* of the text rather than just keywords.
3. **Cosine Similarity Scoring** — The student's answer vector is compared against the model answer vector using **cosine similarity**, producing a similarity score between 0 and 1 that reflects conceptual alignment regardless of exact wording.
4. **Keyword Detection** — A secondary pass scans the student answer for domain-specific keywords defined by the teacher, identifying which key concepts were included and which were missed.
5. **Composite Feedback Generation** — Similarity score and keyword analysis are combined to produce rich, human-readable feedback that tells the student exactly where they lost marks and why.

This dual-layer approach ensures that even partial answers, paraphrased responses, or semantically equivalent but differently worded answers receive fair scores — going far beyond simple string matching. Students can then log in with their enrollment number to view their scores, per-question breakdown, similarity metrics, and personalised AI feedback. The entire cycle, from exam creation to result delivery, is managed within GradingPro.

---

## ✨ Features & Functionalities

### 👩‍🏫 Teacher Features

| Feature | Description |
|---|---|
| **Classroom Management** | Create and manage multiple classrooms. Each classroom is isolated with its own students and exams. |
| **Exam Creation** | Upload question papers and master answer keys as PDF or multiple image files. |
| **Multi-File Evaluation** | Upload multi-page student answer booklets (PDF or image sets) for evaluation in one step. |
| **Gemini OCR & Contextual Scoring** | Gemini 2.5 Flash reads handwritten answer sheets, performs multimodal OCR, understands question context, and returns structured per-question JSON results. |
| **Semantic Similarity Engine** | Uses SBERT (`all-MiniLM-L6-v2`) to encode both student and model answers into sentence embeddings, then computes cosine similarity to measure conceptual alignment — not just surface text matching. |
| **Text Chunking Pipeline** | Long answers are chunked into segments before encoding, ensuring that multi-part answers are evaluated holistically across all their components. |
| **Keyword Analysis** | Teacher-defined domain keywords are scanned for in each submission. Missing and found keywords are tracked and surfaced in feedback to help students understand gaps in their knowledge. |
| **Composite Feedback** | Similarity score and keyword coverage are combined to generate detailed, human-readable feedback per question. |
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
| **Multimodal AI (OCR)** | Google Gemini 2.5 Flash — reads handwritten answer sheets, performs visual OCR, and contextual question-by-question grading |
| **Sentence Embeddings** | `sentence-transformers` — `all-MiniLM-L6-v2` SBERT model encodes answers into 384-dimensional semantic vectors |
| **Vector Similarity** | PyTorch + `util.cos_sim` — cosine similarity between student and model answer embeddings for semantic scoring |
| **Text Generation** | Hugging Face `transformers` pipeline (GPT-2) — for AI-generated model answer suggestions |
| **NLP & Keyword Analysis** | Custom keyword detection pipeline — identifies found/missing domain-specific terms per submission |
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
│   │   ├── gemini_service.py    # Gemini 2.5 Flash: multimodal OCR, file upload, contextual grading
│   │   └── grading_service.py   # Local NLP pipeline: SBERT embeddings, cosine similarity, keyword analysis
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
5. Evaluation Pipeline runs automatically:
   ├─ Gemini 2.5 Flash performs OCR on the uploaded answer sheet
   ├─ Extracted answers are chunked and encoded into SBERT sentence embeddings
   ├─ Cosine similarity is computed between student and model answer vectors
   ├─ Keyword detection scans for found/missing domain concepts
   └─ Composite score + detailed feedback generated per question
6. View Results → See all students' scores for that exam
7. Drill Down → Per-student: extracted answer text, similarity scores, keyword coverage, AI feedback, marks
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
