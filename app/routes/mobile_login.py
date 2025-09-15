import logging
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.mobile_login import MobileLogin
from flask_jwt_extended import create_access_token
import bcrypt
from datetime import datetime
from pytz import timezone

# Setup logging to file
logging.basicConfig(
    filename='app_debug.log',  # Nama file log
    level=logging.DEBUG,       # Level logging
    format='%(asctime)s - %(levelname)s - %(message)s'  # Format log
)

# Zona waktu Asia/Jakarta
jakarta_tz = timezone('Asia/Jakarta')

mobile_login_bp = Blueprint('mobile_login', __name__, url_prefix='/api/pegawai')

@mobile_login_bp.route('/login', methods=['POST'])
def login():
    try:
        logging.debug("Received login request")
        data = request.json
        logging.debug(f"Request data: {data}")

        # Validasi input
        if not data or 'employees_email' not in data or 'employees_password' not in data:
            logging.warning("Missing employees_email or employees_password")
            return jsonify({"error": "Missing employees_email or employees_password"}), 400

        # Cari user berdasarkan employees_email
        user = MobileLogin.query.filter_by(employees_email=data['employees_email']).first()
        logging.debug(f"Queried user: {user}")

        if not user:
            logging.warning("Invalid Email or Password")
            return jsonify({"error": "Invalid Email or Password"}), 401

        # Bandingkan hash menggunakan bcrypt
        if not bcrypt.checkpw(data['employees_password'].encode('utf-8'), user.employees_password.encode('utf-8')):
            logging.warning("Invalid Email or Password")
            return jsonify({"error": "Invalid Email or Password"}), 401

        # Buat token JWT dengan identity
        access_token = create_access_token(identity={
            "id": user.id,
            "employees_email": user.employees_email,
            "employees_name": user.employees_name
        })
        logging.debug(f"Generated access token: {access_token}")

        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        logging.error("Failed to process login", exc_info=True)
        return jsonify({"error": f"Failed to process login: {str(e)}"}), 500

@mobile_login_bp.route('/', methods=['GET'])
def get_employees():
    """Retrieve all employees."""
    try:
        logging.debug("Received request to get all employees")
        employees = MobileLogin.query.all()
        logging.debug(f"Retrieved employees: {employees}")
        return jsonify([employee.to_dict() for employee in employees]), 200
    except Exception as e:
        logging.error("Failed to retrieve employees", exc_info=True)
        return jsonify({"error": f"Failed to retrieve employees: {str(e)}"}), 500
