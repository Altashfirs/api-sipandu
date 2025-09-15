import os
import jwt
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.employees import Employee  # Ganti model ke Employee
from app.models.customers import Customer  # Pastikan path ke model Customer benar
from app.models.password_reset import PasswordReset
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from pytz import timezone
import random
import string
import requests
import bcrypt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Zona waktu Asia/Jakarta
jakarta_tz = timezone('Asia/Jakarta')

employees_mobile_bp = Blueprint('employees_mobile', __name__, url_prefix='/api/employees_mobile')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def delete_file(file_path):
    """Helper function to delete a file if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_SERVER = "mail.nes-sipandu.com"  # Server SMTP yang digunakan
SMTP_PORT = 465  # Gunakan 465 (SSL) atau 587 (TLS)
EMAIL_ADDRESS = "info-password@nes-sipandu.com"  # Email pengirim
EMAIL_PASSWORD = "s2KfSmxkLWNNYMQAM9Du"  # Ganti dengan password atau App Password

def send_reset_email(email, token):
    msg = MIMEMultipart()
    msg['Subject'] = "Pemulihan Akun Sipandu – Tindakan Diperlukan"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email

    # HTML email body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #1a73e8;">Reset Password Anda</h2>
        <p>Halo,</p>
        <p>Anda telah meminta untuk mereset password akun Anda.</p>
        <p>Klik tombol di bawah untuk melanjutkan proses reset password Anda:</p>
        <p>
            <a href="https://apps.nes-sipandu.com/reset-password/{token}" 
               style="display: inline-block; padding: 10px 20px; color: #fff; background-color: #1a73e8; text-decoration: none; border-radius: 5px;">
                Reset Password
            </a>
        </p>
        <p>Jika tombol di atas tidak berfungsi, silakan klik atau salin link berikut:</p>
        <p><a href="https://apps.nes-sipandu.com/reset-password/{token}">https://apps.nes-sipandu.com/reset-password/{token}</a></p>
        <p><i>Link ini akan kedaluwarsa dalam 30 menit.</i></p>
        <hr>
        <p>Jika Anda tidak meminta reset password, abaikan email ini.</p>
        <p>Terima kasih,<br><b>Tim Dukungan Sipandu</b></p>
    </body>
    </html>
    """
    
    # Tambahkan HTML ke email
    msg.attach(MIMEText(html_body, 'html'))

    try:
        # Gunakan SMTP_SSL untuk port 465
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
            print("Email berhasil dikirim!")
    except Exception as e:
        print(f"Error: {e}")
        raise e


@employees_mobile_bp.route('/lupa-password', methods=['POST'])
def lupa_password():
    try:
        data = request.json
        if 'email' not in data:
            return jsonify({"error": "Email harus diisi"}), 400

        user = Employee.query.filter_by(employees_email=data['email']).first()

        today = datetime.now(jakarta_tz).date()
        existing_reset = PasswordReset.query.filter(
            PasswordReset.email == data['email'],
            db.func.date(PasswordReset.created_at) == today
        ).first()

        # Jika sudah ada permintaan reset password untuk hari ini
        if existing_reset:
            return jsonify({"error": "Permintaan reset password untuk email ini sudah dibuat hari ini. Silakan coba lagi besok."}), 400

        # Jika user ada, kita akan membuat token dan mengirim email
        if user:
            token = secrets.token_urlsafe()
            expires_at = datetime.now(jakarta_tz) + timedelta(minutes=30)

            password_reset = PasswordReset(
                email=user.employees_email,
                token=token,
                created_at=datetime.now(jakarta_tz),
                expires_at=expires_at
            )
            db.session.add(password_reset)
            db.session.commit()

            send_reset_email(user.employees_email, token)

        # Jika email tidak ada di database, kembalikan pesan yang sama
        return jsonify({"message": "Email reset password telah dikirim ya, silakan cek di gmail!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal memproses permintaan reset password: {str(e)}"}), 500


@employees_mobile_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        if 'token' not in data or 'new_password' not in data:
            return jsonify({"error": "Token dan password baru harus diisi"}), 400

        password_reset = PasswordReset.query.filter_by(token=data['token']).first()
        if not password_reset:
            return jsonify({"error": "Token tidak valid atau sudah kedaluwarsa"}), 400

        user = Employee.query.filter_by(employees_email=password_reset.email).first()
        if not user:
            return jsonify({"error": "Pengguna tidak ditemukan"}), 404

        hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
        user.employees_password = hashed_password.decode('utf-8')

        PasswordReset.query.filter_by(email=password_reset.email).delete()

        db.session.commit()
        return jsonify({"message": "Password berhasil diperbarui!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal mereset password: {str(e)}"}), 500

@employees_mobile_bp.route('/password-reset-info/<token>', methods=['GET'])
def password_reset_info(token):
    try:
        password_reset = PasswordReset.query.filter_by(token=token).first()
        if not password_reset:
            return jsonify({"error": "Token tidak valid atau sudah kedaluwarsa"}), 400

        return jsonify({
            "email": password_reset.email,
            "created_at": password_reset.created_at.isoformat(),
            "expires_at": password_reset.expires_at.isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil informasi reset password: {str(e)}"}), 500

@employees_mobile_bp.route('/code/<string:formatted_code>', methods=['GET'])
def get_employees_by_code(formatted_code):
    """
    Retrieve employees data by formatted employees_code.
    Replace '---' with space and '--' with slash in employees_code.
    """
    try:
        # Replace custom formatting back to original format
        employees_code = formatted_code.replace('---', ' ').replace('--', '/')

        # Query the database
        employees = Employee.query.filter_by(employees_code=employees_code).first()
        if not employees:
            return jsonify({"error": "Employee not found"}), 404

        return jsonify(employees.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve employees", "details": str(e)}), 500

@employees_mobile_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json

        # Validasi input
        if 'username' not in data or 'password' not in data:
            return jsonify({"error": "Missing username or password"}), 400

        # Cari user berdasarkan username
        user = Employee.query.filter_by(username=data['username']).first()
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401

        # Bandingkan hash menggunakan bcrypt
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user.employees_password.encode('utf-8')):
            return jsonify({"error": "Invalid username or password"}), 401

        # Buat token JWT dengan identity
        access_token = create_access_token(identity={
            "user_id": user.id,
            "username": user.username,
            "email": user.employees_email,
            "level": user.level
        })

        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to process login: {str(e)}"}), 500

@employees_mobile_bp.route('/fcm-token', methods=['GET'])
def get_employees_mobile_fcm_token():
    """Retrieve selected employee details (id, employees_name, shift_id, fcm_token)."""
    try:
        employees = Employee.query.with_entities(Employee.id, Employee.employees_name, Employee.shift_id, Employee.fcm_token).all()
        return jsonify([
            {
                "id": employee.id,
                "employees_name": employee.employees_name,
                "shift_id": employee.shift_id,
                "fcm_token": employee.fcm_token
            } for employee in employees
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve employee details: {str(e)}"}), 500


# Endpoint untuk mengambil data karyawan berdasarkan ID
@employees_mobile_bp.route('/fcm-token/<int:id>', methods=['GET'])
def get_employee_fcm_token_by_id(id):
    """
    Retrieve a single employee's details (id, employees_name, shift_id, fcm_token) by ID.
    """
    try:
        # Retrieve a single employee by ID
        employee = Employee.query.with_entities(
            Employee.id,
            Employee.employees_name,
            Employee.shift_id,
            Employee.fcm_token
        ).filter_by(id=id).first()

        if not employee:
            return jsonify({"error": f"Employee with ID {id} not found"}), 404

        # Return the single employee's details
        return jsonify({
            "id": employee.id,
            "employees_name": employee.employees_name,
            "shift_id": employee.shift_id,
            "fcm_token": employee.fcm_token
        })

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": f"Failed to retrieve employee details: {str(e)}"}), 500
        

# Endpoint untuk mengambil semua data customer dan employee berdasarkan customer_id
@employees_mobile_bp.route('/fcm-token/customer/<int:customer_id>', methods=['GET'])
def get_customer_and_employee_fcm_tokens(customer_id):
    """
    Retrieve all related data for a specific customer_id:
    - Customer details (customer_id, name, fcm_token)
    - All related employees' details (employee_name, shift_id, fcm_token)
    """
    try:
        # Query untuk mendapatkan data customer
        customer = Customer.query.filter_by(customer_id=customer_id).first()

        if not customer:
            return jsonify({"error": f"Customer with ID {customer_id} not found"}), 404

        # Query untuk mendapatkan semua data employee yang terkait dengan customer_id
        employees = Employee.query.filter_by(customer_id=customer_id).all()

        # Format data employees menjadi list
        employee_list = []
        for emp in employees:
            employee_list.append({
                "employee_name": emp.employees_name,
                "shift_id": emp.shift_id,
                "fcm_token": emp.fcm_token
            })

        # Return the combined details of customer and employees
        return jsonify({
            "customer": {
                "customer_id": customer.customer_id,
                "name": customer.name
            },
            "employees": employee_list
        })

    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": f"Failed to retrieve details: {str(e)}"}), 500

@employees_mobile_bp.route('/', methods=['GET'])
def get_employees_mobile():
    """Retrieve all employees."""
    try:
        employees = Employee.query.all()
        return jsonify([employee.to_dict() for employee in employees])
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve employees: {str(e)}"}), 500


@employees_mobile_bp.route('/<identifier>', methods=['GET'])
def get_employee_mobile_by_id(identifier):
    """Retrieve an employee by `id` or `employees_email`."""
    try:
        employee = None
        # Check if identifier is numeric (assume `id`)
        if identifier.isdigit():
            employee = Employee.query.get(int(identifier))
        else:
            # Otherwise, assume `employees_email`
            employee = Employee.query.filter_by(employees_email=identifier).first()

        if not employee:
            return jsonify({"error": "Employee not found"}), 404
        return jsonify(employee.to_dict())
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve employee: {str(e)}"}), 500


@employees_mobile_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_employees_mobile_by_customer_id(customer_id):
    """Retrieve employees by customer_id."""
    try:
        employees = Employee.query.filter_by(customer_id=customer_id).all()

        if not employees:
            return jsonify({"error": "No employees found for the given customer ID"}), 404

        return jsonify([employee.to_dict() for employee in employees]), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve employees: {str(e)}"}), 500

@employees_mobile_bp.route('/', methods=['POST'])
def create_employee_mobile():
    """Create a new employee."""
    try:
        data = request.form
        photo = request.files.get('photo')

        # Cek duplikasi NIP dan Email
        if Employee.query.filter_by(employees_nip=data.get('employees_nip')).first():
            return jsonify({"error": "NIP sudah digunakan"}), 400
        if Employee.query.filter_by(employees_email=data.get('employees_email')).first():
            return jsonify({"error": "Email sudah digunakan"}), 400

        # Simpan foto jika ada
        photo_filename = None
        if photo:
            secure_name = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, secure_name)
            photo.save(photo_path)
            photo_filename = f'uploads/{secure_name}'

        # Timezone Asia/Jakarta
        jakarta_timezone = timezone('Asia/Jakarta')
        current_time = datetime.now(jakarta_timezone)

        # Validasi data yang diperlukan
        required_fields = ['employees_nip', 'employees_name', 'employees_email', 'position_id', 'shift_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Generate employees_code
        employees_code = generate_unique_code()

        # Hash password
        plain_password = data.get("password")
        if not plain_password:
            return jsonify({"error": "Password is required"}), 400
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Siapkan data untuk database
        employee_data = {
            "employees_code": employees_code,
            "employees_nip": data.get("employees_nip"),
            "employees_name": data.get("employees_name"),
            "employees_email": data.get("employees_email"),
            "employees_password": hashed_password,
            "position_id": data.get("position_id"),
            "shift_id": data.get("shift_id"),
            "customer_id": data.get("customer_id"),
            "photo": photo_filename,
            "created_login": current_time,
            "created_cookies": current_time,
            "created_at": current_time,
            "updated_at": current_time,
        }

        # Simpan ke database
        employee = Employee(**employee_data)
        db.session.add(employee)
        db.session.commit()

        return jsonify({"message": "Employee created successfully!", "employee": employee.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create employee: {str(e)}"}), 500

@employees_mobile_bp.route('/<int:id>', methods=['DELETE'])
def delete_employee_mobile(id):
    """Delete an employee."""
    try:
        employee = Employee.query.get(id)  # Gunakan model Employee
        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        # Hapus foto jika ada
        if employee.photo:
            photo_path = os.path.join(os.getcwd(), employee.photo)
            delete_file(photo_path)

        db.session.delete(employee)
        db.session.commit()

        return jsonify({"message": "Employee deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete employee: {str(e)}"}), 500

@employees_mobile_bp.route('/<int:id>', methods=['PUT'])
def update_employee_mobile(id):
    """Update an existing employee."""
    try:
        employee = Employee.query.get(id)
        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        data = request.form  # Ambil data dari request form
        photo = request.files.get('photo')  # Ambil file foto dari request

        # Update employees_name
        if 'employees_name' in data:
            employee.employees_name = data['employees_name']

        # Update employees_nip jika ada
        if 'employees_nip' in data:
            new_nip = data['employees_nip']
            # Cek duplikasi NIP hanya jika NIP diubah
            if new_nip != employee.employees_nip:
                if Employee.query.filter_by(employees_nip=new_nip).first():
                    return jsonify({"error": "NIP sudah digunakan"}), 400
                employee.employees_nip = new_nip

        # Update password jika diberikan
        if 'employees_password' in data and data['employees_password']:
            hashed_password = bcrypt.hashpw(data['employees_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            employee.employees_password = hashed_password

        # Update shift_id jika diberikan
        if 'shift_id' in data:
            employee.shift_id = data['shift_id']

        # Jika ada foto baru, simpan dan hapus foto lama
        if photo:
            # Cek ukuran file foto
            if photo.content_length > 500 * 1024:  # 500 KB
                return jsonify({"error": "Ukuran file tidak boleh lebih dari 500 KB."}), 400

            # Hapus foto lama jika ada
            if employee.photo:
                old_photo_path = os.path.join(os.getcwd(), employee.photo)
                delete_file(old_photo_path)

            # Generate new filename
            new_filename = generate_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, new_filename)
            photo.save(photo_path)

            # Perbarui path foto di database
            employee.photo = f'uploads/{new_filename}'

        # Simpan perubahan ke database
        db.session.commit()

        # Generate new JWT token
        token_data = {
            "id": employee.id,
            "employees_code": employee.employees_code,
            "employees_email": employee.employees_email,
            "employees_name": employee.employees_name,
            "employees_nip": employee.employees_nip,
            "position_id": employee.position_id,
            "shift_id": employee.shift_id,
            "customer_id": employee.customer_id,
            "photo": employee.photo,
            "id_area_patroli": employee.id_area_patroli
        }
        access_token = jwt.encode(token_data, "your_secret_key", algorithm="HS256")

        return jsonify({"message": "Employee updated successfully!", "employee": employee.to_dict(), "access_token": access_token}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update employee: {str(e)}"}), 500

def generate_filename(original_filename):
    # Generate 6 random characters
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    # Get current date
    now = datetime.now()
    date_str = now.strftime("%d_%m_%Y")  # Format: tanggal_bulan_tahun

    # Get file extension
    _, extension = os.path.splitext(original_filename)
    
    # Create new filename
    new_filename = f"User_Update_{random_string}_{date_str}{extension}"
    return new_filename

# Fungsi generate_unique_code tetap sama
def generate_unique_code():
    """Generate a unique employees_code."""
    while True:
        current_time = datetime.now(timezone('Asia/Jakarta'))
        year = current_time.year
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        date_part = current_time.strftime('%Y-%m-%d')
        employees_code = f"{year}/{random_string}/{date_part}"

        # Periksa apakah kode sudah ada di database
        if not Employee.query.filter_by(employees_code=employees_code).first():
            return employees_code