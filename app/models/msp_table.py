from app.database import db
from sqlalchemy.dialects.mysql import ENUM

class MSPTable(db.Model):
    __tablename__ = 'msp_table'

    msp_id_table = db.Column(db.Integer, primary_key=True, autoincrement=True)
    letter_number = db.Column(db.String(255), nullable=True)
    topic_id = db.Column(db.Integer, nullable=True)
    building_id = db.Column(db.Integer, nullable=True)
    khusus_building = db.Column(db.Text, nullable=True)
    khusus_pic = db.Column(db.Text, nullable=True)
    tampil_building = db.Column(db.Text, nullable=True)
    tampil_pic = db.Column(db.Text, nullable=True)
    kategori = db.Column(ENUM('Reguler', 'Customer', 'Head Office'), nullable=False)
    implementation = db.Column(db.Text, nullable=True)
    msp_date = db.Column(db.Date, nullable=True)
    msp_status = db.Column(db.String(255), nullable=True)
    daily = db.Column(db.String(255), nullable=True)
    weekly = db.Column(db.String(255), nullable=True)
    msp_sr = db.Column(db.String(255), nullable=True)
    msp_surat = db.Column(db.String(255), nullable=True)
    id_admin = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            "msp_id_table": self.msp_id_table,
            "letter_number": self.letter_number,
            "topic_id": self.topic_id,
            "building_id": self.building_id,
            "khusus_building": self.khusus_building,
            "khusus_pic": self.khusus_pic,
            "tampil_building": self.tampil_building,
            "tampil_pic": self.tampil_pic,
            "kategori": self.kategori,
            "implementation": self.implementation,
            "msp_date": str(self.msp_date) if self.msp_date else None,
            "msp_status": self.msp_status,
            "daily": self.daily,
            "weekly": self.weekly,
            "msp_sr": self.msp_sr,
            "msp_surat": self.msp_surat,
            "id_admin": self.id_admin,
        }