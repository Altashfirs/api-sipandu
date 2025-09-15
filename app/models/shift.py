from app.database import db
from datetime import datetime

class Shift(db.Model):
    __tablename__ = 'shift'

    shift_id = db.Column(db.Integer, primary_key=True)
    shift_name = db.Column(db.Text, nullable=False)
    time_in = db.Column(db.Time, nullable=False)
    time_out = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "shift_id": self.shift_id,
            "shift_name": self.shift_name,
            "time_in": self.time_in.strftime('%H:%M:%S') if self.time_in else None,  # Konversi ke format HH:MM:SS
            "time_out": self.time_out.strftime('%H:%M:%S') if self.time_out else None,  # Konversi ke format HH:MM:SS
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
