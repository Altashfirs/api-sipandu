from app.database import db
from datetime import date

class Absence(db.Model):
    __tablename__ = 'absence'

    id_absence = db.Column(db.Integer, primary_key=True)
    id_customer = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    id_employee_absen = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    tanggal_absen = db.Column(db.Date, nullable=False)
    id_employee_backup = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    tanggal_backup = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    employee_absen = db.relationship('Employee', foreign_keys=[id_employee_absen], backref='absences_as_absent')
    employee_backup = db.relationship('Employee', foreign_keys=[id_employee_backup], backref='absences_as_backup')
    customer = db.relationship('Customer', foreign_keys=[id_customer], backref='absences')

    def to_dict(self):
        return {
            "id_absence": self.id_absence,
            "id_customer": self.id_customer,
            "id_employee_absen": self.id_employee_absen,
            "tanggal_absen": self.tanggal_absen.isoformat() if self.tanggal_absen else None,
            "id_employee_backup": self.id_employee_backup,
            "tanggal_backup": self.tanggal_backup.isoformat() if self.tanggal_backup else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }