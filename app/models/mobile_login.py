from app.database import db
from datetime import datetime

class MobileLogin(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employees_code = db.Column(db.String(35), nullable=False)
    employees_nip = db.Column(db.String(30), nullable=False)
    employees_email = db.Column(db.String(30), nullable=False, unique=True)
    employees_password = db.Column(db.String(100), nullable=False)
    employees_name = db.Column(db.String(50), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.position_id'), nullable=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.shift_id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    photo = db.Column(db.String(100), nullable=True)
    created_login = db.Column(db.DateTime, nullable=True)
    created_cookies = db.Column(db.String(70), nullable=True)
    id_area_patroli = db.Column(db.Integer, db.ForeignKey('area_patroli.id_area_patroli'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "employees_code": self.employees_code,
            "employees_nip": self.employees_nip,
            "employees_email": self.employees_email,
            "employees_name": self.employees_name,
            "position_id": self.position_id,
            "shift_id": self.shift_id,
            "customer_id": self.customer_id,
            "photo": self.photo,
            "created_login": self.created_login,
            "created_cookies": self.created_cookies,
            "id_area_patroli": self.id_area_patroli,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
