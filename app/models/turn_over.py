from app.database import db
from datetime import date

class TurnOver(db.Model):
    __tablename__ = 'turn_over'

    # Definisi kolom sesuai dengan struktur di database
    id_turn_over = db.Column(db.Integer, primary_key=True)
    id_customer = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    id_employee = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    id_employee_old = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    turn_over_date = db.Column(db.Date, nullable=False)
    turn_over_desc = db.Column(db.Text, nullable=False)
    turn_over_reason = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # 👉 Relasi
    # Relasi ke tabel Customer
    customer = db.relationship('Customer', backref='turn_overs', lazy=True)

    # Karena ada DUA foreign key ke tabel 'employees', kita harus mendefinisikan
    # DUA relasi yang berbeda dan menunjuk foreign key mana yang digunakan oleh masing-masing.
    # Ini untuk mengambil data karyawan BARU.
    employee_new = db.relationship('Employee', foreign_keys=[id_employee], backref='turn_overs_as_new')

    # Ini untuk mengambil data karyawan LAMA.
    employee_old = db.relationship('Employee', foreign_keys=[id_employee_old], backref='turn_overs_as_old')

    def to_dict(self):
        """
        Mengubah object model menjadi dictionary agar mudah diubah ke JSON.
        """
        return {
            "id_turn_over": self.id_turn_over,
            "id_customer": self.id_customer,
            "id_employee": self.id_employee, # Karyawan baru
            "id_employee_old": self.id_employee_old, # Karyawan lama
            "turn_over_date": self.turn_over_date.isoformat() if isinstance(self.turn_over_date, date) else None,
            "turn_over_desc": self.turn_over_desc,
            "turn_over_reason": self.turn_over_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }