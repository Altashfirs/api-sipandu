from app.database import db

class VehicleBook(db.Model):
    __tablename__ = 'vehicle_book'

    id_vehicle_book = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_book_date = db.Column(db.Date, nullable=True, default=None)
    id_area = db.Column(db.Integer, nullable=False)
    shift_id = db.Column(db.Integer, nullable=False)
    id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)  # Foreign key ke employees
    foto = db.Column(db.String(255), nullable=True)

    # Relasi ke Employee
    employee = db.relationship('Employee', backref='vehicle_books')

    def to_dict(self):
        return {
            "id_vehicle_book": self.id_vehicle_book,
            "vehicle_book_date": self.vehicle_book_date.isoformat() if self.vehicle_book_date else None,
            "id_area": self.id_area,
            "shift_id": self.shift_id,
            "id": self.id,
            "foto": self.foto,
            "customer_id": self.employee.customer_id if self.employee else None  # Ambil customer_id dari relasi
        }
