from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.models import Classroom, Assignment, Student, Submission, User
from app import db, bcrypt
from app.services.grading_service import generate_ai_model_answer, compare_answers, _build_feedback, _detect_keywords
from app.models.grading import GradingResult

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))
    
    # Fetch classrooms belonging to this teacher
    classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
    
    # Fetch all assignments belonging to the teacher's classrooms
    classroom_ids = [c.id for c in classrooms]
    assignments = Assignment.query.filter(Assignment.classroom_id.in_(classroom_ids)).order_by(Assignment.id.desc()).all() if classroom_ids else []
    
    return render_template('teacher/dashboard.html', classrooms=classrooms, assignments=assignments)

@teacher_bp.route('/classroom/new', methods=['POST'])
@login_required
def create_classroom():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('student.portal'))
        
    name = request.form.get('name')
    if name:
        classroom = Classroom(name=name, teacher_id=current_user.id)
        db.session.add(classroom)
        db.session.commit()
        flash(f"Classroom '{name}' created successfully!", "success")
    else:
        flash("Classroom name is required.", "danger")
        
    return redirect(url_for('teacher.manage_classes'))

@teacher_bp.route('/classes')
@login_required
def manage_classes():
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))
    classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/manage_classes.html', classrooms=classrooms)

@teacher_bp.route('/classes/<int:classroom_id>')
@login_required
def classroom_detail(classroom_id):
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))
    classroom = Classroom.query.get_or_404(classroom_id)
    if classroom.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.manage_classes'))
    students = Student.query.filter_by(classroom_id=classroom_id).all()
    assignments = Assignment.query.filter_by(classroom_id=classroom_id).order_by(Assignment.id.desc()).all()
    return render_template('teacher/classroom_detail.html', classroom=classroom, students=students, assignments=assignments)

import os
from werkzeug.utils import secure_filename
from flask import current_app

