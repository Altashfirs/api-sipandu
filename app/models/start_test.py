from app.database import db
from datetime import datetime

class StartTest(db.Model):
    __tablename__ = 'start_test'

    id_test = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_date = db.Column(db.Date, nullable=True)
    id_examiner = db.Column(db.Integer, nullable=True)
    id_employees = db.Column(db.Integer, nullable=True)
    id_admin = db.Column(db.Integer, nullable=True)
    status_test = db.Column(db.String(255), nullable=True)
    id_matrix = db.Column(db.Integer, nullable=True)
    dokumentasi = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)

    def to_dict(self):
        def format_datetime(dt):
            """Format datetime ke '22 Desember 2024 Jam 19.00' dengan mapping nama bulan manual."""
            if not dt:
                return None

            # Mapping nama bulan dalam bahasa Indonesia
            bulan_id = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }

            tanggal = dt.day
            bulan = bulan_id[dt.month]  # Ambil nama bulan dari mapping
            tahun = dt.year
            jam = dt.strftime("%H.%M")  # Format jam:menit

            return f"{tanggal} {bulan} {tahun} Jam {jam}"

        return {
            "id_test": self.id_test,
            "test_date": self.test_date.isoformat() if self.test_date else None,  # Tetap format ISO
            "id_examiner": self.id_examiner,
            "id_employees": self.id_employees,
            "id_admin": self.id_admin,
            "status_test": self.status_test,
            "id_matrix": self.id_matrix,
            "dokumentasi": self.dokumentasi,
            "created_at": format_datetime(self.created_at),  # Format sesuai permintaan
            "updated_at": format_datetime(self.updated_at),
        }
