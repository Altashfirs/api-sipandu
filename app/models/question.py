from app.database import db

class Question(db.Model):
    __tablename__ = 'questions'

    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_text = db.Column(db.Text, nullable=True)
    position_id = db.Column(db.Integer, nullable=True)
    building_id = db.Column(db.Integer, nullable=True)
    matrix_id = db.Column(db.Integer, nullable=True)
    answer_a = db.Column(db.Text, nullable=True)
    answer_b = db.Column(db.Text, nullable=True)
    answer_c = db.Column(db.Text, nullable=True)
    answer = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "position_id": self.position_id,
            "building_id": self.building_id,
            "matrix_id": self.matrix_id,
            "answer_a": self.answer_a,
            "answer_b": self.answer_b,
            "answer_c": self.answer_c,
            "answer": self.answer,
        }
