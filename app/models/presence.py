from app.database import db
from datetime import datetime

class Presence(db.Model):
    __tablename__ = 'presence'

    presence_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employees_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # --- SHIFT UTAMA ---
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.shift_id'), nullable=False)

    # --- TAMBAHAN BARU ---
    is_overshift = db.Column(db.Boolean, default=False, nullable=False)  
    detected_shift_id = db.Column(db.Integer, db.ForeignKey('shift.shift_id'), nullable=True)

    presence_date = db.Column(db.Date, nullable=False)
    time_in = db.Column(db.Time, nullable=False)
    time_out = db.Column(db.Time, nullable=True)
    picture_in = db.Column(db.Text, nullable=False)
    picture_out = db.Column(db.String(150), nullable=True)
    present_id = db.Column(db.Integer, nullable=False)
    latitude_longtitude_in = db.Column(db.String(100), nullable=False)
    latitude_longtitude_out = db.Column(db.String(100), nullable=True)
    information = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(
        db.TIMESTAMP, 
        server_default=db.func.current_timestamp(), 
        onupdate=db.func.current_timestamp(), 
        nullable=False
    )
    
    # --- RELASI DIPERBARUI ---
    employee = db.relationship('Employee', backref='presences')
    shift = db.relationship('Shift', foreign_keys=[shift_id], backref='presences')
    detected_shift = db.relationship('Shift', foreign_keys=[detected_shift_id], backref='detected_presences')

    def to_dict(self):
        # ✅ Tambahkan dictionary untuk mapping
        present_names = {
            1: "Hadir",
            2: "Sakit",
            3: "Izin",
            4: "Dinas Luar Kota",
            5: "Dinas Dalam Kota",
        }
        
        return {
            "presence_id": self.presence_id,
            "employees_id": self.employees_id,

            # --- INFO SHIFT ---
            "shift_id": self.shift_id,
            "shift_name": self.shift.shift_name if self.shift else None,

            # --- INFO OVERSHIFT ---
            "is_overshift": self.is_overshift,
            "detected_shift_id": self.detected_shift_id,
            "detected_shift_name": self.detected_shift.shift_name if self.detected_shift else None,

            # --- INFO EMPLOYEE ---
            "customer_id": self.employee.customer_id if self.employee else None,

            # --- INFO PRESENCE ---
            "presence_date": self.presence_date.strftime('%Y-%m-%d') if self.presence_date else None,
            "time_in": self.time_in.strftime('%H:%M:%S') if self.time_in else None,
            "time_out": self.time_out.strftime('%H:%M:%S') if self.time_out else None,
            "picture_in": self.picture_in,
            "picture_out": self.picture_out,
            "present_id": self.present_id,
            "latitude_longtitude_in": self.latitude_longtitude_in,
            "latitude_longtitude_out": self.latitude_longtitude_out,
            "information": self.information,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            
            # ✅ Tambahkan field present_name
            "present_name": present_names.get(self.present_id, "Tidak Diketahui")
        }