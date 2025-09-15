from app.database import db

class MSPLogAnswer(db.Model):
    __tablename__ = 'msp_log_answer'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employees_id = db.Column(db.Integer,db.ForeignKey('employees.id'), nullable=True)  # Tambahkan kolom employees_id di bawah id
    msp_id_table = db.Column(db.Integer, db.ForeignKey('msp_table.msp_id_table'), nullable=False)
    msp_id_surat = db.Column(db.Integer, nullable=False)
    answer_real = db.Column(db.Text, nullable=True)
    answer_user = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)

    employee = db.relationship('Employee', backref='msp_logs')

    def to_dict(self):
        return {
            "id": self.id,
            "employees_id": self.employees_id,  # Tambahkan employees_id ke dictionary
            "msp_id_table": self.msp_id_table,
            "msp_id_surat": self.msp_id_surat,
            "answer_real": self.answer_real,
            "answer_user": self.answer_user,
            "created_at": self.created_at.isoformat()  # Mengembalikan dalam format ISO 8601
        }