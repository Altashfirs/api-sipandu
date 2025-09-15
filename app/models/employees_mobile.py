from app.database import db

class EmployeeMobile(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, extend_existing=True)
    employees_code = db.Column(db.String(35), nullable=False, extend_existing=True)
    employees_nip = db.Column(db.String(30), nullable=False, extend_existing=True)
    employees_email = db.Column(db.String(30), nullable=False, unique=True, extend_existing=True)
    employees_password = db.Column(db.String(100), nullable=False, extend_existing=True)
    employees_name = db.Column(db.String(50), nullable=False, extend_existing=True)
    position_id = db.Column(db.Integer, db.ForeignKey('position.position_id'), nullable=True, extend_existing=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.shift_id'), nullable=True, extend_existing=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True, extend_existing=True)
    photo = db.Column(db.String(100), nullable=True, extend_existing=True)
    created_login = db.Column(db.DateTime, nullable=True, extend_existing=True)
    created_cookies = db.Column(db.String(70), nullable=True, extend_existing=True)
    id_area_patroli = db.Column(db.Integer, db.ForeignKey('area_patroli.id_area_patroli'), nullable=True, extend_existing=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, extend_existing=True)
    updated_at = db.Column(db.TIMESTAMP, nullable=False, extend_existing=True)

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
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
