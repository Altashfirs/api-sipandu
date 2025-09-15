from flask import Blueprint, jsonify, request
from app.database import db
from app.models.msp_log import MSPLog
from app.models.msp_table import MSPTable  # Jika perlu relasi dengan MSPTable

msp_log_bp = Blueprint('msp_log', __name__, url_prefix='/api/msp_log')

@msp_log_bp.route('/', methods=['GET'])
def get_all_msp_logs():
    try:
        logs = MSPLog.query.order_by(MSPLog.msp_id_log.desc()).all()
        return jsonify([log.to_dict() for log in logs]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP logs", "details": str(e)}), 500

@msp_log_bp.route('/<int:msp_id_log>', methods=['GET'])
def get_msp_log_by_id(msp_id_log):
    try:
        log = MSPLog.query.get(msp_id_log)
        if not log:
            return jsonify({"error": "MSP log not found"}), 404
        return jsonify(log.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP log", "details": str(e)}), 500

@msp_log_bp.route('/', methods=['POST'])
def create_msp_log():
    try:
        data = request.json

        # Kolom id_msp_table dan employees_id boleh null, jadi tidak wajib
        entry = MSPLog(
            id_msp_table=data.get('id_msp_table'),  # Boleh null
            employees_id=data.get('employees_id'),  # Boleh null
            created_at=data.get('created_at', datetime.utcnow())  # Default ke waktu saat ini jika tidak disediakan
        )

        db.session.add(entry)
        db.session.commit()
        return jsonify({"message": "MSP log created successfully", "log": entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create MSP log", "details": str(e)}), 500

@msp_log_bp.route('/<int:msp_id_log>', methods=['PUT'])
def update_msp_log(msp_id_log):
    try:
        data = request.json
        log = MSPLog.query.get(msp_id_log)

        if not log:
            return jsonify({"error": "MSP log not found"}), 404

        log.id_msp_table = data.get('id_msp_table', log.id_msp_table)
        log.employees_id = data.get('employees_id', log.employees_id)
        log.created_at = data.get('created_at', log.created_at)  # Hati-hati dengan update waktu, biasanya tidak diubah

        db.session.commit()
        return jsonify({"message": "MSP log updated successfully", "log": log.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update MSP log", "details": str(e)}), 500

@msp_log_bp.route('/<int:msp_id_log>', methods=['DELETE'])
def delete_msp_log(msp_id_log):
    try:
        log = MSPLog.query.get(msp_id_log)
        if not log:
            return jsonify({"error": "MSP log not found"}), 404

        db.session.delete(log)
        db.session.commit()
        return jsonify({"message": "MSP log deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete MSP log", "details": str(e)}), 500