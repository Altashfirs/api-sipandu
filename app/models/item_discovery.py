from app.database import db

class ItemDiscovery(db.Model):
    __tablename__ = 'item_discovery'

    id_item_discovery = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_discovery_date = db.Column(db.Date, nullable=False)
    o_clock_item_discovery = db.Column(db.Time, nullable=False)
    inventors_name = db.Column(db.String(255), nullable=False)
    ttl = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    telephone_number = db.Column(db.String(255), nullable=False)
    id_card_number = db.Column(db.String(255), nullable=False)
    location_found = db.Column(db.Text, nullable=False)
    name_goods = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.String(255), nullable=False)
    information = db.Column(db.Text, nullable=False)
    id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)  # Foreign key ke employees
    position_id = db.Column(db.Integer, nullable=False)
    shift_id = db.Column(db.Integer, nullable=False)
    item_discovery_photo = db.Column(db.String(255), nullable=True, default=None)
    status = db.Column(db.Text, nullable=True, default=None)
    item_discovery_date_end = db.Column(db.DateTime, nullable=True, default=None)
    id_user_end = db.Column(db.Text, nullable=True, default=None)
    information_end = db.Column(db.Text, nullable=True, default=None)
    item_discovery_photo_end = db.Column(db.Text, nullable=True, default=None)
    inventors_name_end = db.Column(db.Text, nullable=True, default=None)

    # Relasi ke Employee
    employee = db.relationship('Employee', backref='item_discoveries')

    def to_dict(self):
        return {
            "id_item_discovery": self.id_item_discovery,
            "item_discovery_date": self.item_discovery_date.isoformat() if self.item_discovery_date else None,
            "o_clock_item_discovery": self.o_clock_item_discovery.strftime('%H:%M:%S') if self.o_clock_item_discovery else None,
            "inventors_name": self.inventors_name,
            "ttl": self.ttl,
            "address": self.address,
            "telephone_number": self.telephone_number,
            "id_card_number": self.id_card_number,
            "location_found": self.location_found,
            "name_goods": self.name_goods,
            "amount": self.amount,
            "information": self.information,
            "id": self.id,
            "position_id": self.position_id,
            "shift_id": self.shift_id,
            "item_discovery_photo": self.item_discovery_photo,
            "status": self.status,
            "item_discovery_date_end": self.item_discovery_date_end.isoformat() if self.item_discovery_date_end else None,
            "id_user_end": self.id_user_end,
            "information_end": self.information_end,
            "item_discovery_photo_end": self.item_discovery_photo_end,
            "inventors_name_end": self.inventors_name_end,
            "customer_id": self.employee.customer_id if self.employee else None,  # Ambil customer_id dari relasi
        }
