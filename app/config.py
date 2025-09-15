import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Log nilai variabel lingkungan untuk debug
    print("DB_USER:", os.getenv('DB_USER'))
    print("DB_PASSWORD:", os.getenv('DB_PASSWORD'))
    print("DB_HOST:", os.getenv('DB_HOST'))
    print("DB_NAME:", os.getenv('DB_NAME'))

    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,   # Test connections before use to discard stale ones
        'pool_recycle': 28800,      # Recycle connections every 30 seconds (less than wait_timeout=40)
        'pool_size': 100,          # Smaller pool for shared hosting to avoid overloading MySQL
        'max_overflow': 200,       # Allow fewer overflow connections to stay within limits
        'pool_timeout': 30,      # Shorter timeout to fail fast if connections are unavailable
        'connect_args': {
            'connect_timeout': 10  # Ensure connection attempts don’t hang
        }
    }
    SECRET_KEY = os.getenv('SECRET_KEY')
