# 🎓 GradingPro — Complete Setup Guide for New Developers

> Follow this guide step-by-step to get GradingPro running on your machine from scratch.
> Estimated time: **15–20 minutes**

---

## ✅ Prerequisites (Install These First)

Before you begin, make sure you have the following installed:

| Tool | Download Link | Why |
|---|---|---|
| **Python 3.11+** | https://www.python.org/downloads/ | The backend language |
| **PostgreSQL 16** | https://www.postgresql.org/download/ | The database |
| **Git** | https://git-scm.com/downloads | To clone the project |
| **pgAdmin 4** *(optional)* | Comes with PostgreSQL installer | GUI to view the DB |

> ⚠️ **Windows users:** When installing Python, check ✅ **"Add Python to PATH"** before clicking Install.

> ⚠️ **PostgreSQL:** During installation, you'll be asked to set a **superuser password** for the `postgres` user. **Remember this password** — you'll need it in Step 4.

---

## 📥 Step 1: Clone the Repository

Open a terminal (Command Prompt / PowerShell / Terminal) and run:

```bash
git clone https://github.com/AnandBhaskarx/Answer-grading-System.git
cd Answer-grading-System
```

---

## 🐍 Step 2: Create a Python Virtual Environment

This keeps the project's packages isolated from your system Python.

```bash
# Create the virtual environment
python -m venv myenv

# Activate it — Windows (PowerShell)
myenv\Scripts\activate

# Activate it — Mac/Linux
source myenv/bin/activate
```

You should now see `(myenv)` at the start of your terminal prompt. ✅

---

## 📦 Step 3: Install All Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, Bcrypt, Google Gemini SDK, and all other required packages.  
It may take 2–3 minutes on the first run.

---

## 🗄️ Step 4: Set Up the PostgreSQL Database

### 4a. Create the Database

Open **pgAdmin 4** (or the PostgreSQL command line) and create a new database named `gradingpro`.

**Using pgAdmin:**
1. Open pgAdmin → expand Servers → right-click **Databases** → **Create → Database**
2. Name it: `gradingpro`
3. Click **Save**

**Using the command line:**
```bash
# Open PostgreSQL shell
psql -U postgres

# Run this command inside the shell
CREATE DATABASE gradingpro;

# Exit
\q
```

### 4b. (Alternative) Use the Helper Script

The project includes a script that creates the database automatically:

```bash
python init_db.py
```

> This requires your `DATABASE_URL` to be set in `.env` first (see Step 5).

---

## 🔑 Step 5: Configure Environment Variables

Copy the example file and fill in your credentials:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Now open the `.env` file in any text editor and fill in your values:

```env
# Replace with your actual PostgreSQL credentials
DATABASE_URL=postgresql://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/gradingpro

# Generate a random secret key (any long random string works)
SECRET_KEY=my-super-secret-random-key-change-this-123456

# Your Google Gemini API Key
GEMINI_API_KEY=your-gemini-api-key-here
```

### How to get a Gemini API Key (Free):
1. Go to → https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key and paste it into `.env`

---

## 🔄 Step 6: Run Database Migrations

This creates all the required tables in your `gradingpro` database automatically:

```bash
flask db upgrade
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade -> f66134563eaa, initial schema
INFO  [alembic.runtime.migration] Running upgrade ... -> 3c90d3a8f1e3, student onboarding
```

If you see errors about `FLASK_APP`, set it first:
```bash
# Windows PowerShell
$env:FLASK_APP = "run.py"

# Windows Command Prompt
set FLASK_APP=run.py

# Mac/Linux
export FLASK_APP=run.py
```

---

## 🚀 Step 7: Run the Application

```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open your browser and go to: **http://localhost:5000** 🎉

---

## 👤 Step 8: Create Your First Account

1. Go to **http://localhost:5000/signup**
2. Register as a **Teacher** (select the Teacher role)
3. Log in → you'll land on the Teacher Dashboard
4. Go to **Manage Classes** → Create your first classroom
5. Go to **Manage Classes → Your Classroom** → Set a **Default Student Password**
6. Go to **Quick Grade Tool** → Create an exam and start evaluating!

---

## 🔧 Troubleshooting

### ❌ `ModuleNotFoundError`
Your virtual environment isn't activated. Run:
```bash
myenv\Scripts\activate   # Windows
source myenv/bin/activate  # Mac/Linux
```

### ❌ `could not connect to server` (Database error)
- Make sure PostgreSQL is running
- Double-check the `DATABASE_URL` in your `.env` file (username, password, port)
- Default PostgreSQL port is `5432`

### ❌ `flask: command not found`
Flask is installed inside the venv. Make sure you've activated it first.

### ❌ `GEMINI_API_KEY` errors during evaluation
- Make sure the key is correctly copied into `.env` (no extra spaces)
- Check your key is valid at https://aistudio.google.com/app/apikey
- The free tier has rate limits — wait a moment and retry

### ❌ PowerShell security error on `myenv\Scripts\activate`
Run this once in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📁 Project Structure (Quick Reference)

```
Answer-grading-System/
├── app/
│   ├── models/         ← Database models (User, Classroom, Student, etc.)
│   ├── routes/         ← All Flask routes (teacher, student, auth, analytics)
│   ├── services/       ← Gemini AI integration, grading logic
│   ├── templates/      ← HTML pages
│   └── static/         ← CSS and images
├── migrations/         ← Database migration scripts (don't edit manually)
├── .env.example        ← Template for your .env file
├── requirements.txt    ← All Python dependencies
├── init_db.py          ← Helper script to create the PostgreSQL database
└── run.py              ← App entry point
```

---

## 📋 Quick Command Reference

```bash
# Start the app
python run.py

# Apply new DB migrations (if you pull updates)
flask db upgrade

# Install new packages (if requirements.txt updated)
pip install -r requirements.txt

# Deactivate virtual environment when done
deactivate
```

---

## 🆘 Still Stuck?

Contact **Anand Bhaskar** or open an issue on the GitHub repository:  
👉 https://github.com/AnandBhaskarx/Answer-grading-System
