from app.database import db

class GuestBook(db.Model):
    __tablename__ = 'guest_book'

    id_guest = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.String(255), db.ForeignKey('employees.id'), nullable=True)  # Foreign key ke employees
    guest_date = db.Column(db.Date, nullable=False)
    guest_name = db.Column(db.String(255), nullable=False)
    identity_number = db.Column(db.String(255), nullable=False)
    hp_number = db.Column(db.String(255), nullable=False)
    from_company = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    unit_goals = db.Column(db.String(255), nullable=True)
    necessity = db.Column(db.String(255), nullable=False)
    visitor_number = db.Column(db.String(255), nullable=False)
    clock_in = db.Column(db.Time, nullable=False)
    clock_out = db.Column(db.Time, nullable=True)
    guest_book_photo = db.Column(db.String(255), nullable=True)
    guest_book_photo_ktp = db.Column(db.Text, nullable=True)

    # Relasi ke Employee
    employee = db.relationship('Employee', backref='guest_books')

    def to_dict(self):
        return {
            "id_guest": self.id_guest,
            "id": self.id,
            "guest_date": self.guest_date.isoformat() if self.guest_date else None,
            "guest_name": self.guest_name,
            "identity_number": self.identity_number,
            "hp_number": self.hp_number,
            "from_company": self.from_company,
            "address": self.address,
            "unit_goals": self.unit_goals,
            "necessity": self.necessity,
            "visitor_number": self.visitor_number,
            "clock_in": self.clock_in.strftime('%H:%M:%S') if self.clock_in else None,
            "clock_out": self.clock_out.strftime('%H:%M:%S') if self.clock_out else None,
            "guest_book_photo": self.guest_book_photo,
            "guest_book_photo_ktp": self.guest_book_photo_ktp,
            "customer_id": self.employee.customer_id if self.employee else None,  # Ambil customer_id dari relasi
        }
