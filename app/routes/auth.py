from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models.models import User, Student, Classroom

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:
            # Enforce password change wall even if somehow already logged in
            if current_user.must_change_password:
                return redirect(url_for('student.change_password'))
            return redirect(url_for('student.portal'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password   = request.form.get('password', '')

        # Accept email OR enrollment number as login identifier
        user = User.query.filter_by(email=identifier).first()
        if not user:
            # Try by enrollment number
            student = Student.query.filter_by(enrollment_number=identifier).first()
            if student and student.user_id:
                user = User.query.get(student.user_id)

        if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')

            if user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))

            # Student — check if they must change password first
            if user.must_change_password:
                flash('🔒 Please set a new private password to continue.', 'warning')
                return redirect(url_for('student.change_password'))

            return redirect(url_for('student.portal'))

        flash('Invalid credentials. Please check your enrollment number / email and password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'student')

        # Block duplicate emails
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('auth.signup'))

        if role == 'student':
            enrollment_number = request.form.get('enrollment_number', '').strip()

            # Check if system already created a user account via the teacher flow
            existing_student = Student.query.filter_by(enrollment_number=enrollment_number).first()
            if existing_student and existing_student.user_id:
                flash('This enrollment number already has an account. Please log in directly with your enrollment number and the password shared by your teacher.', 'info')
                return redirect(url_for('auth.login'))

            # Normal student self-signup (no teacher pre-evaluation)
            if User.query.filter_by(username=username).first():
                flash('That username is already taken.', 'danger')
                return redirect(url_for('auth.signup'))

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password_hash=hashed_password, role='student',
                        must_change_password=False)
            db.session.add(user)
            db.session.flush()

            if existing_student:
                # Link the existing stub to the newly signed-up user
                existing_student.user_id = user.id
                existing_student.email   = email
                existing_student.name    = username
            else:
                # Brand-new student — find first available classroom
                classroom = Classroom.query.first()
                if not classroom:
                    sys_teacher = User(username="System", email="sys@admin.gradepro",
                                       password_hash="unused", role="teacher")
                    db.session.add(sys_teacher)
                    db.session.flush()
                    classroom = Classroom(name="General", teacher_id=sys_teacher.id)
                    db.session.add(classroom)
                    db.session.flush()

                student = Student(name=username, email=email,
                                  enrollment_number=enrollment_number,
                                  classroom_id=classroom.id, user_id=user.id)
                db.session.add(student)

        else:
            # Teacher signup
            if User.query.filter_by(username=username).first():
                flash('That username is already taken.', 'danger')
                return redirect(url_for('auth.signup'))

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password_hash=hashed_password, role='teacher',
                        must_change_password=False)
            db.session.add(user)

        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
