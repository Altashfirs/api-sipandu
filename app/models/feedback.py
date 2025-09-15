from app.database import db

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)  # Foreign key ke employees
    category = db.Column(db.String(50), nullable=False)
    information = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('pending', 'resolved', 'in_progress'), default='pending')
    photo_feedback = db.Column(db.String(255))  # Kolom untuk menyimpan path atau URL file
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relasi ke Employee
    employee = db.relationship('Employee', backref='feedbacks')

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "customer_id": self.employee.customer_id if self.employee else None,  # Ambil customer_id dari relasi
            "category": self.category,
            "information": self.information,
            "status": self.status,
            "photo_feedback": self.photo_feedback,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }
