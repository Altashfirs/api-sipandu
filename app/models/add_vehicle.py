from app.database import db

class AddVehicle(db.Model):
    __tablename__ = 'add_vehicle'

    id_add_vehicle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_area = db.Column(db.Integer, nullable=False)
    id_vehicle_book = db.Column(db.Integer, db.ForeignKey('vehicle_book.id_vehicle_book'), nullable=False)  # Foreign key ke vehicle_book
    model_type = db.Column(db.String(255), nullable=False)
    nopol = db.Column(db.String(255), nullable=False)
    wheel = db.Column(db.String(255), nullable=False)
    spy = db.Column(db.String(255), nullable=False)
    tire = db.Column(db.String(255), nullable=False)
    condition_vehicle = db.Column(db.String(255), nullable=False)
    glass_door = db.Column(db.String(255), nullable=False)
    information = db.Column(db.Text, nullable=True)
    photo_add_vehicle = db.Column(db.String(255), nullable=True)

    # Relasi ke VehicleBook
    vehicle_book = db.relationship('VehicleBook', backref='add_vehicles')

    def to_dict(self):
        return {
            "id_add_vehicle": self.id_add_vehicle,
            "id_area": self.id_area,
            "id_vehicle_book": self.id_vehicle_book,
            "model_type": self.model_type,
            "nopol": self.nopol,
            "wheel": self.wheel,
            "spy": self.spy,
            "tire": self.tire,
            "condition_vehicle": self.condition_vehicle,
            "glass_door": self.glass_door,
            "information": self.information,
            "photo_add_vehicle": self.photo_add_vehicle,
            "customer_id": self.vehicle_book.employee.customer_id if self.vehicle_book and self.vehicle_book.employee else None  # Ambil customer_id dari relasi
        }
