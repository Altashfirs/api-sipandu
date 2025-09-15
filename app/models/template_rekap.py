from app.database import db

class TemplateRekap(db.Model):
    __tablename__ = 'template_rekap'

    id_template = db.Column(db.Integer, primary_key=True)
    section_template = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=True)
    image = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id_template": self.id_template,
            "section_template": self.section_template,
            "content": self.content,
            "image": self.image,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }