from app.database import db
from datetime import datetime

class MSPLog(db.Model):
    __tablename__ = 'msp_log'

    # Kolom-kolom tabel
    msp_id_log = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_msp_table = db.Column(db.Integer, nullable=True)  # Foreign key ke msp_table, boleh null
    employees_id = db.Column(db.Integer,db.ForeignKey('employees.id'), nullable=True)  # Boleh null
    status = db.Column(db.String(255), nullable=True)     # Status (opsional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Default current_timestamp
    update_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)  # Diupdate saat record berubah

    employee = db.relationship('Employee', backref='logs')

    # Metode untuk mengonversi objek ke dictionary
    def to_dict(self):
        return {
            "msp_id_log": self.msp_id_log,
            "id_msp_table": self.id_msp_table,
            "employees_id": self.employees_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "update_at": self.update_at.isoformat() if self.update_at else None
        }