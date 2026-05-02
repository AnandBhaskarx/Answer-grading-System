"""
grading_service.py
------------------
Core AI grading logic.

Public API:
    grade_submission(student_answer, assignment_id, student_id) -> Submission
        Compares student_answer against the assignment's model_answer using SBERT,
        detects missing keywords, generates rich feedback, and persists the result
        to the PostgreSQL Submission table.
"""

from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# ── Model loading (singleton — loaded once at import time) ────────────────────
_sbert = SentenceTransformer('all-MiniLM-L6-v2')
_gpt2 = pipeline('text-generation', model='gpt2')


# ── Public helpers ────────────────────────────────────────────────────────────

def generate_ai_model_answer(question: str) -> str:
    """Generate an AI model answer for a question using GPT-2."""
    result = _gpt2(question, max_length=100, num_return_sequences=1)
    return result[0]['generated_text']


def compare_answers(model_answer: str, student_answer: str) -> float:
    """Return the cosine similarity (0-1) between two answer strings via SBERT."""
    emb_ref = _sbert.encode(model_answer, convert_to_tensor=True)
    emb_stu = _sbert.encode(student_answer, convert_to_tensor=True)
    return float(util.cos_sim(emb_ref, emb_stu).item())


def _detect_keywords(student_answer: str, keywords: list) -> tuple[list, list]:
    """
    Scan student_answer for each keyword (case-insensitive).
    Returns (found_keywords, missing_keywords).
    """
    found, missing = [], []
    lower_answer = student_answer.lower()
    for kw in keywords:
        if kw.lower() in lower_answer:
            found.append(kw)
        else:
            missing.append(kw)
    return found, missing


def _build_feedback(similarity: float, found: list, missing: list) -> str:
    """
    Compose a human-readable feedback string.

    Format:
        "[Base sentence]. You missed the concept of [X, Y], but correctly
         identified [A, B]."
    """
    # Base sentence from similarity
    if similarity > 0.85:
        base = "Excellent answer — it closely matches the expected response."
    elif similarity > 0.65:
        base = "Good attempt, but there is room for improvement."
    elif similarity > 0.45:
        base = "Partial answer. Several key ideas are missing."
    else:
        base = "The answer needs significant improvement."

    parts = [base]

    if missing and found:
        parts.append(
            f"You missed the concept of {_list_str(missing)}, "
            f"but correctly identified {_list_str(found)}."
        )
    elif missing:
        parts.append(f"You missed the concept of {_list_str(missing)}.")
    elif found:
        parts.append(f"You correctly identified all key concepts: {_list_str(found)}.")

    return " ".join(parts)


def _list_str(items: list) -> str:
    """Format ['a', 'b', 'c'] → 'a, b and c'."""
    if len(items) == 1:
        return f"'{items[0]}'"
    return ", ".join(f"'{i}'" for i in items[:-1]) + f" and '{items[-1]}'"


# ── Main grading function ─────────────────────────────────────────────────────

def grade_submission(student_answer: str, assignment_id: int, student_id: int):
    """
    Full grading pipeline:
        1. Fetch Assignment (model_answer + keywords) from DB.
        2. Compute SBERT similarity score.
        3. Detect found / missing keywords.
        4. Build rich feedback string.
        5. Persist Submission to PostgreSQL.
        6. Return the saved Submission object.

    Raises ValueError if the assignment does not exist.
    """
    # Avoid circular imports by importing inside function
    from app import db
    from app.models.models import Assignment, Submission

    # 1 — Fetch assignment
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        raise ValueError(f"Assignment {assignment_id} not found.")

    model_answer = assignment.model_answer or ""
    keywords = assignment.keywords or []

    # 2 — SBERT similarity
    similarity = compare_answers(model_answer, student_answer) if model_answer else 0.0

    # 3 — Keyword analysis
    found, missing = _detect_keywords(student_answer, keywords)

    # 4 — Score (0-10 scale, rounded to 2dp)
    score = round(similarity * 10, 2)

    # 5 — Build feedback
    feedback_summary = _build_feedback(similarity, found, missing)

    # 6 — Detailed analysis payload (stored as JSONB)
    detailed_analysis = {
        "similarity_score": similarity,
        "score_out_of_10": score,
        "keywords_found": found,
        "keywords_missing": missing,
        "model_answer_used": model_answer,
    }

    # 7 — Persist to DB
    submission = Submission(
        student_answer=student_answer,
        score=score,
        feedback_summary=feedback_summary,
        detailed_analysis=detailed_analysis,
        assignment_id=assignment_id,
        student_id=student_id,
    )
    db.session.add(submission)
    db.session.commit()

    return submission
