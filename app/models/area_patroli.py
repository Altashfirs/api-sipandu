from app.database import db

class AreaPatroli(db.Model):
    __tablename__ = 'area_patroli'

    id_area_patroli = db.Column(db.Integer, primary_key=True)
    desc_area_patroli = db.Column(db.Text, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, nullable=False)

    def to_dict(self):
        return {
            "id_area_patroli": self.id_area_patroli,
            "desc_area_patroli": self.desc_area_patroli,
            "customer_id": self.customer_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
