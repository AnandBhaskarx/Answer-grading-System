"""
chatbot_logic.py
----------------
Chat Router for the AI Grading Assistant.

Intent Detection
----------------
A lightweight keyword-based classifier maps the user message to one of three
intents:

    GRADE      — student wants to grade an answer right now
    ANALYTICS  — teacher wants class statistics / at-risk report
    HISTORY    — student wants their last N submission results

Each intent is handled by a dedicated function that returns a structured
response dict consumed by the chat API endpoint.

Response shape
--------------
{
    "intent"  : str,          # "GRADE" | "ANALYTICS" | "HISTORY" | "UNKNOWN"
    "reply"   : str,          # Plain-text / markdown for the chat bubble
    "data"    : dict | None,  # Optional structured payload (tables, charts, etc.)
}
"""

from __future__ import annotations

import re
from typing import Optional

# ── Intent keyword maps ───────────────────────────────────────────────────────

_GRADE_KW    = {"grade", "evaluate", "mark", "score", "check", "assess", "submit"}
_ANALYTICS_KW = {
    "analytics", "analysis", "average", "mean", "class", "performance",
    "report", "risk", "at-risk", "at risk", "statistics", "stats",
    "overview", "summary", "struggling",
}
_HISTORY_KW  = {
    "history", "previous", "past", "last", "recent", "my grades",
    "my results", "my submissions", "submissions",
}


# ── Intent classifier ─────────────────────────────────────────────────────────

def detect_intent(message: str) -> str:
    """
    Classify the user message into GRADE, ANALYTICS, HISTORY, or UNKNOWN.

    Strategy:
        1. Tokenise the message (lower-case, strip punctuation).
        2. Count keyword hits for each intent class.
        3. Return the class with the highest hit count; ties go to GRADE.
        4. Fall back to UNKNOWN if no keywords match.
    """
    cleaned = re.sub(r"[^\w\s]", " ", message.lower())
    tokens  = set(cleaned.split())
    # Also test bigrams (for "at risk", "my grades", etc.)
    words   = cleaned.split()
    bigrams = {f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)}
    all_terms = tokens | bigrams

    scores = {
        "GRADE":     len(all_terms & _GRADE_KW),
        "ANALYTICS": len(all_terms & _ANALYTICS_KW),
        "HISTORY":   len(all_terms & _HISTORY_KW),
    }

    best_score = max(scores.values())
    if best_score == 0:
        return "UNKNOWN"

    # Priority: ANALYTICS > HISTORY > GRADE on tie
    for intent in ("ANALYTICS", "HISTORY", "GRADE"):
        if scores[intent] == best_score:
            return intent

    return "UNKNOWN"


# ── Intent handlers ───────────────────────────────────────────────────────────

def handle_grade_intent(user_message: str) -> dict:
    """
    Guide the user to the grading tool or prompt them for the required fields.
    The actual grading is done via grade_submission() — not duplicated here.
    """
    return {
        "intent": "GRADE",
        "reply": (
            "Sure! To grade an answer, I need a few details.\n\n"
            "Please use the **Grade Answer** form at the home page (/) or tell me:\n"
            "1. The **Assignment ID**\n"
            "2. Your **Student ID**\n"
            "3. Your **answer** to the question\n\n"
            "Type: `grade assignment_id=<ID> student_id=<ID> answer=<your answer>`"
        ),
        "data": None,
    }


def handle_history_intent(student_id: int, limit: int = 5) -> dict:
    """
    Fetch the last `limit` submissions for the given student.
    Returns a structured reply with a results table.
    """
    from app.models.models import Submission, Assignment

    submissions = (
        Submission.query
        .filter_by(student_id=student_id)
        .order_by(Submission.id.desc())
        .limit(limit)
        .all()
    )

    if not submissions:
        return {
            "intent": "HISTORY",
            "reply": "You haven't submitted any answers yet. Go ahead and submit your first one!",
            "data": None,
        }

    rows = []
    for sub in submissions:
        rows.append({
            "submission_id"  : sub.id,
            "assignment"     : sub.assignment.title if sub.assignment else f"Assignment #{sub.assignment_id}",
            "score"          : f"{sub.score}/10",
            "feedback"       : sub.feedback_summary or "—",
        })

    reply_lines = [f"Here are your last **{len(rows)}** submission(s):\n"]
    for row in rows:
        reply_lines.append(
            f"• **{row['assignment']}** — Score: `{row['score']}`  \n"
            f"  _{row['feedback']}_"
        )

    return {
        "intent": "HISTORY",
        "reply" : "\n".join(reply_lines),
        "data"  : {"submissions": rows},
    }


