from flask import Blueprint, jsonify, request
from datetime import datetime
from app.database import db
from app.models.msp_log import MSPLog
from app.models.employees import Employee
from app.models.position import Position

# Definisikan Blueprint untuk endpoint msp_log
msp_log_bp_baru = Blueprint('msp_log_baru', __name__, url_prefix='/api/msp_log_baru')

@msp_log_bp_baru.route('/history/<int:id_msp_table>', methods=['GET'])
def get_history_by_id_msp_table(id_msp_table):
    try:
        # Query data berdasarkan id_msp_table dengan join ke tabel Employee dan Position
        logs = (
            MSPLog.query
            .join(Employee, MSPLog.employees_id == Employee.id)
            .join(Position, Employee.position_id == Position.position_id)
            .filter(MSPLog.id_msp_table == id_msp_table)
            .all()
        )

        # Jika tidak ada data yang ditemukan
        if not logs:
            return jsonify({"message": "Data tidak ditemukan untuk id_msp_table ini..."}), 404

        # Mengembalikan data dalam format JSON
        result = []
        for log in logs:
            result.append({
                "created_at": log.created_at.isoformat(),
                "employees_name": log.employee.employees_name,
                "position_name": log.employee.position.position_name
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log", "details": str(e)}), 500

@msp_log_bp_baru.route('/employees/<int:employees_id>/msp_table/<int:id_msp_table>', methods=['GET'])
def get_msp_logs_by_employees_and_msp_table(employees_id, id_msp_table):
    try:
        # Query data berdasarkan employees_id dan id_msp_table
        logs = MSPLog.query.filter_by(
            employees_id=employees_id,
            id_msp_table=id_msp_table
        ).order_by(MSPLog.msp_id_log.desc()).all()

        # Jika tidak ada data yang ditemukan
        if not logs:
            return jsonify({"message": "Data tidak ditemukan untuk employees_id dan id_msp_table ini..."}), 404

        # Mengembalikan data dalam format JSON
        return jsonify([log.to_dict() for log in logs]), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log", "details": str(e)}), 500
        
# 1. GET: Mengambil semua log
@msp_log_bp_baru.route('/', methods=['GET'])
def get_all_msp_logs():
    try:
        # Query semua log, urutkan berdasarkan msp_id_log secara descending
        logs = MSPLog.query.order_by(MSPLog.msp_id_log.desc()).all()
        return jsonify([log.to_dict() for log in logs]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP logs", "details": str(e)}), 500

# 2. GET: Mengambil log berdasarkan ID
@msp_log_bp_baru.route('/<int:msp_id_log>', methods=['GET'])
def get_msp_log_by_id(msp_id_log):
    try:
        # Query log berdasarkan ID
        log = MSPLog.query.get(msp_id_log)
        if not log:
            return jsonify({"error": "MSP log not found"}), 404
        return jsonify(log.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP log", "details": str(e)}), 500

# 3. POST: Membuat log baru
@msp_log_bp_baru.route('/', methods=['POST'])
def create_msp_log():
    try:
        # Ambil data dari body request
        data = request.json

        # Validasi minimal data
        if not data:
            return jsonify({"error": "Request body is empty"}), 400

        # Buat instance baru dari MSPLog
        new_log = MSPLog(
            id_msp_table=data.get('id_msp_table'),  # Boleh null
            employees_id=data.get('employees_id'),  # Boleh null
            status=data.get('status'),              # Pastikan status diisi jika wajib
            created_at=datetime.utcnow()            # Default ke waktu saat ini
        )

        # Simpan ke database
        db.session.add(new_log)
        db.session.commit()

        # Return response sukses
        return jsonify({
            "message": "MSP log created successfully",
            "log": new_log.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create MSP log", "details": str(e)}), 500

# 4. PUT: Memperbarui log berdasarkan ID
@msp_log_bp_baru.route('/<int:msp_id_log>', methods=['PUT'])
def update_msp_log(msp_id_log):
    try:
        # Ambil data dari body request
        data = request.json

        # Cari log berdasarkan ID
        log = MSPLog.query.get(msp_id_log)
        if not log:
            return jsonify({"error": "MSP log not found"}), 404

        # Update kolom yang dikirim dalam request
        log.id_msp_table = data.get('id_msp_table', log.id_msp_table)
        log.employees_id = data.get('employees_id', log.employees_id)
        log.status = data.get('status', log.status)
        log.update_at = datetime.utcnow()  # Update waktu terakhir diubah

        # Commit perubahan ke database
        db.session.commit()

        # Return response sukses
        return jsonify({
            "message": "MSP log updated successfully",
            "log": log.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update MSP log", "details": str(e)}), 500

# 5. DELETE: Menghapus log berdasarkan ID
@msp_log_bp_baru.route('/<int:msp_id_log>', methods=['DELETE'])
def delete_msp_log(msp_id_log):
    try:
        # Cari log berdasarkan ID
        log = MSPLog.query.get(msp_id_log)
        if not log:
            return jsonify({"error": "MSP log not found"}), 404

        # Hapus log dari database
        db.session.delete(log)
        db.session.commit()

        # Return response sukses
        return jsonify({"message": "MSP log deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete MSP log", "details": str(e)}), 500