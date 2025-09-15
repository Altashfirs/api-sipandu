from app.database import db

class Area(db.Model):
    __tablename__ = 'area'

    id_area = db.Column(db.Integer, primary_key=True, autoincrement=True)
    area_name = db.Column(db.String(255), nullable=False)
    building_id = db.Column(db.Integer, nullable=False)  # Foreign key removed

    def to_dict(self):
        return {
            "id_area": self.id_area,
            "area_name": self.area_name,
            "building_id": self.building_id
        }
