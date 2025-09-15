from app.database import db
from datetime import datetime

class Topic(db.Model):
    __tablename__ = 'topic'

    id_topic = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_topic": self.id_topic,
            "topic_name": self.topic_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
