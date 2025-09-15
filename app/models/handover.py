from app.database import db

class Handover(db.Model):
    __tablename__ = 'handover'

    id_handover = db.Column(db.Integer, primary_key=True, autoincrement=True)
    handover_date = db.Column(db.Date, nullable=False)
    o_clock_handover = db.Column(db.Time, nullable=False)
    givers_name = db.Column(db.String(255), nullable=False)
    givers_position = db.Column(db.String(255), nullable=False)
    telephone_number_giver = db.Column(db.String(255), nullable=False)
    id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)  # Foreign key ke employees
    address = db.Column(db.Text, nullable=False)
    telephone_number_recipient = db.Column(db.String(255), nullable=True)
    item_name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.String(255), nullable=False)
    information = db.Column(db.Text, nullable=False)
    handover_photo = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    handover_date_end = db.Column(db.DateTime, nullable=True)
    id_user_end = db.Column(db.Integer, nullable=True)
    information_end = db.Column(db.Text, nullable=True)
    handover_photo_end = db.Column(db.String(255), nullable=True)
    givers_name_end = db.Column(db.String(255), nullable=True)

    # Relasi ke Employee
    employee = db.relationship('Employee', backref='handovers')

    def to_dict(self):
        return {
            "id_handover": self.id_handover,
            "handover_date": self.handover_date.isoformat() if self.handover_date else None,
            "o_clock_handover": self.o_clock_handover.strftime('%H:%M:%S') if self.o_clock_handover else None,
            "givers_name": self.givers_name,
            "givers_position": self.givers_position,
            "telephone_number_giver": self.telephone_number_giver,
            "id": self.id,
            "address": self.address,
            "telephone_number_recipient": self.telephone_number_recipient,
            "item_name": self.item_name,
            "amount": self.amount,
            "information": self.information,
            "handover_photo": self.handover_photo,
            "status": self.status,
            "handover_date_end": self.handover_date_end.isoformat() if self.handover_date_end else None,
            "id_user_end": self.id_user_end,
            "information_end": self.information_end,
            "handover_photo_end": self.handover_photo_end,
            "givers_name_end": self.givers_name_end,
            "customer_id": self.employee.customer_id if self.employee else None,  # Ambil customer_id dari relasi
        }
