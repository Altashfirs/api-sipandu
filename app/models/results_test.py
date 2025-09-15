from app.database import db
from datetime import datetime

class ResultsTest(db.Model):
    __tablename__ = 'results_test'

    id_result = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_test = db.Column(db.Integer, nullable=False)
    id_question = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id_result": self.id_result,
            "id_test": self.id_test,
            "id_question": self.id_question,
            "answer": self.answer,
        }
