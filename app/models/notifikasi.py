from app.database import db
from datetime import datetime
import pytz  # Import pytz untuk timezone

# Timezone untuk Indonesia (WIB)
WIB = pytz.timezone("Asia/Jakarta")

class Notification(db.Model):
    __tablename__ = 'notifications'

    id_notifikasi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employees_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)  # Foreign key ke employees
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(WIB)  # Default waktu dengan timezone WIB
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(WIB),
        onupdate=lambda: datetime.now(WIB)  # Update waktu dengan timezone WIB
    )

    # Relasi ke tabel employees
    employee = db.relationship('Employee', backref='notifications')

    def to_dict(self):
        return {
            "id_notifikasi": self.id_notifikasi,
            "employees_id": self.employees_id,
            "message": self.message,
            "type": self.type,
            "is_read": self.is_read,
            "created_at": self.created_at.astimezone(WIB).strftime('%Y-%m-%d %H:%M:%S'),  # Format lokal WIB
            "updated_at": self.updated_at.astimezone(WIB).strftime('%Y-%m-%d %H:%M:%S'),  # Format lokal WIB
            "customer_id": self.employee.customer_id if self.employee else None,  # Ambil customer_id dari relasi
        }