def handle_analytics_intent(classroom_id: Optional[int] = None) -> dict:
    """
    Compute class-level analytics:
        • Average score across all submissions (or a specific classroom)
        • At-Risk students: avg score < 40% (< 4 out of 10)

    Returns a structured reply with summary statistics.
    """
    from app.models.models import Submission, Student, Classroom
    from sqlalchemy import func
    from app import db

    # ── Build base query ──────────────────────────────────────────────────────
    query = db.session.query(Submission)
    if classroom_id:
        # Join through Student to filter by classroom
        query = (
            db.session.query(Submission)
            .join(Student, Submission.student_id == Student.id)
            .filter(Student.classroom_id == classroom_id)
        )

    all_submissions = query.all()

    if not all_submissions:
        scope = f"classroom #{classroom_id}" if classroom_id else "any classroom"
        return {
            "intent": "ANALYTICS",
            "reply" : f"No submissions found for {scope} yet.",
            "data"  : None,
        }

    # ── Class average ─────────────────────────────────────────────────────────
    total_score = sum(s.score for s in all_submissions if s.score is not None)
    count       = len([s for s in all_submissions if s.score is not None])
    class_avg   = round(total_score / count, 2) if count else 0.0

    # ── Per-student averages (for at-risk detection) ──────────────────────────
    student_scores: dict[int, list[float]] = {}
    for sub in all_submissions:
        if sub.score is not None:
            student_scores.setdefault(sub.student_id, []).append(sub.score)

    at_risk = []
    performing_well = []
    for sid, scores in student_scores.items():
        avg = round(sum(scores) / len(scores), 2)
        student = Student.query.get(sid)
        name    = student.name if student else f"Student #{sid}"
        entry   = {"student_id": sid, "name": name, "avg_score": avg}
        if avg < 4.0:         # < 40% of 10-point scale
            at_risk.append(entry)
        else:
            performing_well.append(entry)

    # ── Build reply ───────────────────────────────────────────────────────────
    scope_label = f"Classroom #{classroom_id}" if classroom_id else "All Classrooms"
    reply_parts = [
        f"📊 **Analytics Report — {scope_label}**\n",
        f"• Total submissions analysed: **{count}**",
        f"• Class average score: **{class_avg}/10**\n",
    ]

    if at_risk:
        reply_parts.append(f"⚠️ **At-Risk Students ({len(at_risk)})** _(avg < 4/10)_:")
        for s in at_risk:
            reply_parts.append(f"  - {s['name']} — avg `{s['avg_score']}/10`")
    else:
        reply_parts.append("✅ No at-risk students detected — great work!")

    return {
        "intent": "ANALYTICS",
        "reply" : "\n".join(reply_parts),
        "data"  : {
            "class_average"     : class_avg,
            "total_submissions" : count,
            "at_risk"           : at_risk,
            "performing_well"   : performing_well,
        },
    }


# ── Main router ───────────────────────────────────────────────────────────────

def route_message(message: str, current_user) -> dict:
    """
    Primary entry point called by the chat API endpoint.

    Args:
        message      : Raw text from the user's chat input.
        current_user : Flask-Login current_user object.

    Returns:
        A response dict  {intent, reply, data}.
    """
    intent = detect_intent(message)

    if intent == "GRADE":
        return handle_grade_intent(message)

    if intent == "HISTORY":
        # Students can only see their own history
        if current_user.role != "student" or not hasattr(current_user, "student_profile"):
            return {
                "intent": "HISTORY",
                "reply" : "History is only available to student accounts. Please log in as a student.",
                "data"  : None,
            }
        student_profile = current_user.student_profile
        if not student_profile:
            return {
                "intent": "HISTORY",
                "reply" : "Your student profile isn't set up yet. Please contact your teacher.",
                "data"  : None,
            }
        return handle_history_intent(student_profile.id)

    if intent == "ANALYTICS":
        # Teachers see analytics for their classrooms
        if current_user.role == "teacher":
            # If teacher has classrooms, analyse the first one (can be extended)
            classrooms = current_user.classrooms
            cid = classrooms[0].id if classrooms else None
            return handle_analytics_intent(classroom_id=cid)
        else:
            return {
                "intent": "ANALYTICS",
                "reply" : "Analytics reports are available to teachers only.",
                "data"  : None,
            }

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    return {
        "intent": "UNKNOWN",
        "reply" : (
            "I'm not sure what you mean. Here's what I can help with:\n\n"
            "• **Grade** — _'Grade my answer for assignment 3'_\n"
            "• **History** — _'Show my last submissions'_\n"
            "• **Analytics** — _'Give me the class performance report'_"
        ),
        "data": None,
    }
