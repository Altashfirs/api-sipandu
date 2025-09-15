import os
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.presence import Presence
from datetime import date, datetime, timedelta
from werkzeug.utils import secure_filename
from app.models.employees import Employee
from app.models.position import Position
from app.models.shift import Shift
from app.models.customers import Customer
from sqlalchemy.orm import joinedload
from sqlalchemy import func, extract


presence_bp = Blueprint('presence', __name__, url_prefix='/api/presence')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@presence_bp.route('/status-by-shift', methods=['GET']) # Ganti dengan blueprint-mu
def get_presence_status_by_shift_multiple():
    """
    Mengecek status absensi dengan logika baru yang memperbolehkan
    check-in/check-out berkali-kali dalam satu hari untuk shift yang sama.
    """
    employees_id = request.args.get('employees_id')
    selected_shift_id = request.args.get('shift_id', type=int)

    if not employees_id or not selected_shift_id:
        return jsonify({"error": "Parameter 'employees_id' dan 'shift_id' diperlukan"}), 400

    try:
        shift = Shift.query.get(selected_shift_id)
        if not shift:
            return jsonify({"status": "ERROR", "message": "Shift yang dipilih tidak valid."}), 404

        today = date.today()
        # Batas pencarian sesi aktif tetap 2 hari, ini adalah praktik yang baik
        search_limit_date = today - timedelta(days=2)

        # 1. CARI SESI YANG MASIH AKTIF (time_out IS NULL) UNTUK PresenceFirst
        # Ini menjadi prioritas untuk menentukan apakah user harus checkout.
        open_presence_record = Presence.query.filter(
            Presence.employees_id == employees_id,
            Presence.shift_id == selected_shift_id,
            Presence.time_out == None,
            Presence.presence_date >= search_limit_date
        ).order_by(Presence.presence_date.desc(), Presence.time_in.desc()).first()

        # 2. CARI SEMUA RIWAYAT ABSENSI YANG SUDAH SELESAI HARI INI untuk ListPresence
        completed_today_records = Presence.query.filter(
            Presence.employees_id == employees_id,
            Presence.shift_id == selected_shift_id,
            Presence.presence_date == today,
            Presence.time_out != None
        ).order_by(Presence.time_in.asc()).all()

        # 3. TENTUKAN STATUS DAN SUSUN RESPON JSON
        response_data = {
            "shift_name": shift.shift_name,
            "PresenceFirst": None,
            "ListPresence": [rec.to_dict() for rec in completed_today_records]
        }

        if open_presence_record:
            # Jika ada sesi yang terbuka, statusnya BISA_CHECK_OUT
            response_data["status"] = "BISA_CHECK_OUT"
            response_data["PresenceFirst"] = open_presence_record.to_dict()
        else:
            # Jika tidak ada sesi terbuka, user bisa check-in lagi
            response_data["status"] = "BISA_CHECK_IN"

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": f"Terjadi kesalahan pada server: {str(e)}"}), 500





@presence_bp.route('/', methods=['GET'])
def get_presences():
    presences = Presence.query.all()
    return jsonify([presence.to_dict() for presence in presences]), 200

@presence_bp.route('/<int:id>', methods=['GET'])
def get_presence_by_id(id):
    presence = Presence.query.get(id)
    if not presence:
        return jsonify({"error": "Presence not found"}), 404
    return jsonify(presence.to_dict()), 200

