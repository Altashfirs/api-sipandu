from app.database import db

class SoalSurat(db.Model):
    __tablename__ = 'soal_surat'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    letter_number = db.Column(db.Integer, nullable=False)
    pertanyaan = db.Column(db.Text, nullable=False)
    pilihan = db.Column(db.Text, nullable=False)
    kunci_jawaban = db.Column(db.String(1), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    created_by = db.Column(db.String(60), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    updated_by = db.Column(db.String(60), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "letter_number": self.letter_number,
            "pertanyaan": self.pertanyaan,
            "pilihan": self.pilihan,
            "kunci_jawaban": self.kunci_jawaban,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by
        }
