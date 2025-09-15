from flask import Blueprint, jsonify, request
from app.database import db
from app.models.patrol_logs import PatrolLog
from datetime import datetime

patroli_bp = Blueprint('patroli', __name__, url_prefix='/api/patrol-logs')

@patroli_bp.route('/', methods=['POST'])
def create_patrol_log():
    try:
        data = request.json

        patrol_log = PatrolLog(
            employee_id=data.get('employee_id'),
            checkpoint_id=data.get('checkpoint_id'),
            checkpoint_result=data.get('checkpoint_result'),
            checkpoint_date=data.get('checkpoint_date'),
            checkpoint_in=data.get('checkpoint_in'),
            checkpoint_out=data.get('checkpoint_out'),
            checkpoint_photo=data.get('checkpoint_photo'),
            session=data.get('session')
        )

        db.session.add(patrol_log)
        db.session.commit()

        return jsonify({"message": "Patrol log created successfully!", "patrol_log": patrol_log.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create patrol log: {str(e)}"}), 500

@patroli_bp.route('/', methods=['GET'])
def get_patrol_logs():
    patrol_logs = PatrolLog.query.all()
    return jsonify([log.to_dict() for log in patrol_logs])

@patroli_bp.route('/<int:log_id>', methods=['GET'])
def get_patrol_log(log_id):
    patrol_log = PatrolLog.query.get(log_id)
    if not patrol_log:
        return jsonify({"error": "Patrol log not found"}), 404
    return jsonify(patrol_log.to_dict())

@patroli_bp.route('/<int:log_id>', methods=['PUT'])
def update_patrol_log(log_id):
    try:
        patrol_log = PatrolLog.query.get(log_id)
        if not patrol_log:
            return jsonify({"error": "Patrol log not found"}), 404

        data = request.json
        for key in ['employee_id', 'checkpoint_id', 'checkpoint_result', 'checkpoint_date', 'checkpoint_in', 'checkpoint_out', 'checkpoint_photo', 'session']:
            if key in data:
                setattr(patrol_log, key, data[key])

        db.session.commit()
        return jsonify({"message": "Patrol log updated successfully!", "patrol_log": patrol_log.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update patrol log: {str(e)}"}), 500

@patroli_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_patrol_log(log_id):
    try:
        patrol_log = PatrolLog.query.get(log_id)
        if not patrol_log:
            return jsonify({"error": "Patrol log not found"}), 404

        db.session.delete(patrol_log)
        db.session.commit()
        return jsonify({"message": "Patrol log deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete patrol log: {str(e)}"}), 500
