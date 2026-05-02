"""
analytics.py — /analytics blueprint
------------------------------------
Routes:
    GET /analytics/                          → High-level classroom cards landing
    GET /analytics/classroom/<id>            → Per-classroom analytics page
    GET /analytics/classroom/<id>/data       → JSON for classroom charts
    GET /analytics/assignment/<id>           → Per-exam analytics page
    GET /analytics/assignment/<id>/data      → JSON for exam charts
    GET /analytics/export                    → CSV download
"""

import csv
import io
from flask import Blueprint, render_template, jsonify, Response, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.models import Assignment, Submission, Student, Classroom

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


# ── Helpers ────────────────────────────────────────────────────────────────────

def _classroom_summary(classroom_id: int) -> dict:
    """KPI stats for a single classroom."""
    subs = (
        db.session.query(Submission.score, Assignment.max_marks, Assignment.passing_percentage)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Assignment.classroom_id == classroom_id)
        .all()
    )
    total_students = db.session.query(func.count(Student.id)).filter_by(classroom_id=classroom_id).scalar() or 0
    total_assignments = db.session.query(func.count(Assignment.id)).filter_by(classroom_id=classroom_id).scalar() or 0

    if not subs:
        return {
            "total_submissions": 0, "total_students": int(total_students),
            "total_assignments": int(total_assignments), "avg_pct": 0.0, "pass_rate": 0.0
        }

    pcts = [(s / m * 100) for s, m, _ in subs if m]
    passed = sum(1 for s, m, p in subs if m and (s / m * 100) >= p)
    return {
        "total_submissions": len(subs),
        "total_students": int(total_students),
        "total_assignments": int(total_assignments),
        "avg_pct": round(sum(pcts) / len(pcts), 1) if pcts else 0.0,
        "pass_rate": round(passed / len(subs) * 100, 1) if subs else 0.0,
    }


def _bar_chart(classroom_id: int) -> dict:
    rows = (
        db.session.query(Assignment.title, Assignment.max_marks,
                         func.round(func.avg(Submission.score), 2).label('avg'),
                         func.count(Submission.id).label('cnt'))
        .join(Submission, Submission.assignment_id == Assignment.id)
        .filter(Assignment.classroom_id == classroom_id)
        .group_by(Assignment.id, Assignment.title, Assignment.max_marks)
        .order_by(Assignment.id).all()
    )
    return {
        "labels": [r.title for r in rows],
        "values": [round(float(r.avg) / float(r.max_marks) * 100, 1) if r.avg and r.max_marks else 0 for r in rows],
        "counts": [r.cnt for r in rows],
    }


def _line_chart(classroom_id: int) -> dict:
    rows = (
        db.session.query(
            func.date_trunc('day', Submission.created_at).label('day'),
            func.round(func.avg(Submission.score), 2).label('avg'),
            func.round(func.avg(Assignment.max_marks), 2).label('avg_max'),
        )
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Student.classroom_id == classroom_id)
        .group_by('day').order_by('day').all()
    )
    return {
        "labels": [r.day.strftime('%b %d') for r in rows if r.day],
        "values": [round(float(r.avg) / float(r.avg_max) * 100, 1) if r.avg and r.avg_max else 0 for r in rows if r.day],
    }


def _pass_fail(classroom_id: int) -> dict:
    assignments = Assignment.query.filter_by(classroom_id=classroom_id).all()
    labels, pass_counts, fail_counts = [], [], []
    for a in assignments:
        if not a.submissions:
            continue
        threshold = a.max_marks * (a.passing_percentage / 100.0)
        passed = sum(1 for s in a.submissions if s.score >= threshold)
        labels.append(a.title)
        pass_counts.append(passed)
        fail_counts.append(len(a.submissions) - passed)
    return {"labels": labels, "pass": pass_counts, "fail": fail_counts}


def _score_distribution(classroom_id: int) -> dict:
    subs = (
        db.session.query(Submission.score, Assignment.max_marks)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Assignment.classroom_id == classroom_id).all()
    )
    bands = {"0–39%": 0, "40–59%": 0, "60–74%": 0, "75–89%": 0, "90–100%": 0}
    for score, max_marks in subs:
        if not max_marks:
            continue
        pct = (score / max_marks) * 100
        if pct < 40: bands["0–39%"] += 1
        elif pct < 60: bands["40–59%"] += 1
        elif pct < 75: bands["60–74%"] += 1
        elif pct < 90: bands["75–89%"] += 1
        else: bands["90–100%"] += 1
    return {"labels": list(bands.keys()), "values": list(bands.values())}


