from app.database import db  
  
class Urgent(db.Model):  
    __tablename__ = 'urgent'  
  
    id_urgent = db.Column(db.Integer, primary_key=True, autoincrement=True)  
    id = db.Column(db.Integer, nullable=False)  
    checkpoint_id = db.Column(db.Integer, nullable=False)  
    urgent_date = db.Column(db.DateTime, nullable=True)  
    urgent_date_process = db.Column(db.DateTime, nullable=True)  
    urgent_date_end = db.Column(db.DateTime, nullable=True)  
    urgent_result_user = db.Column(db.Text, nullable=True) 
    urgent_result_user_end = db.Column(db.Text, nullable=True)
    urgent_result_admin = db.Column(db.Text, nullable=True)  
    urgent_photo = db.Column(db.String(255), nullable=True)  
    status = db.Column(db.String(255), nullable=False)  
    id_admin = db.Column(db.Integer, nullable=True)  
    id_user_terima = db.Column(db.Integer, nullable=True)  
    id_user_selesai = db.Column(db.Integer, nullable=True)  
    building_id = db.Column(db.String(255), nullable=True)  
  
    def to_dict(self):  
        return {  
            "id_urgent": self.id_urgent,  
            "id": self.id,  
            "checkpoint_id": self.checkpoint_id,  
            "urgent_date": self.urgent_date.isoformat() if self.urgent_date else None,  
            "urgent_date_process": self.urgent_date_process.isoformat() if self.urgent_date_process else None,  
            "urgent_date_end": self.urgent_date_end.isoformat() if self.urgent_date_end else None,  
            "urgent_result_user": self.urgent_result_user, 
            "urgent_result_user_end": self.urgent_result_user_end,
            "urgent_result_admin": self.urgent_result_admin,  
            "urgent_photo": self.urgent_photo,  
            "status": self.status,  
            "id_admin": self.id_admin,  
            "id_user_terima": self.id_user_terima,  
            "id_user_selesai": self.id_user_selesai,  
            "building_id": self.building_id,  
        }  
