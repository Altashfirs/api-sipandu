from app.database import db
from datetime import datetime

class Checkpoint(db.Model):
    __tablename__ = 'checkpoints'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    checkpoints_code = db.Column(db.String(255), nullable=True)
    urutan = db.Column(db.Integer, nullable=True)
    todo_list = db.Column(db.Text, nullable=True)
    duration = db.Column(db.String(255), nullable=False)
    checkpoints_name = db.Column(db.String(255), nullable=True)
    id_area_patroli = db.Column(db.Integer, db.ForeignKey('area_patroli.id_area_patroli'), nullable=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.shift_id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    photo = db.Column(db.String(100), nullable=True)
    created_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_cookies = db.Column(db.String(70), nullable=False)
    building_name = db.Column(db.String(255), nullable=True)
    checkpoint_qrcode = db.Column(db.String(100), nullable=False)  # Added this line
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "checkpoints_code": self.checkpoints_code,
            "urutan": self.urutan,
            "todo_list": self.todo_list,
            "duration": self.duration,
            "checkpoints_name": self.checkpoints_name,
            "id_area_patroli": self.id_area_patroli,
            "shift_id": self.shift_id,
            "customer_id": self.customer_id,
            "photo": self.photo,
            "created_login": self.created_login,
            "created_cookies": self.created_cookies,
            "building_name": self.building_name,
            "checkpoint_qrcode": self.checkpoint_qrcode,  # Added this line
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
