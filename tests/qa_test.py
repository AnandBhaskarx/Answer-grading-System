import os
from app import create_app, db
from app.models.models import User, Classroom, Student, Assignment, Submission

app = create_app()

with app.app_context():
    try:
        print("--- QA Database Testing ---")
        
        # 1. Test Teacher Creation
        teacher = User(username="QA Teacher", email="qa_teacher@test.com", password_hash="test", role="teacher")
        db.session.add(teacher)
        db.session.flush()
        print("Teacher Creation: OK")
        
        # 2. Test Classroom Creation
        classroom = Classroom(name="QA Class", teacher_id=teacher.id)
        db.session.add(classroom)
        db.session.flush()
        print("Classroom Creation: OK")
        
        # 3. Test Assignment Creation
        assignment = Assignment(
            title="QA Exam", 
            max_marks=100.0, 
            passing_percentage=40.0,
            question_paper_path="dummy/qp.pdf",
            answer_key_path="dummy/ak.pdf",
            classroom_id=classroom.id
        )
        db.session.add(assignment)
        db.session.flush()
        print("Assignment Creation: OK")
        
        # 4. Test Student Creation
        s_user = User(username="QA Student", email="qa_student@test.com", password_hash="test", role="student")
        db.session.add(s_user)
        db.session.flush()
            
        student = Student(
            name="QA Student",
            email="qa_student@test.com",
            enrollment_number="QA123",
            classroom_id=classroom.id,
            user_id=s_user.id
        )
        db.session.add(student)
        db.session.flush()
        print("Student Creation: OK")
        
        # 5. Test Submission Creation
        submission = Submission(
            student_answer="Dummy",
            score=85.0,
            feedback_summary="Good job",
            detailed_analysis=[{"q":1}],
            answer_sheet_path="dummy/ans.png",
            assignment_id=assignment.id,
            student_id=student.id
        )
        db.session.add(submission)
        db.session.flush()
        print("Submission Creation: OK")
        
        # Rollback so we don't pollute the actual DB
        db.session.rollback()
        print("Rollback: OK")
        
        print("All Database Relationships & Constraints QA PASSED!")
    except Exception as e:
        db.session.rollback()
        print(f"QA FAILED: {e}")
