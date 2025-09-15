from app.database import db

class JournalBook(db.Model):
    __tablename__ = 'journal_book'

    id_journal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    journal_date = db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer, nullable=False)
    id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)  # Foreign key ke employees
    o_clock = db.Column(db.Time, nullable=False)
    incident_description = db.Column(db.String(255), nullable=False)
    information = db.Column(db.Text, nullable=False)
    journal_book_photo = db.Column(db.String(255), nullable=False)

    # Relasi ke Employee
    employee = db.relationship('Employee', backref='journals')

    def to_dict(self):
        return {
            "id_journal": self.id_journal,
            "journal_date": str(self.journal_date),
            "shift_id": self.shift_id,
            "id": self.id,
            "customer_id": self.employee.customer_id if self.employee else None,  # Ambil customer_id dari relasi
            "o_clock": str(self.o_clock),
            "incident_description": self.incident_description,
            "information": self.information,
            "journal_book_photo": self.journal_book_photo,
        }
