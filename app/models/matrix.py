from app.database import db

class Matrix(db.Model):
    __tablename__ = 'matrix'

    matrix_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    matrix_name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "matrix_id": self.matrix_id,
            "matrix_name": self.matrix_name,
        }
