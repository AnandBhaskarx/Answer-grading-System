from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Student, Submission
from app import db, bcrypt

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.before_request
@login_required
def enforce_password_change():
    """Wall: force student to change default password before accessing anything else."""
    if current_user.role == 'student' and current_user.must_change_password:
        # Allow only the change_password route itself (and static files)
        if request.endpoint not in ('student.change_password', 'auth.logout', 'static'):
            flash('🔒 You must set a new personal password before continuing.', 'warning')
            return redirect(url_for('student.change_password'))


@student_bp.route('/portal')
@login_required
def portal():
    if current_user.role != 'student':
        flash('Access denied. Student only area.', 'danger')
        return redirect(url_for('teacher.dashboard'))

    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if student_profile:
        submissions = Submission.query.filter_by(student_id=student_profile.id).order_by(Submission.created_at.desc()).all()
    else:
        submissions = []

    return render_template('student/portal.html', student=student_profile, submissions=submissions)


@student_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Forced password change wall for first-time student login."""
    if current_user.role != 'student':
        return redirect(url_for('teacher.dashboard'))

    # Already changed — no need to be here
    if not current_user.must_change_password:
        return redirect(url_for('student.portal'))

    if request.method == 'POST':
        new_password     = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('student.change_password'))

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('student.change_password'))

        # Update the password securely
        current_user.password_hash       = bcrypt.generate_password_hash(new_password).decode('utf-8')
        current_user.must_change_password = False
        db.session.commit()

        flash('✅ Password changed successfully! Welcome to your portal.', 'success')
        return redirect(url_for('student.portal'))

    return render_template('student/change_password.html')
