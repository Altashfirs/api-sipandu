import os
import jwt  # Import library JWT
from flask import Blueprint, jsonify, request, send_file
from app.database import db
from app.models.employees import Employee
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from pytz import timezone
import pandas as pd
import random
import string
import requests
import bcrypt
import traceback  # Tambahkan ini di bagian import
import qrcode
import logging
from PIL import Image, ImageDraw, ImageFont
import textwrap
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import math
import zipfile # <-- Tambahkan import ini di atas jika ingin pakai metode ZIP

# TAMBAHKAN IMPORT DI BAWAH INI
from app.models.position import Position
from app.models.shift import Shift
from app.models.customers import Customer 

# Setup logging
logging.basicConfig(level=logging.INFO)

employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def delete_file(file_path):
    """Helper function to delete a file if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


# --- FUNGSI HELPER UNTUK MENGGAMBAR SATU HALAMAN ---
def _draw_single_page(page_data, page_num, total_pages, start_index, headers, col_widths, output_dir, customer_id):
    """
    Final version using the user's uploaded Monomakh font.
    """
    SCALE = 2
    
    margin = 40 * SCALE
    row_height = 70 * SCALE
    table_header_height = 75 * SCALE
    image_width = sum(col_widths) + (margin * 2)

    num_rows_on_page = len(page_data)
    image_height = table_header_height + (num_rows_on_page * row_height) + (margin * 2)

    img = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        # Menggunakan font Monomakh yang kamu upload
        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, '..', 'fonts', 'Monomakh-Regular.ttf')

        # Pakai font yang sama untuk header dan isi, tapi beda ukuran
        font_header = ImageFont.truetype(font_path, 22 * SCALE)
        font_row = ImageFont.truetype(font_path, 20 * SCALE)
    except IOError:
        logging.error("!!! FONT MONOMAKH TIDAK DITEMUKAN. Pastikan file 'Monomakh-Regular.ttf' ada di folder 'app/fonts'.")
        # Jika font tidak ada, program berhenti agar tidak menghasilkan gambar jelek
        raise Exception("Font file not found")

    table_start_y = margin

    # Gambar Header Tabel
    current_x = margin
    for i, header in enumerate(headers):
        draw.rectangle(
            [current_x, table_start_y, current_x + col_widths[i], table_start_y + table_header_height],
            fill='#4472C4', outline='white', width=1 * SCALE
        )
        bbox = draw.textbbox((0, 0), header, font=font_header)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_x = current_x + (col_widths[i] - text_width) / 2
        text_y = table_start_y + (table_header_height - text_height) / 2
        draw.text((text_x, text_y), header, font=font_header, fill='white')
        current_x += col_widths[i]

    # Gambar Isi Tabel
    current_y = table_start_y + table_header_height
    for i, row in enumerate(page_data):
        current_x = margin
        row_number = str(start_index + i + 1)
        row_content = [
            row_number,
            row.nama or '-',
            row.nik or '-',
            row.jabatan or '-',
            row.tanggal_join.strftime("%d-%m-%Y") if row.tanggal_join else '-',
            row.nomor_kta or '-',
            row.masa_berlaku_kta.strftime("%d-%m-%Y") if row.masa_berlaku_kta else '-',
            row.keterangan_status or '-'
        ]
        
        row_color = '#F2F2F2' if i % 2 == 1 else 'white'
        
        for j, cell in enumerate(row_content):
            draw.rectangle(
                [current_x, current_y, current_x + col_widths[j], current_y + row_height],
                fill=row_color, outline='#D9D9D9', width=1 * SCALE
            )
            
            text_to_draw = str(cell)
            bbox = draw.textbbox((0, 0), text_to_draw, font=font_row)
            text_height = bbox[3] - bbox[1]
            text_y = current_y + (row_height - text_height) / 2

            if j == 0: # Kolom 'No' rata tengah
                 text_x = current_x + (col_widths[j] - (bbox[2] - bbox[0])) / 2
            else: # Kolom lainnya rata kiri
                 text_x = current_x + (20 * SCALE)

            draw.text((text_x, text_y), text_to_draw, font=font_row, fill='black')
            current_x += col_widths[j]

        current_y += row_height

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"daftar_karyawan_{customer_id}_{timestamp}_page_{page_num}_of_{total_pages}.png"
    file_path = os.path.join(output_dir, filename)
    
    img.save(file_path, dpi=(300, 300))
    
    file_url = f"/laporan/laporan-karyawan/{filename}"
    return file_url

# --- FUNGSI UTAMA (ENDPOINT) ---
@employees_bp.route('/create-employee-report-image', methods=['POST'])
def create_employee_report_image():
    try:
        data = request.get_json()
        if not data or 'customer_id' not in data:
            return jsonify({"error": "customer_id is required"}), 400

        customer_id = data.get('customer_id')

        employee_data = db.session.query(
            Employee.employees_name.label("nama"),
            Employee.employees_nip.label("nik"),
            Position.position_name.label("jabatan"),
            Employee.tanggal_join,
            Employee.nomor_kta,
            Employee.masa_berlaku_kta,
            Employee.keterangan_status,
            Customer.name.label("lokasi")
        ).join(Position, Employee.position_id == Position.position_id, isouter=True) \
         .join(Customer, Employee.customer_id == Customer.customer_id) \
         .filter(Employee.customer_id == customer_id) \
         .order_by(Employee.employees_name).all()

        if not employee_data:
            return jsonify({"error": "No employees found for the given customer_id"}), 404

        ROWS_PER_PAGE = 20
        total_rows = len(employee_data)
        total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
        
        output_dir = os.path.join(os.getcwd(), 'laporan', 'laporan-karyawan')
        os.makedirs(output_dir, exist_ok=True)
        
        SCALE = 2
        headers = ["No", "Nama", "NIK", "Jabatan", "Tgl Join", "No. KTA", "Masa Berlaku KTA", "Keterangan"]
        
        col_widths = [w * SCALE for w in [80, 320, 240, 240, 180, 200, 220, 220]]
        
        generated_urls = []
        for page_num in range(total_pages):
            start_index = page_num * ROWS_PER_PAGE
            end_index = start_index + ROWS_PER_PAGE
            page_data = employee_data[start_index:end_index]
            
            file_url = _draw_single_page(
                page_data=page_data,
                page_num=page_num + 1,
                total_pages=total_pages,
                start_index=start_index,
                headers=headers,
                col_widths=col_widths,
                output_dir=output_dir,
                customer_id=customer_id
            )
            generated_urls.append(file_url)
            logging.info(f"Generated page {page_num + 1}/{total_pages} at {file_url}")

        return jsonify({
            "message": f"Successfully generated {total_pages} page(s).",
            "image_urls": generated_urls
        }), 200

    except Exception as e:
        logging.error(f"Error saat membuat gambar daftar karyawan: {traceback.format_exc()}")
        return jsonify({"error": "Failed to generate employee report image", "message": str(e)}), 500





@employees_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json

        # Validasi input
        if 'employees_email' not in data or 'employees_password' not in data:
            return jsonify({"error": "Missing email or password"}), 400

        # Cari karyawan berdasarkan email
        employee = Employee.query.filter_by(employees_email=data['employees_email']).first()
        if not employee:
            return jsonify({"error": "Invalid email or password"}), 401

        # Debug: Periksa data employee dari database
        print("Employee Data from DB:", employee.__dict__)

        # Perbaiki hash jika menggunakan format $2y$
        hashed_password = employee.employees_password
        if hashed_password.startswith("$2y$"):
            hashed_password = hashed_password.replace("$2y$", "$2b$")

        # Verifikasi password
        if not bcrypt.checkpw(data['employees_password'].encode('utf-8'), hashed_password.encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401

        # Siapkan data untuk token JWT
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
            "id_area_patroli": employee.id_area_patroli,
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


@employees_bp.route('/fcm-token', methods=['POST'])
def save_fcm_token():
    data = request.get_json()
    id = data.get("id")  # Ganti 'employees_id' menjadi 'id' sesuai permintaan

    fcm_token = data.get("fcm_token")

    # Mengambil data employee berdasarkan 'id'
    employee = Employee.query.get(id)  # Ganti 'employees_id' dengan 'id'

    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    # Menyimpan fcm_token ke field yang sesuai di tabel Employee
    employee.fcm_token = fcm_token
    db.session.commit()  # Commit perubahan ke database
    return jsonify({"message": "Token saved successfully!"}), 200



@employees_bp.route('/', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    return jsonify([employee.to_dict() for employee in employees])

@employees_bp.route('/<int:id>', methods=['GET'])
def get_employee_by_id(id):
    """
    Retrieve an employee by id.
    """
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        return jsonify(employee.to_dict()), 200
    except Exception as e:
        print("Error:", str(e))  # Log kesalahan
        return jsonify({"error": f"Failed to retrieve employee: {str(e)}"}), 500

@employees_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_employees_by_customer_id(customer_id):
    """
    Retrieve all employees by customer_id.
    """
    try:
        employees = Employee.query.filter_by(customer_id=customer_id).all()

        if not employees:
            return jsonify({"error": "No employees found for the given customer ID"}), 404

        return jsonify([employee.to_dict() for employee in employees]), 200
    except Exception as e:
        print("Error:", str(e))  # Log kesalahan
        return jsonify({"error": f"Failed to retrieve employees: {str(e)}"}), 500


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


       
@employees_bp.route('/regenerate-qr/<int:id>', methods=['PUT'])
def regenerate_qr_code(id):
    """
    Regenerate the QR code for an employee by ID.
    This will replace the existing QR code with a new one.
    """
    try:
        # Query the employee by ID
        employee = Employee.query.get(id)
        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        # Delete the existing QR code file if it exists
        if employee.employees_code:
            old_qr_filename = f"uploads/qr_code/{employee.employees_code.replace('/', '-').lower()}.png"
            old_qr_filepath = os.path.join(os.getcwd(), old_qr_filename)
            delete_file(old_qr_filepath)

        # Generate a new QR code
        qr_data = employee.employees_code  # Use employee.employees_code as the data
        size = 300  # Ukuran default QR code

        # Buat kode QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size // 30,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Simpan gambar QR code ke file permanen
        new_qr_filename = f"uploads/qr_code/{employee.employees_code.replace('/', '-').replace(' ', '').lower()}.png"
        new_qr_filepath = os.path.join(os.getcwd(), new_qr_filename)
        img.save(new_qr_filepath)

        # Update the employee's employee_qrcode field
        employee.employee_qrcode = new_qr_filename
        db.session.commit()

        return jsonify({
            "message": "QR code regenerated successfully!",
            "employee": employee.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to regenerate QR code: {str(e)}"}), 500

@employees_bp.route('/', methods=['POST'])
def create_employee():
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

        # Generate QR Code langsung
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,  # Ukuran box default, bisa disesuaikan
            border=1,
        )
        qr.add_data(employees_code)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Simpan QR code ke file
        qr_filename = f"uploads/qr_code/{employees_code.replace('/', '-').lower()}.png"
        qr_filepath = os.path.join(os.getcwd(), qr_filename)
        qr_img.save(qr_filepath, format='PNG')

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
            "employee_qrcode": qr_filename,
            "employees_email": data.get("employees_email"),
            "employees_password": hashed_password,
            "position_id": data.get("position_id"),
            "shift_id": data.get("shift_id"),
            "customer_id": data.get("id_area_patroli"),
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

@employees_bp.route('/<int:id>', methods=['PUT'])
def update_employee(id):
    employee = Employee.query.get(id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    data = request.form
    photo = request.files.get('photo')

    # Cek duplikasi NIP dan Email (kecuali milik sendiri)
    if 'employees_nip' in data and data.get('employees_nip') != employee.employees_nip:
        if Employee.query.filter_by(employees_nip=data.get('employees_nip')).first():
            return jsonify({"error": "NIP sudah digunakan"}), 400
    if 'employees_email' in data and data.get('employees_email') != employee.employees_email:
        if Employee.query.filter_by(employees_email=data.get('employees_email')).first():
            return jsonify({"error": "Email sudah digunakan"}), 400

    # Update foto jika ada
    if photo:
        old_photo_path = os.path.join(os.getcwd(), employee.photo) if employee.photo else None
        secure_name = secure_filename(photo.filename)
        new_photo_path = os.path.join(UPLOAD_FOLDER, secure_name)

        if not os.path.exists(new_photo_path):
            photo.save(new_photo_path)
            if old_photo_path and os.path.exists(old_photo_path):
                delete_file(old_photo_path)
            employee.photo = f'uploads/{secure_name}'
        else:
            print("Foto sudah ada, menggunakan foto lama")

    # Update atribut lainnya
    for key in ['employees_nip', 'employees_name', 'employees_email', 'position_id', 'shift_id', 'customer_id']:
        if key in data and data.get(key):
            setattr(employee, key, data.get(key))

    # Hash password jika diberikan
    if 'password' in data and data.get('password'):
        hashed_password = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        employee.employees_password = hashed_password

    # Perbarui waktu
    employee.updated_at = datetime.now(timezone('Asia/Jakarta'))

    # Perbarui employees_code dan QR code jika NIP berubah
    if 'employees_nip' in data and data.get('employees_nip') != employee.employees_nip:
        current_time = datetime.now(timezone('Asia/Jakarta'))
        year = current_time.year
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        date_part = current_time.strftime('%Y-%m-%d')
        employees_code = f"{year}/{random_string}/{date_part}"
        employee.employees_code = employees_code

        # Generate QR Code baru
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(employees_code)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Simpan QR code baru
        qr_filename = f"uploads/qr_code/{employees_code.replace('/', '-').lower()}.png"
        qr_filepath = os.path.join(os.getcwd(), qr_filename)
        qr_img.save(qr_filepath, format='PNG')
        employee.employee_qrcode = qr_filename

    # Commit perubahan ke database
    db.session.commit()

    return jsonify({"message": "Employee updated successfully!", "employee": employee.to_dict()})

@employees_bp.route('/import', methods=['POST'])
def import_employees():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "File is required"}), 400

        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            return jsonify({"error": "Only Excel files are allowed"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        data = pd.read_excel(file_path)

        required_columns = ['NIP', 'Name', 'Email', 'Jabatan', 'Shift']
        if not all(col in data.columns for col in required_columns):
            return jsonify({"error": f"Excel must contain the following columns: {', '.join(required_columns)}"}), 400

        errors = []
        success_count = 0

        for index, row in data.iterrows():
            row_errors = []

            if Employee.query.filter_by(employees_nip=row['NIP']).first():
                row_errors.append("NIP sudah digunakan")
            if Employee.query.filter_by(employees_email=row['Email']).first():
                row_errors.append("Email sudah digunakan")

            if row_errors:
                errors.append({
                    "row": index + 2,
                    "NIP": row['NIP'],
                    "Email": row['Email'],
                    "errors": row_errors
                })
                continue

            jakarta_timezone = timezone('Asia/Jakarta')
            current_time = datetime.now(jakarta_timezone)

            employees_code = generate_unique_code()

            # Generate QR Code langsung
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(employees_code)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            qr_filename = f"uploads/qr_code/{employees_code.replace('/', '-').lower()}.png"
            qr_filepath = os.path.join(os.getcwd(), qr_filename)
            qr_img.save(qr_filepath, format='PNG')

            plain_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            employee_data = {
                "employees_code": employees_code,
                "employees_nip": row['NIP'],
                "employees_name": row['Name'],
                "employees_email": row['Email'],
                "employees_password": hashed_password,
                "position_id": row['Jabatan'] if not pd.isna(row['Jabatan']) else None,
                "shift_id": row['Shift'] if not pd.isna(row['Shift']) else None,
                "customer_id": row['Lokasi'] if 'Lokasi' in row and not pd.isna(row['Lokasi']) else None,
                "employee_qrcode": qr_filename,
                "photo": "0",
                "created_login": current_time,
                "created_cookies": current_time,
                "created_at": current_time,
                "updated_at": current_time,
            }

            employee = Employee(**employee_data)
            db.session.add(employee)
            success_count += 1

        db.session.commit()
        delete_file(file_path)

        return jsonify({
            "message": f"{success_count} employees imported successfully!",
            "errors": errors
        }), 207 if errors else 201
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        error_trace = traceback.format_exc()

        print("ERROR: Import Employees Failed")
        print(error_message)
        print(error_trace)

        return jsonify({
            "error": "Failed to import employees",
            "message": error_message,
            "traceback": error_trace
        }), 500

@employees_bp.route('/<int:id>', methods=['DELETE'])
def delete_employee(id):
    try:
        employee = Employee.query.get(id)
        if not employee:
            return jsonify({"error": "Employee not found"}), 404

        # Hapus foto jika ada
        if employee.photo:
            photo_path = os.path.join(os.getcwd(), employee.photo)
            delete_file(photo_path)

        # Hapus QR Code jika ada
        if employee.employees_code:
            qr_filename = f"uploads/{employee.employees_code.replace('/', '-').lower()}.png"
            qr_path = os.path.join(os.getcwd(), qr_filename)
            delete_file(qr_path)

        db.session.delete(employee)
        db.session.commit()

        return jsonify({"message": "Employee deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete employee: {str(e)}"}), 500
