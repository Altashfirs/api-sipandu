from app.database import db

class PatrolLog(db.Model):
    __tablename__ = 'patrol_logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, nullable=True)
    checkpoint_id = db.Column(db.Integer, nullable=True)
    checkpoint_result = db.Column(db.String(200), nullable=True)
    checkpoint_date = db.Column(db.Date, nullable=True)
    checkpoint_in = db.Column(db.Time, nullable=True)
    checkpoint_out = db.Column(db.Time, nullable=True)
    checkpoint_photo = db.Column(db.String(255), nullable=True)
    session = db.Column(db.Enum('process', 'end'), nullable=True)
    track = db.Column(db.Integer, nullable=True)  
    schedule = db.Column(db.Integer, nullable=True) 
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "employee_id": self.employee_id,
            "checkpoint_id": self.checkpoint_id,
            "checkpoint_result": self.checkpoint_result,
            "checkpoint_date": self.checkpoint_date.isoformat() if self.checkpoint_date else None,
            "checkpoint_in": self.checkpoint_in.strftime('%H:%M:%S') if self.checkpoint_in else None,
            "checkpoint_out": self.checkpoint_out.strftime('%H:%M:%S') if self.checkpoint_out else None,
            "checkpoint_photo": self.checkpoint_photo,
            "session": self.session,
            "track": self.track,  
            "schedule": self.schedule, 
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
