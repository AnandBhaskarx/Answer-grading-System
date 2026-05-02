from app import db

class GradingResult(db.Model):
    __tablename__ = 'grading_results'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    student_answer = db.Column(db.Text, nullable=False)
    model_answer = db.Column(db.Text, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    score = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f'<GradingResult {self.id} - Score: {self.score}>'
