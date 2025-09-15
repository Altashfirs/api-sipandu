from app.database import db
from datetime import datetime

class SwSite(db.Model):
    __tablename__ = 'sw_site'

    site_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site_url = db.Column(db.String(100), nullable=False)
    site_name = db.Column(db.String(50), nullable=False)
    site_company = db.Column(db.String(30), nullable=False)
    site_manager = db.Column(db.String(30), nullable=False)
    site_director = db.Column(db.String(30), nullable=False)
    site_phone = db.Column(db.String(12), nullable=False)
    site_address = db.Column(db.Text, nullable=False)
    site_description = db.Column(db.Text, nullable=False)
    site_logo = db.Column(db.String(50), nullable=True)
    site_email = db.Column(db.String(30), nullable=False)
    site_email_domain = db.Column(db.String(50), nullable=False)
    gmail_host = db.Column(db.String(50), nullable=False)
    gmail_username = db.Column(db.String(50), nullable=False)
    gmail_password = db.Column(db.String(50), nullable=False)
    gmail_port = db.Column(db.String(10), nullable=False)
    
    def to_dict(self):
        return {
            "site_id": self.site_id,
            "site_url": self.site_url,
            "site_name": self.site_name,
            "site_company": self.site_company,
            "site_manager": self.site_manager,
            "site_director": self.site_director,
            "site_phone": self.site_phone,
            "site_address": self.site_address,
            "site_description": self.site_description,
            "site_logo": self.site_logo,
            "site_email": self.site_email,
            "site_email_domain": self.site_email_domain,
            "gmail_host": self.gmail_host,
            "gmail_username": self.gmail_username,
            "gmail_password": self.gmail_password,
            "gmail_port": self.gmail_port
        }