def _at_risk(classroom_id: int) -> list:
    rows = (
        db.session.query(
            Student.name, Student.email, Student.enrollment_number,
            func.round(func.avg(Submission.score), 2).label('avg'),
            func.round(func.avg(Assignment.max_marks), 2).label('avg_max'),
            func.count(Submission.id).label('cnt'),
        )
        .join(Submission, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Student.classroom_id == classroom_id)
        .group_by(Student.id, Student.name, Student.email, Student.enrollment_number).all()
    )
    result = []
    for r in rows:
        if r.avg_max and r.avg:
            pct = float(r.avg) / float(r.avg_max) * 100
            if pct < 40:
                result.append({"name": r.name, "email": r.email or "—", "enrollment": r.enrollment_number, "avg_pct": round(pct, 1), "submissions": r.cnt})
    result.sort(key=lambda x: x["avg_pct"])
    return result


# ── Per-Exam helpers ───────────────────────────────────────────────────────────

def _exam_summary_data(assignment_id: int) -> dict:
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
    if not submissions:
        return {"error": "no_data"}

    pcts = [round(s.score / assignment.max_marks * 100, 1) if assignment.max_marks else 0 for s in submissions]
    passed = sum(1 for p in pcts if p >= assignment.passing_percentage)
    bands = {"0–39%": 0, "40–59%": 0, "60–74%": 0, "75–89%": 0, "90–100%": 0}
    for p in pcts:
        if p < 40: bands["0–39%"] += 1
        elif p < 60: bands["40–59%"] += 1
        elif p < 75: bands["60–74%"] += 1
        elif p < 90: bands["75–89%"] += 1
        else: bands["90–100%"] += 1

    q_totals = {}
    for sub in submissions:
        if sub.detailed_analysis:
            for q in sub.detailed_analysis:
                qn = str(q.get("question_number", "?"))
                awarded = float(q.get("marks_awarded", 0))
                max_q = float(q.get("max_marks_for_question", 0))
                if qn not in q_totals:
                    q_totals[qn] = {"total": 0, "max": max_q, "count": 0}
                q_totals[qn]["total"] += awarded
                q_totals[qn]["count"] += 1

    q_labels = sorted(q_totals.keys(), key=lambda x: int(x) if x.isdigit() else 0)
    q_avg_pcts = []
    for qn in q_labels:
        d = q_totals[qn]
        q_avg_pcts.append(round(d["total"] / d["count"] / d["max"] * 100, 1) if d["max"] and d["count"] else 0)

    return {
        "summary": {
            "total": len(submissions), "passed": passed, "failed": len(submissions) - passed,
            "avg_pct": round(sum(pcts) / len(pcts), 1),
            "highest_pct": round(max(pcts), 1), "lowest_pct": round(min(pcts), 1),
            "pass_rate": round(passed / len(submissions) * 100, 1),
        },
        "distribution": {"labels": list(bands.keys()), "values": list(bands.values())},
        "per_question": {"labels": [f"Q{q}" for q in q_labels], "values": q_avg_pcts},
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@analytics_bp.route('/')
@login_required
def dashboard():
    if current_user.role != 'teacher':
        flash('Analytics are available to teachers only.', 'warning')
        return redirect(url_for('student.portal'))
    classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
    summaries = {c.id: _classroom_summary(c.id) for c in classrooms}
    return render_template('analytics.html', classrooms=classrooms, summaries=summaries)


@analytics_bp.route('/classroom/<int:classroom_id>')
@login_required
def classroom_analytics(classroom_id):
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('student.portal'))
    classroom = Classroom.query.get_or_404(classroom_id)
    if classroom.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('analytics.dashboard'))
    return render_template('teacher/classroom_analytics.html', classroom=classroom)