@teacher_bp.route('/quick-grade', methods=['GET', 'POST'])
@login_required
def quick_grade():
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))
        
    # Fetch classrooms for the dropdown
    classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        max_marks = request.form.get("max_marks", 100.0, type=float)
        passing_percentage = request.form.get("passing_percentage", 40.0, type=float)
        classroom_id = request.form.get("classroom_id")

        question_papers = request.files.getlist("question_paper")
        answer_keys = request.files.getlist("answer_key")

        if not classroom_id:
            flash("Please select a classroom.", "danger")
            return redirect(url_for("teacher.quick_grade"))

        if not question_papers or not answer_keys or not question_papers[0].filename or not answer_keys[0].filename:
            flash("Both Question Paper and Answer Key documents are required.", "danger")
            return redirect(url_for("teacher.quick_grade"))

        # Setup uploads directory
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        qp_paths = []
        for qp in question_papers:
            if qp.filename:
                qp_filename = secure_filename(qp.filename)
                qp_path = os.path.join(uploads_dir, qp_filename)
                qp.save(qp_path)
                qp_paths.append(qp_path)

        ak_paths = []
        for ak in answer_keys:
            if ak.filename:
                ak_filename = secure_filename(ak.filename)
                ak_path = os.path.join(uploads_dir, ak_filename)
                ak.save(ak_path)
                ak_paths.append(ak_path)

        # Create Assignment
        try:
            assignment = Assignment(
                title=title,
                description=description,
                max_marks=max_marks,
                passing_percentage=passing_percentage,
                question_paper_paths=qp_paths,
                answer_key_paths=ak_paths,
                classroom_id=classroom_id
            )
            db.session.add(assignment)
            db.session.commit()
            flash(f"Exam '{title}' successfully created! Documents are embedded and ready for grading.", "success")
            return redirect(url_for("teacher.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("teacher.quick_grade"))

    # If teacher has no classrooms, redirect them to dashboard to create one
    if not classrooms:
        flash("You must create a classroom first before you can create an exam.", "warning")
        return redirect(url_for("teacher.dashboard"))

    return render_template("teacher/quick_grade.html", classrooms=classrooms)

from app.services.gemini_service import evaluate_answer_sheet

@teacher_bp.route('/evaluate/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def evaluate_copies(assignment_id):
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))

    assignment = Assignment.query.get_or_404(assignment_id)

    if request.method == 'POST':
        enrollment_number = request.form.get('enrollment_number')
        student_files = request.files.getlist('student_files')

        # Find student
        student = Student.query.filter_by(enrollment_number=enrollment_number).first()
        if not student:
            flash(f"Student with enrollment number '{enrollment_number}' not found.", "danger")
            return redirect(url_for('teacher.evaluate_copies', assignment_id=assignment.id))

        if not student_files or not student_files[0].filename:
            flash("Please upload the student's answer sheet documents.", "danger")
            return redirect(url_for('teacher.evaluate_copies', assignment_id=assignment.id))

        # Save student files
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        saved_student_paths = []
        for i, file in enumerate(student_files):
            if file.filename:
                img_filename = secure_filename(f"{student.id}_{assignment.id}_{i}_{file.filename}")
                img_path = os.path.join(uploads_dir, img_filename)
                file.save(img_path)
                saved_student_paths.append(img_path)

        if not assignment.question_paper_paths or not assignment.answer_key_paths:
            flash("This assignment is missing its master documents (likely created before the recent system update). Please create a new assignment.", "warning")
            return redirect(url_for('teacher.evaluate_copies', assignment_id=assignment.id))

        try:
            # Call Gemini
            result = evaluate_answer_sheet(
                student_file_paths=saved_student_paths,
                question_paper_paths=assignment.question_paper_paths,
                answer_key_paths=assignment.answer_key_paths,
                max_marks=assignment.max_marks,
                passing_percentage=assignment.passing_percentage
            )

            # Persist to database
            submission = Submission(
                student_answer="<Extracted by Gemini AI>",  # Legacy text field
                score=result.get('total_score', 0),
                feedback_summary=result.get('overall_feedback', ''),
                detailed_analysis=result.get('questions', []),
                answer_sheet_paths=saved_student_paths,
                assignment_id=assignment.id,
                student_id=student.id
            )
            db.session.add(submission)
            db.session.commit()

            flash(f"Successfully graded copy for {student.name}. Score: {submission.score}/{assignment.max_marks}", "success")
            return redirect(url_for('teacher.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error during Gemini AI Evaluation: {str(e)}", "danger")
            return redirect(url_for('teacher.evaluate_copies', assignment_id=assignment.id))

    return render_template('teacher/evaluate.html', assignment=assignment)

@teacher_bp.route('/api/student/check-or-create', methods=['POST'])
@login_required
def check_or_create_student():
    """Called by AJAX before evaluation. Creates a full student account if missing."""
    if current_user.role != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    enrollment_number = (data.get('enrollment_number') or '').strip()
    assignment_id     = data.get('assignment_id')
    create_if_missing = data.get('create_if_missing', False)

    if not enrollment_number or not assignment_id:
        return jsonify({"error": "Missing parameters"}), 400

    student = Student.query.filter_by(enrollment_number=enrollment_number).first()
    if student:
        return jsonify({"exists": True, "student_id": student.id})

    if not create_if_missing:
        return jsonify({"exists": False})

    # ── Create full account ───────────────────────────────────────────────────
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return jsonify({"error": "Invalid assignment"}), 404

    classroom = Classroom.query.get(assignment.classroom_id)

    # Check classroom has a default password set
    if not classroom or not classroom.default_password:
        return jsonify({
            "error": "no_default_password",
            "message": f"Please set a default password for '{classroom.name}' before evaluating. Go to Manage Classes → {classroom.name}."
        }), 400

    # Create the User login account
    placeholder_email = f"{enrollment_number}@student.gradepro"
    existing_user = User.query.filter_by(email=placeholder_email).first()
    if existing_user:
        # Edge case: user exists but no student row
        new_student = Student(
            enrollment_number=enrollment_number,
            name=f"Student {enrollment_number}",
            classroom_id=classroom.id,
            user_id=existing_user.id
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify({"exists": True, "student_id": new_student.id, "created": True})

    new_user = User(
        username=enrollment_number,
        email=placeholder_email,
        password_hash=classroom.default_password,   # already bcrypt-hashed
        role='student',
        must_change_password=True
    )
    db.session.add(new_user)
    db.session.flush()

    new_student = Student(
        enrollment_number=enrollment_number,
        name=f"Student {enrollment_number}",
        classroom_id=classroom.id,
        user_id=new_user.id
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"exists": True, "student_id": new_student.id, "created": True, "account_created": True})


@teacher_bp.route('/classes/<int:classroom_id>/set-default-password', methods=['POST'])
@login_required
def set_default_password(classroom_id):
    """Teacher sets the default login password for an entire classroom."""
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('student.portal'))

    classroom = Classroom.query.get_or_404(classroom_id)
    if classroom.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.manage_classes'))

    new_password = request.form.get('default_password', '').strip()
    if len(new_password) < 6:
        flash('Default password must be at least 6 characters.', 'danger')
        return redirect(url_for('teacher.classroom_detail', classroom_id=classroom_id))

    classroom.default_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    flash(f'✅ Default password for "{classroom.name}" set successfully! Share "{new_password}" with your students.', 'success')
    return redirect(url_for('teacher.classroom_detail', classroom_id=classroom_id))


@teacher_bp.route('/assignment/<int:assignment_id>/results')
@login_required
def assignment_results(assignment_id):
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))
    
    assignment = Assignment.query.get_or_404(assignment_id)
    # Ensure this assignment belongs to the teacher's classroom
    if assignment.classroom.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
        
    submissions = Submission.query.filter_by(assignment_id=assignment_id).order_by(Submission.score.desc()).all()
    
    return render_template('teacher/assignment_results.html', assignment=assignment, submissions=submissions)

@teacher_bp.route('/submission/<int:submission_id>')
@login_required
def submission_details(submission_id):
    if current_user.role != 'teacher':
        flash('Access denied. Teacher only area.', 'danger')
        return redirect(url_for('student.portal'))
        
    submission = Submission.query.get_or_404(submission_id)
    if submission.assignment.classroom.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('teacher.dashboard'))
        
    return render_template('teacher/submission_details.html', submission=submission)
