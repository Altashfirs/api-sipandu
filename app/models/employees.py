from app.database import db

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    employees_code = db.Column(db.String(35), nullable=False)
    employees_nip = db.Column(db.String(30), nullable=False)
    employees_email = db.Column(db.String(255), nullable=False, unique=True)
    employees_password = db.Column(db.String(255), nullable=False)
    employees_name = db.Column(db.String(255), nullable=False)
    employee_qrcode = db.Column(db.String(100), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.position_id'), nullable=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.shift_id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    created_login = db.Column(db.DateTime, nullable=True)
    created_cookies = db.Column(db.String(70), nullable=True)
    id_area_patroli = db.Column(db.Integer, db.ForeignKey('area_patroli.id_area_patroli'), nullable=True)
    fcm_token = db.Column(db.Text, nullable=True)
    

    # 👉 Field tambahan sesuai DB
    tanggal_join = db.Column(db.Date, nullable=True)
    nomor_kta = db.Column(db.String(255), nullable=True)
    masa_berlaku_kta = db.Column(db.Date, nullable=True)
    keterangan_status = db.Column(db.String(255), nullable=True)  # Isiannya "Ya" atau "Tidak"

    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relasi
    position = db.relationship('Position', backref='employees', lazy=True)
    shift = db.relationship('Shift', backref='employees', lazy=True)
    customer = db.relationship('Customer', backref='employees', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "employees_code": self.employees_code,
            "employees_nip": self.employees_nip,
            "employees_email": self.employees_email,
            "employees_name": self.employees_name,
            "employee_qrcode": self.employee_qrcode,
            "position_id": self.position_id,
            "shift_id": self.shift_id,
            "customer_id": self.customer_id,
            "photo": self.photo,
            "created_login": self.created_login,
            "created_cookies": self.created_cookies,
            "id_area_patroli": self.id_area_patroli,
            "fcm_token": self.fcm_token,
            "tanggal_join": self.tanggal_join,
            "nomor_kta": self.nomor_kta,
            "masa_berlaku_kta": self.masa_berlaku_kta,
            "keterangan_status": self.keterangan_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