@analytics_bp.route('/classroom/<int:classroom_id>/data')
@login_required
def classroom_analytics_data(classroom_id):
    if current_user.role != 'teacher':
        return jsonify({"error": "Forbidden"}), 403
    classroom = Classroom.query.get_or_404(classroom_id)
    if classroom.teacher_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({
        "summary":      _classroom_summary(classroom_id),
        "bar":          _bar_chart(classroom_id),
        "line":         _line_chart(classroom_id),
        "pass_fail":    _pass_fail(classroom_id),
        "distribution": _score_distribution(classroom_id),
        "at_risk":      _at_risk(classroom_id),
    })


@analytics_bp.route('/assignment/<int:assignment_id>')
@login_required
def exam_analytics(assignment_id):
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('student.portal'))
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.classroom.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
    return render_template('teacher/exam_analytics.html', assignment=assignment)


@analytics_bp.route('/assignment/<int:assignment_id>/data')
@login_required
def exam_analytics_data(assignment_id):
    if current_user.role != 'teacher':
        return jsonify({"error": "Forbidden"}), 403
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.classroom.teacher_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(_exam_summary_data(assignment_id))


@analytics_bp.route('/dashboard-data')
@login_required
def dashboard_data():
    if current_user.role != 'teacher':
        return jsonify({"error": "Forbidden"}), 403
    cids = [c.id for c in current_user.classrooms]
    if not cids:
        return jsonify({"stats": {"total_submissions": 0, "overall_avg_pct": 0.0, "total_students": 0, "total_assignments": 0, "pass_rate": 0.0}, "recent": []})

    all_subs = (
        db.session.query(Submission.score, Assignment.max_marks, Assignment.passing_percentage)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(Student, Submission.student_id == Student.id)
        .filter(Student.classroom_id.in_(cids)).all()
    )
    pcts = [(s / m * 100) for s, m, _ in all_subs if m]
    passed_all = sum(1 for s, m, p in all_subs if m and (s / m * 100) >= p)
    total_students = db.session.query(func.count(Student.id)).filter(Student.classroom_id.in_(cids)).scalar() or 0
    total_assignments = db.session.query(func.count(Assignment.id)).filter(Assignment.classroom_id.in_(cids)).scalar() or 0

    stats = {
        "total_submissions": len(all_subs),
        "overall_avg_pct": round(sum(pcts) / len(pcts), 1) if pcts else 0.0,
        "total_students": int(total_students),
        "total_assignments": int(total_assignments),
        "pass_rate": round(passed_all / len(all_subs) * 100, 1) if all_subs else 0.0,
    }

    recent_rows = (
        db.session.query(Submission, Student, Assignment)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Student.classroom_id.in_(cids))
        .order_by(Submission.created_at.desc()).limit(6).all()
    )
    recent = []
    for sub, stu, asgn in recent_rows:
        pct = round(sub.score / asgn.max_marks * 100, 1) if asgn.max_marks else 0
        recent.append({
            "student_name": stu.name, "enrollment": stu.enrollment_number,
            "exam_title": asgn.title, "score": sub.score, "max_marks": asgn.max_marks,
            "pct": pct, "passed": pct >= asgn.passing_percentage,
            "date": sub.created_at.strftime('%b %d, %Y') if sub.created_at else "—",
            "submission_id": sub.id,
        })
    return jsonify({"stats": stats, "recent": recent})


@analytics_bp.route('/export')
@login_required
def export_csv():
    if current_user.role != 'teacher':
        flash('Only teachers can export reports.', 'danger')
        return redirect(url_for('student.portal'))
    cids = [c.id for c in current_user.classrooms]
    rows = (
        db.session.query(
            Submission.id, Student.name, Student.enrollment_number, Student.email,
            Assignment.title, Assignment.max_marks, Submission.score,
            Submission.feedback_summary, Submission.created_at,
        )
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Student.classroom_id.in_(cids))
        .order_by(Submission.created_at.desc()).all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Student', 'Enrollment', 'Email', 'Assignment', 'Score', 'Max Marks', 'Score %', 'Feedback', 'Evaluated At'])
    for r in rows:
        pct = round(r.score / r.max_marks * 100, 1) if r.max_marks else 0
        writer.writerow([r.id, r.name, r.enrollment_number, r.email, r.title, r.score, r.max_marks, f"{pct}%", r.feedback_summary, r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=grading_report.csv'})
