from app import db
from sqlalchemy.dialects.postgresql import JSONB
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='teacher')
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)

    classrooms = db.relationship('Classroom', backref='teacher', lazy=True)

class Classroom(db.Model):
    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    default_password = db.Column(db.String(128), nullable=True)  # bcrypt hash of class default pwd

    students = db.relationship('Student', backref='classroom', lazy=True)
    assignments = db.relationship('Assignment', backref='classroom', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_number = db.Column(db.String(50), unique=True, nullable=True) # Will be populated for new students
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    submissions = db.relationship('Submission', backref='student', lazy=True)

class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    model_answer = db.Column(db.Text)          # The correct answer set by teacher
    keywords = db.Column(JSONB, default=list)  # e.g. ["photosynthesis", "chlorophyll"]
    max_marks = db.Column(db.Float, default=100.0)
    passing_percentage = db.Column(db.Float, default=40.0)
    question_paper_paths = db.Column(JSONB, default=list)
    answer_key_paths = db.Column(JSONB, default=list)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)

    submissions = db.relationship('Submission', backref='assignment', lazy=True)

class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    student_answer = db.Column(db.Text)
    score = db.Column(db.Float)
    feedback_summary = db.Column(db.Text)
    detailed_analysis = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    answer_sheet_paths = db.Column(JSONB, default=list)

    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)