@presence_bp.route('/harian', methods=['GET'])
def get_harian_data():
    try:
        # Get month and year from query parameters, default to current month and year
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)

        # Query to get presences with their corresponding employee names, filtered by month and year
        presences = (
            db.session.query(Employee.employees_name, Presence)
            .join(Presence, Employee.id == Presence.employees_id)
            .filter(extract('month', Presence.presence_date) == month)
            .filter(extract('year', Presence.presence_date) == year)
            .order_by(Presence.presence_date.desc())  # Sort by date descending
            .all()
        )

        # Organize the data into the desired format
        data = {}
        for employees_name, presence in presences:
            presence_month = presence.presence_date.strftime('%Y-%m')  # Format month as YYYY-MM
            
            if employees_name not in data:
                data[employees_name] = {
                    "employees_name": employees_name,
                    "presence": {}
                }
            
            if presence_month not in data[employees_name]["presence"]:
                data[employees_name]["presence"][presence_month] = {
                    "presence_month": presence_month,
                    "details": []
                }
            
            # Append presence details
            data[employees_name]["presence"][presence_month]["details"].append({
                "time_in": presence.time_in.strftime('%H:%M:%S') if presence.time_in else None,
                "time_out": presence.time_out.strftime('%H:%M:%S') if presence.time_out else None,
                "present_id": presence.present_id,
                "presence_date": presence.presence_date.strftime('%Y-%m-%d') if presence.presence_date else None
            })

        # Convert the dictionary to a list
        result = []
        for employee in data.values():
            employee["presence"] = list(employee["presence"].values())  # Convert presence dict to list
            result.append(employee)

        return jsonify({"data": result}), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data harian: {str(e)}"}), 500
    
# New route to retrieve presence data for a specific employees_id
@presence_bp.route('/employee/<int:employees_id>', methods=['GET'])
def get_presences_by_employee_id(employees_id):
    try:
        presences = Presence.query.filter_by(employees_id=employees_id).all()
        if not presences:
            return jsonify({"message": "Tidak ada data kehadiran untuk employees_id ini."}), 404
        return jsonify([presence.to_dict() for presence in presences]), 200
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

# @presence_bp.route('/filter_customer', methods=['GET'])
# def filter_presences_by_customer():
#     customer_id = request.args.get('customer_id')
#     tanggal_awal = request.args.get('tanggal_awal')
#     tanggal_akhir = request.args.get('tanggal_akhir')

#     # Validasi input
#     if not customer_id or not tanggal_awal or not tanggal_akhir:
#         return jsonify({"error": "customer_id, tanggal_awal, dan tanggal_akhir harus diisi"}), 400

#     try:
#         # Konversi tanggal dari string ke objek datetime
#         start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d')
#         end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d')

#         # Query untuk mendapatkan data kehadiran dalam rentang tanggal berdasarkan customer_id
#         presences = Presence.query.join(Employee).filter(
#             Employee.customer_id == customer_id,
#             Presence.presence_date >= start_date,
#             Presence.presence_date <= end_date
#         ).order_by(Presence.presence_date.desc()).all()

#         # Cek jika tidak ada data kehadiran ditemukan
#         if not presences:
#             return jsonify({"message": "Tidak ada data tersedia."}), 404

#         # Mengembalikan data kehadiran dalam format JSON
#         return jsonify([presence.to_dict() for presence in presences]), 200

#     except ValueError:
#         return jsonify({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD."}), 400
#     except Exception as e:
#         return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

