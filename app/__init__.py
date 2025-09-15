from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.database import db

def create_app():
    """Factory function untuk membuat aplikasi Flask."""
    app = Flask(__name__)

    # Konfigurasi database
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mysql+mysqlconnector://nesipand_sipandu:nesipand_sipandu@localhost/nesipand_sipandu'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,    # Test connections before use
        'pool_recycle': 28800,       # Recycle connections every 30 seconds (less than wait_timeout=40)
        'pool_size': 100,           # Small pool for shared hosting
        'max_overflow': 200,        # Limit overflow connections
        'pool_timeout': 30,       # Fail fast if pool is exhausted
        'connect_args': {
            'connect_timeout': 10  # Match MySQL connect_timeout
        }
    }

    # Konfigurasi JWT
    app.config['JWT_SECRET_KEY'] = 'your_secret_key'  # Ganti dengan secret key Anda
    # app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)  # Masa aktif token 10 menit
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Token tidak akan pernah kadaluarsa

    # Inisialisasi database
    db.init_app(app)

    # Inisialisasi JWT
    jwt = JWTManager(app)

    # Tambahkan middleware CORS
    # SESUDAH (Solusi 1: Paling Simpel dan Direkomendasikan)
    CORS(app, supports_credentials=True)

    # Daftarkan blueprint
    from app.routes import register_routes
    register_routes(app)

    return app