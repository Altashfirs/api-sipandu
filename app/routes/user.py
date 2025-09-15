import jwt  # Import library JWT
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.user import User
from app.models.password_reset import PasswordReset
from flask_jwt_extended import create_access_token
import bcrypt
from datetime import datetime, timedelta
from pytz import timezone
import secrets
import smtplib
from email.mime.text import MIMEText

# Zona waktu Asia/Jakarta
jakarta_tz = timezone('Asia/Jakarta')

users_bp = Blueprint('user', __name__, url_prefix='/api/users')

def send_reset_email(email, token):
    msg = MIMEText(f"Klik link berikut untuk mereset password Anda: https://nes-sipandu.com/reset-password/{token}")
    msg['Subject'] = 'Reset Password'
    msg['From'] = 'info-password@nes-sipandu.com'
    msg['To'] = email

    with smtplib.SMTP('smtp.nes-sipandu.com') as server:
        server.login('info-password@nes-sipandu.com', 'v6yzG8sc4xsnE2H8RqRR')
        server.sendmail(msg['From'], [msg['To']], msg.as_string())

@users_bp.route('/lupa-password', methods=['POST'])
def lupa_password():
    try:
        data = request.json
        if 'email' not in data:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({"error": "Email not found"}), 404

        token = secrets.token_urlsafe()
        expires_at = datetime.now(jakarta_tz) + timedelta(hours=1)

        password_reset = PasswordReset(
            email=user.email,
            token=token,
            created_at=datetime.now(jakarta_tz),
            expires_at=expires_at
        )
        db.session.add(password_reset)
        db.session.commit()

        send_reset_email(user.email, token)
        return jsonify({"message": "Password reset email sent!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process password reset request: {str(e)}"}), 500


@users_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        if 'token' not in data or 'new_password' not in data:
            return jsonify({"error": "Token and new password are required"}), 400

        password_reset = PasswordReset.query.filter_by(token=data['token']).first()
        if not password_reset or password_reset.expires_at < datetime.now(jakarta_tz):
            return jsonify({"error": "Invalid or expired token"}), 400

        user = User.query.filter_by(email=password_reset.email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
        user.password = hashed_password.decode('utf-8')

        db.session.delete(password_reset)
        db.session.commit()
        return jsonify({"message": "Password updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to reset password: {str(e)}"}), 500
        
@users_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json

        # Validasi input
        if 'username' not in data or 'password' not in data:
            return jsonify({"error": "Missing username or password"}), 400

        # Cari user berdasarkan username
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401

        # Bandingkan hash menggunakan bcrypt
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({"error": "Invalid username or password"}), 401

        # Buat token JWT dengan identity
        access_token = create_access_token(identity={
            "user_id": user.user_id,
            "unix_id": user.unix_id, 
            "username": user.username,
            "email": user.email,
            "level": user.level
        })

        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to process login: {str(e)}"}), 500

@users_bp.route('/login/email', methods=['POST'])
def login_email():
    try:
        data = request.json

        # Validasi input
        if 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing email or password"}), 400

        # Cari user berdasarkan email
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        # Debug: Periksa data user dari database
        print("User Data from DB:", user.__dict__)

        # Perbaiki hash jika menggunakan format $2y$
        hashed_password = user.password
        if hashed_password.startswith("$2y$"):
            hashed_password = hashed_password.replace("$2y$", "$2b$")

        # Verifikasi password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), hashed_password.encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401

        # Siapkan data untuk token JWT
        token_data = {
            "user_id": user.user_id,
            "unix_id": user.unix_id, 
            "username": user.username,
            "email": user.email,
            "fullname": user.fullname,
            "session": user.session,
            "ip": user.ip,
            "browser": user.browser,
            "level": user.level,
            "exp": datetime.utcnow() + timedelta(hours=1)  # Token berlaku selama 1 jam
        }

        # Debug: Periksa data yang akan dikodekan ke JWT
        print("Token Data:", token_data)

        # Buat token JWT
        access_token = jwt.encode(token_data, "your_secret_key", algorithm="HS256")

        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to process login: {str(e)}"}), 500


@users_bp.route('/', methods=['GET'])
def get_users():
    """Retrieve all users."""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve users: {str(e)}"}), 500


@users_bp.route('/<identifier>', methods=['GET'])
def get_user(identifier):
    """Retrieve a user by `user_id` or `unix_id`."""
    try:
        user = None
        # Check if identifier is numeric (assume `user_id`)
        if identifier.isdigit():
            user = User.query.get(int(identifier))
        else:
            # Otherwise, assume `unix_id`
            user = User.query.filter_by(unix_id=identifier).first()

        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve user: {str(e)}"}), 500

@users_bp.route('/level/<level>', methods=['GET'])
def get_user_by_level(level):
    """Retrieve a user by `level`."""
    try:
        # Query the database for a user with the specified level
        user = User.query.filter_by(level=level).first()

        if not user:
            return jsonify({"error": "User with the specified level not found"}), 404

        return jsonify(user.to_dict())

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve user: {str(e)}"}), 500

@users_bp.route('/', methods=['POST'])
def create_user():
    """Create a new user."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Data cannot be empty."}), 400

        # Validate username and email uniqueness at the same level
        existing_users = User.query.filter_by(level=data['level']).all()
        for user in existing_users:
            if user.username == data['username'] or user.email == data['email']:
                return jsonify({"error": "Username or email already exists at this level."}), 400

        # Enforce constraints on specific usernames (admin_ or customer_)
        admin_count = sum(1 for user in existing_users if user.username.startswith('admin_'))
        customer_count = sum(1 for user in existing_users if user.username.startswith('customer_'))

        if data['username'].startswith('admin_') and admin_count >= 1:
            return jsonify({"error": "Only one admin is allowed per level."}), 400
        if data['username'].startswith('customer_') and customer_count >= 1:
            return jsonify({"error": "Only one customer is allowed per level."}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        # Create user
        user = User(
            unix_id=data.get('unix_id'),
            username=data['username'],
            email=data['email'],
            password=hashed_password.decode('utf-8'),
            fullname=data['fullname'],
            registered=datetime.now(jakarta_tz),
            created_login=datetime.now(jakarta_tz),
            last_login=datetime.now(jakarta_tz),
            session=data.get('session'),
            ip=data.get('ip'),
            browser=data.get('browser'),
            level=data['level']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User created successfully!", "user": user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error creating user: {str(e)}"}), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Data cannot be empty."}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        existing_users = User.query.filter(User.level == data['level']).all()

        # Check username and email uniqueness at the same level
        for existing_user in existing_users:
            if existing_user.user_id != user_id:
                if existing_user.username == data['username'] or existing_user.email == data['email']:
                    return jsonify({"error": "Username or email already exists at this level."}), 400

        # Update user fields
        for key, value in data.items():
            if key == 'password' and value:
                hashed_password = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user.password = hashed_password
            elif key != 'password':
                setattr(user, key, value)

        db.session.commit()
        return jsonify({"message": "User updated successfully!", "user": user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error updating user: {str(e)}"}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error deleting user: {str(e)}"}), 500