@presence_bp.route('/filter_customer', methods=['GET'])
def filter_presences_by_customer():
    customer_id = request.args.get('customer_id')
    tanggal_awal = request.args.get('tanggal_awal')
    tanggal_akhir = request.args.get('tanggal_akhir')

    # Validasi input
    if not customer_id or not tanggal_awal or not tanggal_akhir:
        return jsonify({"error": "customer_id, tanggal_awal, dan tanggal_akhir harus diisi"}), 400

    try:
        # Konversi tanggal dari string ke objek datetime
        start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d')
        end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d')

        # Query dengan joinedload untuk mengambil data Employee dan Shift
        presences = Presence.query.options(
            joinedload(Presence.employee).joinedload(Employee.shift)
        ).join(Employee).filter(
            Employee.customer_id == customer_id,
            Presence.presence_date >= start_date,
            Presence.presence_date <= end_date
        ).order_by(Presence.presence_date.desc()).all()

        # Cek jika tidak ada data kehadiran ditemukan
        if not presences:
            return jsonify({"message": "Tidak ada data tersedia."}), 404

        # Mengembalikan data kehadiran dengan informasi Shift
        result = []
        for presence in presences:
            presence_dict = presence.to_dict()
            presence_dict['employee'] = presence.employee.to_dict() if presence.employee else {}
            presence_dict['shift'] = presence.employee.shift.to_dict() if presence.employee and presence.employee.shift else {}
            result.append(presence_dict)

        return jsonify(result), 200

    except ValueError:
        return jsonify({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500
  
@presence_bp.route('/check_customer', methods=['GET'])
def check_presence_by_customer():
    customer_id = request.args.get('customer_id')
    presence_date = request.args.get('presence_date')

    if not customer_id or not presence_date:
        return jsonify({"error": "customer_id dan presence_date harus diisi"}), 400

    try:
        # Konversi presence_date ke objek date
        presence_date_obj = datetime.strptime(presence_date, '%Y-%m-%d').date()

        # Query dengan joinedload untuk mengambil data Employee dan Shift
        presence = Presence.query.options(
            joinedload(Presence.employee).joinedload(Employee.shift)
        ).join(Employee).filter(
            Employee.customer_id == customer_id,
            Presence.presence_date == presence_date_obj
        ).all()

        if presence:
            # Mengembalikan data kehadiran dengan informasi Shift
            result = []
            for p in presence:
                presence_dict = p.to_dict()
                presence_dict['employee'] = p.employee.to_dict() if p.employee else {}
                presence_dict['shift'] = p.employee.shift.to_dict() if p.employee and p.employee.shift else {}
                result.append(presence_dict)

            return jsonify(result), 200
        else:
            return jsonify({"message": "Tidak ada data kehadiran."}), 404

    except ValueError:
        return jsonify({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal memeriksa data kehadiran: {str(e)}"}), 500


# @presence_bp.route('/check_customer', methods=['GET'])
# def check_presence_by_customer():
#     customer_id = request.args.get('customer_id')
#     presence_date = request.args.get('presence_date')

#     if not customer_id or not presence_date:
#         return jsonify({"error": "customer_id dan presence_date harus diisi"}), 400

#     try:
#         # Konversi presence_date ke objek date
#         presence_date_obj = datetime.strptime(presence_date, '%Y-%m-%d').date()

#         # Mencari data kehadiran berdasarkan customer_id dan presence_date
#         presence = Presence.query.join(Employee).filter(
#             Employee.customer_id == customer_id,
#             Presence.presence_date == presence_date_obj
#         ).all()

#         if presence:
#             return jsonify([p.to_dict() for p in presence]), 200
#         else:
#             return jsonify({"message": "Tidak ada data kehadiran."}), 404

#     except ValueError:
#         return jsonify({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD."}), 400
#     except Exception as e:
#         return jsonify({"error": f"Gagal memeriksa data kehadiran: {str(e)}"}), 500

        
@presence_bp.route('/latest', methods=['GET'])
def get_latest_presence():
    try:
        # Subquery to get the latest presence_id for each employees_id
        subquery = (
            db.session.query(
                Presence.employees_id,
                func.max(Presence.presence_id).label('latest_presence_id')
            )
            .group_by(Presence.employees_id)
            .subquery()
        )

        # Main query to get the latest presence records
        latest_presences = (
            db.session.query(Presence)
            .join(subquery, Presence.presence_id == subquery.c.latest_presence_id)
            .join(Employee, Presence.employees_id == Employee.id)
            .join(Position, Employee.position_id == Position.position_id)
            .join(Shift, Employee.shift_id == Shift.shift_id)
            .join(Customer, Employee.customer_id == Customer.customer_id)
            .all()
        )

        if not latest_presences:
            return jsonify({"message": "Tidak ada data kehadiran."}), 404

        # Convert the results to a list of dictionaries
        result = []
        for presence in latest_presences:
            presence_dict = presence.to_dict()
            presence_dict['employee'] = presence.employee.to_dict()
            presence_dict['position'] = presence.employee.position.to_dict() if presence.employee.position else None
            presence_dict['shift'] = presence.employee.shift.to_dict() if presence.employee.shift else None
            presence_dict['customer'] = presence.employee.customer.to_dict() if presence.employee.customer else None
            result.append(presence_dict)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

@presence_bp.route('/tujuh', methods=['GET'])
def get_presences_last_seven_days():
    try:
        today = datetime.utcnow().date()
        seven_days_ago = today - timedelta(days=7)

        presences = Presence.query.filter(
            Presence.presence_date >= seven_days_ago,
            Presence.presence_date <= today
        ).order_by(Presence.presence_date.desc()).all()

        if not presences:
            return jsonify({"message": "Tidak ada data kehadiran dalam 7 hari terakhir."}), 404

        return jsonify([presence.to_dict() for presence in presences]), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

@presence_bp.route('/tujuh/<int:customer_id>', methods=['GET'])
def get_presences_last_seven_days_by_customer(customer_id):
    try:
        today = datetime.utcnow().date()
        seven_days_ago = today - timedelta(days=7)

        presences = Presence.query.join(Presence.employee).filter(
            Presence.presence_date >= seven_days_ago,
            Presence.presence_date <= today,
            Presence.employee.has(customer_id=customer_id)
        ).order_by(Presence.presence_date.desc()).all()

        if not presences:
            return jsonify({"message": "Tidak ada data kehadiran dalam 7 hari terakhir."}), 404

        return jsonify([presence.to_dict() for presence in presences]), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500
        
@presence_bp.route('/now', methods=['GET'])
def get_presences_now():
    try:
        # Gunakan tanggal saat ini
        today = datetime.utcnow().date()

        # Urutkan berdasarkan presence_id dari terbesar ke terkecil
        presences = Presence.query.filter(
            Presence.presence_date == today
        ).order_by(Presence.presence_id.desc()).all()

        if not presences:
            return jsonify({"message": "Tidak ada data kehadiran untuk tanggal ini."}), 404

        return jsonify([presence.to_dict() for presence in presences]), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

@presence_bp.route('/today', methods=['GET'])
def get_presences_today():
    try:
        # Ambil tanggal dari query parameter 'presence_date'
        date_str = request.args.get('presence_date')
        if not date_str:
            return jsonify({"error": "Parameter 'presence_date' diperlukan dalam format YYYY-MM-DD"}), 400
        
        # Konversi string tanggal ke objek date
        try:
            today = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Format tanggal salah, gunakan YYYY-MM-DD"}), 400

        # Debugging (opsional)
        print(f"Tanggal yang diterima: {today}")

        # Urutkan berdasarkan presence_id dari terbesar ke terkecil
        presences = Presence.query.filter(
            Presence.presence_date == today
        ).order_by(Presence.presence_id.desc()).all()

        if not presences:
            return jsonify({"message": "Tidak ada data kehadiran untuk tanggal ini."}), 404

        return jsonify([presence.to_dict() for presence in presences]), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

@presence_bp.route('/today/<int:customer_id>', methods=['GET'])
def get_presences_today_by_customer(customer_id):
    try:
        today = datetime.utcnow().date()

        presences = Presence.query.join(Presence.employee).filter(
            Presence.presence_date == today,
            Presence.employee.has(customer_id=customer_id)
        ).order_by(Presence.presence_date.desc()).all()

        if not presences:
            return jsonify({"message": "Tidak ada data kehadiran hari ini."}), 404

        return jsonify([presence.to_dict() for presence in presences]), 200

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data kehadiran: {str(e)}"}), 500

@presence_bp.route('/filter', methods=['GET'])
def filter_presences_with_details():
    employees_id = request.args.get('employees_id')
    tanggal_awal = request.args.get('tanggal_awal')
    tanggal_akhir = request.args.get('tanggal_akhir')

    if not employees_id or not tanggal_awal or not tanggal_akhir:
        return jsonify({"error": "employees_id, tanggal_awal, dan tanggal_akhir harus diisi"}), 400

    try:
        start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d').date()
        end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d').date()

        # --- PERBAIKAN 1: Query dibuat lebih efisien ---
        # Mengambil data presensi dan langsung menggabungkannya (join) dengan data shift-nya.
        presences = Presence.query.options(
            joinedload(Presence.shift)
        ).filter(
            Presence.employees_id == employees_id,
            Presence.presence_date.between(start_date, end_date)
        ).order_by(Presence.presence_date.desc()).all()

        if not presences:
            return jsonify({"message": "Tidak ada data tersedia."}), 404

        # --- PERBAIKAN 2: Proses data di backend untuk menambahkan status ---
        result = []
        for p in presences:
            # Menggunakan to_dict() dari model yang sudah kita perbaiki
            presence_dict = p.to_dict() 
            
            status_masuk = "N/A"
            status_pulang = "N/A"

            # Logika untuk menentukan status tepat waktu atau tidak
            if p.shift: # Memastikan data shift ada untuk menghindari error
                # Cek Status Masuk (Time In)
                if p.time_in:
                    status_masuk = "Tepat Waktu" if p.time_in <= p.shift.time_in else "Terlambat"
                
                # Cek Status Pulang (Time Out)
                if p.time_out:
                    status_pulang = "Pulang Tepat Waktu" if p.time_out >= p.shift.time_out else "Pulang Awal"
                else:
                    status_pulang = "Belum Checkout"
            
            # Sisipkan kolom status baru ke dalam dictionary
            presence_dict['status_masuk'] = status_masuk
            presence_dict['status_pulang'] = status_pulang
            result.append(presence_dict)

        # --- PERBAIKAN 3: Kirim hasil yang sudah diperkaya ---
        return jsonify(result), 200

    except ValueError:
        return jsonify({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data riwayat: {str(e)}"}), 500

@presence_bp.route('/check', methods=['GET'])
def check_presence_with_punctuality_complete():
    employees_id = request.args.get('employees_id')
    presence_date = request.args.get('presence_date')

    if not employees_id or not presence_date:
        return jsonify({"error": "employees_id dan presence_date harus diisi"}), 400

    try:
        # Ambil data presensi sekaligus dengan data shift-nya
        presence = Presence.query.options(
            joinedload(Presence.shift)
        ).filter(
            Presence.employees_id == employees_id,
            Presence.presence_date == presence_date
        ).first()
        
        if presence:
            presence_dict = presence.to_dict()

            # --- LOGIKA BARU UNTUK STATUS MASUK & PULANG ---
            status_masuk = "N/A"
            status_pulang = "N/A"

            if presence.shift:
                # Cek Status Masuk (Time In)
                if presence.time_in:
                    if presence.time_in <= presence.shift.time_in:
                        status_masuk = "Tepat Waktu"
                    else:
                        status_masuk = "Terlambat"
                
                # Cek Status Pulang (Time Out)
                if presence.time_out:
                    if presence.time_out >= presence.shift.time_out:
                        status_pulang = "Pulang Tepat Waktu"
                    else:
                        status_pulang = "Pulang Awal"
                else:
                    status_pulang = "Belum Checkout"
            
            # Sisipkan dua kolom status baru ke dalam JSON
            presence_dict['status_masuk'] = status_masuk
            presence_dict['status_pulang'] = status_pulang
            
            return jsonify(presence_dict), 200
        else:
            return jsonify({"message": "Tidak ada data kehadiran."}), 404
            
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500


@presence_bp.route('/check-status', methods=['GET'])
def check_status_presence():
    employees_id = request.args.get('employees_id')

    if not employees_id:
        return jsonify({"error": "employees_id harus diisi"}), 400

    try:
        # Ambil tanggal hari ini dan kemarin
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # Ambil data presensi terbaru dengan time_out NULL dan presence_date hari ini atau kemarin
        presence = Presence.query.options(
            joinedload(Presence.shift)
        ).filter(
            Presence.employees_id == employees_id,
            Presence.time_out.is_(None),  # Filter time_out NULL
            Presence.presence_date.in_([today, yesterday])  # Filter hari ini atau kemarin
        ).order_by(
            Presence.presence_id.desc()  # Ambil data terbaru berdasarkan presence_id
        ).first()

        if presence:
            presence_dict = presence.to_dict()

            # Logika status masuk
            status_masuk = "N/A"
            status_pulang = "Belum Checkout"  # Karena time_out dijamin NULL

            if presence.shift and presence.time_in:
                if presence.time_in <= presence.shift.time_in:
                    status_masuk = "Tepat Waktu"
                else:
                    status_masuk = "Terlambat"

            # Tambahkan status ke response
            presence_dict['status_masuk'] = status_masuk
            presence_dict['status_pulang'] = status_pulang

            return jsonify(presence_dict), 200
        else:
            return jsonify({"message": "Tidak ada data kehadiran dengan status belum checkout untuk hari ini atau kemarin."}), 404

    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500




@presence_bp.route('/create-new', methods=['POST'])
def create_presence_new_two():
    try:
        data = request.form
        picture_in = request.files.get('picture_in')

        # --- 1. Validasi & 2. Konversi Data ---
        required_fields = ['employees_id', 'shift_id', 'presence_date', 'time_in']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Field '{field}' harus diisi"}), 400

        employees_id = data.get('employees_id')
        shift_id_input = int(data.get('shift_id'))
        presence_date_str = data.get('presence_date')
        time_in_str = data.get('time_in')
        
        try:
            presence_date = datetime.strptime(presence_date_str, '%Y-%m-%d').date()
            time_in = datetime.strptime(time_in_str, '%H:%M:%S').time()
        except ValueError as e:
            return jsonify({"error": f"Format tanggal atau waktu salah: {e}"}), 400

        # --- 3. Logika Penentuan Shift ---
        is_overshift = False
        detected_shift_id = None
        if shift_id_input == 6:
            is_overshift = True
            all_shifts = Shift.query.all()
            for shift in all_shifts:
                if shift.shift_id == 6: continue
                if shift.time_in <= shift.time_out:
                    if shift.time_in <= time_in <= shift.time_out:
                        detected_shift_id = shift.shift_id
                        break 
                else:
                    if time_in >= shift.time_in or time_in <= shift.time_out:
                        detected_shift_id = shift.shift_id
                        break
        else:
            is_overshift = False
            detected_shift_id = shift_id_input
        
        if shift_id_input == 6 and detected_shift_id is None:
            return jsonify({"error": f"Jam masuk {time_in_str} tidak cocok dengan shift manapun."}), 400

        # --- 4. Proses dan Simpan Gambar ---
        picture_in_filename = None
        if picture_in:
            # Langsung amankan nama file yang dikirim dari frontend
            secure_name = secure_filename(picture_in.filename)
            picture_in_path = os.path.join(UPLOAD_FOLDER, secure_name)
            
            try:
                picture_in.save(picture_in_path)
                # Simpan path relatifnya ke database
                picture_in_filename = f'uploads/{secure_name}'
            except Exception as e:
                return jsonify({"error": f"Gagal menyimpan gambar: {e}"}), 500

        # --- 5. Buat Record Baru ---
        new_presence = Presence(
            employees_id=employees_id,
            shift_id=shift_id_input,
            is_overshift=is_overshift,
            detected_shift_id=detected_shift_id,
            presence_date=presence_date,
            time_in=time_in,
            picture_in=picture_in_filename,
            present_id=1,
            latitude_longtitude_in=data.get('latitude_longtitude_in'),
        )
        db.session.add(new_presence)
        db.session.commit()

        return jsonify({
            "message": "Berhasil membuat data kehadiran!", 
            "presence": new_presence.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"FATAL ERROR in create_presence_new: {str(e)}")
        return jsonify({"error": f"Terjadi kesalahan pada server: {str(e)}"}), 500




@presence_bp.route('/create', methods=['POST'])
def create_presence_new():
    try:
        data = request.form
        picture_in = request.files.get('picture_in')

        # --- 1. Validasi & 2. Konversi Data (Tetap sama) ---
        required_fields = ['employees_id', 'shift_id', 'presence_date', 'time_in']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Field '{field}' harus diisi"}), 400

        employees_id = data.get('employees_id')
        shift_id_input = int(data.get('shift_id'))
        presence_date_str = data.get('presence_date')
        time_in_str = data.get('time_in')
        
        try:
            presence_date = datetime.strptime(presence_date_str, '%Y-%m-%d').date()
            time_in = datetime.strptime(time_in_str, '%H:%M:%S').time()
        except ValueError as e:
            return jsonify({"error": f"Format tanggal atau waktu salah: {e}"}), 400

        # --- 3. Logika Penentuan Shift (Tetap sama) ---
        is_overshift = False
        detected_shift_id = None
        if shift_id_input == 6:
            is_overshift = True
            all_shifts = Shift.query.all()
            for shift in all_shifts:
                if shift.shift_id == 6: continue
                if shift.time_in <= shift.time_out:
                    if shift.time_in <= time_in <= shift.time_out:
                        detected_shift_id = shift.shift_id
                        break 
                else:
                    if time_in >= shift.time_in or time_in <= shift.time_out:
                        detected_shift_id = shift.shift_id
                        break
        else:
            is_overshift = False
            detected_shift_id = shift_id_input
        
        if shift_id_input == 6 and detected_shift_id is None:
            return jsonify({"error": f"Jam masuk {time_in_str} tidak cocok dengan shift manapun."}), 400

        # --- 4. Pengecekan Duplikat (Tetap sama) ---
        existing_presence = Presence.query.filter_by(
            employees_id=employees_id,
            presence_date=presence_date,
            detected_shift_id=detected_shift_id 
        ).first()
        if existing_presence:
            return jsonify({"error": f"Karyawan sudah tercatat absen untuk shift ini pada tanggal {presence_date_str}."}), 409

        # --- 5. Proses dan Simpan Gambar (INI YANG DIPERBAIKI) ---
        picture_in_filename = None
        if picture_in:
            # Langsung amankan nama file yang dikirim dari frontend
            secure_name = secure_filename(picture_in.filename)
            picture_in_path = os.path.join(UPLOAD_FOLDER, secure_name)
            
            try:
                picture_in.save(picture_in_path)
                # Simpan path relatifnya ke database
                picture_in_filename = f'uploads/{secure_name}'
            except Exception as e:
                return jsonify({"error": f"Gagal menyimpan gambar: {e}"}), 500

        # --- 6. Buat Record Baru (Tetap sama) ---
        new_presence = Presence(
            employees_id=employees_id,
            shift_id=shift_id_input,
            is_overshift=is_overshift,
            detected_shift_id=detected_shift_id,
            presence_date=presence_date,
            time_in=time_in,
            picture_in=picture_in_filename,
            present_id=1,
            latitude_longtitude_in=data.get('latitude_longtitude_in'),
        )
        db.session.add(new_presence)
        db.session.commit()

        return jsonify({
            "message": "Berhasil membuat data kehadiran!", 
            "presence": new_presence.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"FATAL ERROR in create_presence_new: {str(e)}")
        return jsonify({"error": f"Terjadi kesalahan pada server: {str(e)}"}), 500


@presence_bp.route('/update/<int:id>', methods=['PUT'])
def update_presence_new(id):
    try:
        presence = Presence.query.get(id)
        if not presence:
            return jsonify({"error": "Data kehadiran tidak ditemukan"}), 404

        data = request.form
        picture_out = request.files.get('picture_out')

        if presence.time_out is not None:
            return jsonify({"error": "Anda Sudah Melakukan Absensi Pulang."}), 400

        # Update field yang diperbolehkan
        if 'time_out' in data:
            try:
                presence.time_out = datetime.strptime(data['time_out'], '%H:%M:%S').time()
            except ValueError:
                return jsonify({"error": "Field 'time_out' harus dalam format HH:MM:SS"}), 400

        if 'latitude_longtitude_out' in data:
            presence.latitude_longtitude_out = data['latitude_longtitude_out']

        if 'information' in data:
            presence.information = data['information']

        if picture_out:
            secure_name = secure_filename(picture_out.filename)
            picture_out_path = os.path.join(UPLOAD_FOLDER, secure_name)
            picture_out.save(picture_out_path)
            presence.picture_out = f'uploads/{secure_name}'

        db.session.commit()

        return jsonify({"message": "Berhasil memperbarui data kehadiran!", "presence": presence.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": f"Gagal memperbarui data kehadiran: {str(e)}"}), 500


@presence_bp.route('/', methods=['POST'])
def create_presence():
    try:
        data = request.form
        picture_in = request.files.get('picture_in')  # Mengambil file gambar dari request

        # Log data yang diterima
        print("Data yang diterima:", data)
        print("Gambar yang diterima:", picture_in)

        required_fields = ['employees_id', 'presence_date', 'time_in']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Field '{field}' harus diisi"}), 400

        # Validasi dan konversi presence_date dan time_in
        presence_date = data.get('presence_date')
        time_in = data.get('time_in')

        if not presence_date:
            return jsonify({"error": "Tanggal kehadiran harus diisi dan tidak boleh kosong."}), 400
        if not time_in:
            return jsonify({"error": "Waktu masuk harus diisi dan tidak boleh kosong."}), 400

        # Log nilai presence_date dan time_in
        print("Tanggal Kehadiran:", presence_date)
        print("Waktu Masuk:", time_in)

        # Cek apakah presence_date sudah ada
        existing_presence = Presence.query.filter_by(employees_id=data['employees_id'], presence_date=presence_date).first()
        if existing_presence:
            return jsonify({"error": "Data kehadiran untuk tanggal ini sudah ada."}), 400

        # Simpan gambar picture_in jika ada
        picture_in_filename = None
        if picture_in:
            secure_name = secure_filename(picture_in.filename)
            picture_in_path = os.path.join(UPLOAD_FOLDER, secure_name)
            picture_in.save(picture_in_path)
            picture_in_filename = f'uploads/{secure_name}'  # Simpan path relatif

        # Buat entri kehadiran
        presence = Presence(
            employees_id=data['employees_id'],
            presence_date=presence_date,
            time_in=time_in,
            picture_in=picture_in_filename,  # Simpan nama file gambar
            present_id=1,
            latitude_longtitude_in=data.get('latitude_longtitude_in'),
        )

        db.session.add(presence)
        db.session.commit()

        return jsonify({"message": "Berhasil membuat data kehadiran!", "presence": presence.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))  # Log error detail
        return jsonify({"error": f"Gagal membuat data kehadiran: {str(e)}"}), 500

@presence_bp.route('/<int:id>', methods=['PUT'])
def update_presence(id):
    try:
        presence = Presence.query.get(id)
        if not presence:
            return jsonify({"error": "Data kehadiran tidak ditemukan"}), 404

        data = request.form  # Mengambil data form
        picture_out = request.files.get('picture_out')  # Mengambil file gambar untuk picture_out

        # Log data yang diterima
        print("Data untuk update:", data)
        print("Gambar yang diterima:", picture_out)

        # Cek apakah time_out masih null
        if presence.time_out is not None:
            return jsonify({"error": "Anda Sudah Melakukan Absensi Pulang. Sampai Jumpa Besok!"}), 400

        # Update field yang diperbolehkan
        if 'time_out' in data:
            try:
                presence.time_out = datetime.strptime(data['time_out'], '%H:%M:%S').time()
            except ValueError:
                return jsonify({"error": "Field 'time_out' harus dalam format HH:MM:SS"}), 400

        if 'latitude_longtitude_out' in data:
            presence.latitude_longtitude_out = data['latitude_longtitude_out']

        if 'information' in data:
            presence.information = data['information']

        # Simpan gambar picture_out jika ada
        if picture_out:
            secure_name = secure_filename(picture_out.filename)
            picture_out_path = os.path.join(UPLOAD_FOLDER, secure_name)
            picture_out.save(picture_out_path)
            presence.picture_out = f'uploads/{secure_name}'  # Simpan path relatif

        # Commit perubahan
        db.session.commit()

        return jsonify({"message": "Berhasil memperbarui data kehadiran!", "presence": presence.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))  # Log error detail
        return jsonify({"error": f"Gagal memperbarui data kehadiran: {str(e)}"}), 500

@presence_bp.route('/edit/<int:id>', methods=['PUT'])
def update_presence_edit(id):
    try:
        # Cari kehadiran berdasarkan id di URL
        presence = Presence.query.get(id)
        if not presence:
            return jsonify({"error": "Data kehadiran tidak ditemukan"}), 404

        data = request.get_json()  # Mengambil data JSON

        # Validasi input
        if not data:
            return jsonify({"error": "Tidak ada data yang dikirim"}), 400

        # Cek keberadaan present_id dan information
        present_id = data.get('present_id')
        information = data.get('information')

        if present_id is not None:
            presence.present_id = present_id  # Update present_id

        if information is not None:
            presence.information = information  # Update information

        # Commit perubahan
        db.session.commit()

        return jsonify({
            "message": "Berhasil memperbarui data kehadiran!", 
            "presence": presence.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": f"Gagal memperbarui data kehadiran: {str(e)}"}), 500


@presence_bp.route('/<int:id>', methods=['DELETE'])
def delete_presence(id):
    presence = Presence.query.get(id)
    if not presence:
        return jsonify({"error": "Presence tidak ditemukan"}), 404

    db.session.delete(presence)
    db.session.commit()
    return jsonify({"message": "Presence berhasil dihapus!"}), 200