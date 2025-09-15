from app.database import db

class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    unix_id = db.Column(db.String(5), nullable=True)
    username = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    fullname = db.Column(db.String(40), nullable=False)
    registered = db.Column(db.DateTime, nullable=False)
    created_login = db.Column(db.DateTime, nullable=False)
    last_login = db.Column(db.DateTime, nullable=False)
    session = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(20), nullable=False)
    browser = db.Column(db.String(30), nullable=False)
    level = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "unix_id": self.unix_id,
            "username": self.username,
            "email": self.email,
            "fullname": self.fullname,
            "registered": self.registered.isoformat() if self.registered else None,
            "created_login": self.created_login.isoformat() if self.created_login else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "session": self.session,
            "ip": self.ip,
            "browser": self.browser,
            "level": self.level,
        }
