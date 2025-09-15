from app.database import db

class Position(db.Model):
    __tablename__ = 'position'

    position_id = db.Column(db.Integer, primary_key=True)
    position_name = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, nullable=False)

    def to_dict(self):
        return {
            "position_id": self.position_id,
            "position_name": self.position_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
