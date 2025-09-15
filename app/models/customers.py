from app.database import db

class Customer(db.Model):
    __tablename__ = 'customers'

    customer_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text)
    latitude_longtitude = db.Column(db.String(150))
    radius = db.Column(db.Text)
    logo = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP)
    updated_at = db.Column(db.TIMESTAMP)

    # employees = db.relationship('Employee', backref='customer', lazy=True)

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "code": self.code,
            "name": self.name,
            "address": self.address,
            "latitude_longtitude": self.latitude_longtitude,
            "radius": self.radius,
            "logo": self.logo,
            "total_employees": len(self.employees),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
