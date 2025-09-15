from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.database import db

def create_app():
    """Factory function untuk membuat aplikasi Flask."""
    app = Flask(__name__)

    # Konfigurasi database
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mysql+mysqlconnector://nesipand_sipandu:nesipand_sipandu@localhost/nesipand_sipandu'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Konfigurasi JWT
    app.config['JWT_SECRET_KEY'] = 'your_secret_key'  # Ganti dengan secret key Anda
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Token tidak akan pernah kadaluarsa

    # Inisialisasi database
    db.init_app(app)

    # Inisialisasi JWT
    jwt = JWTManager(app)

    # Tambahkan middleware CORS
    CORS(app, resources={r"/*": {"origins": "*"}, r"/uploads/*": {"origins": "*"}}, supports_credentials=True)

    # Inisialisasi Flask-Limiter
    limiter = Limiter(
        get_remote_address,  # Menggunakan alamat IP pengguna
        app=app,
        default_limits=["2000 per 5 seconds"]  # 10 request dalam 5 detik secara default
    )

    # Daftarkan blueprint
    from app.routes import register_routes
    register_routes(app)

    return app
