from flask import Blueprint, request, jsonify
from app.database import db
from app.models.notifikasi import Notification
from app.models.employees import Employee  # Import model Employee untuk mengambil token FCM
from datetime import datetime
import requests  # Untuk FCM HTTP API

notifikasi_bp = Blueprint('notifikasi', __name__, url_prefix='/api/notifikasi')

# Firebase Server Key (dapatkan dari Firebase Console)
FCM_SERVER_KEY = "BLeNHWJf0E85Z7rii8MFMtl0NP7IlwCiGWL35rCcTHJX3XSZhuflGMsTCDup949NivEm2kr-_8zIJpsDyeypTqo"

@notifikasi_bp.route('/', methods=['POST'])
def create_notification():
    """Membuat notifikasi baru dan mengirimkannya ke FCM."""
    try:
        data = request.get_json()
        employees_id = data.get('employees_id')
        message = data.get('message')
        type = data.get('type')

        if not all([employees_id, message, type]):
            return jsonify({"error": "Missing required fields"}), 400

        # Simpan notifikasi ke database
        notification = Notification(
            employees_id=employees_id,
            message=message,
            type=type,
        )
        db.session.add(notification)
        db.session.commit()

        # Kirim notifikasi ke FCM (jika ada token)
        employee = Employee.query.get(employees_id)
        if employee and employee.fcm_token:
            fcm_response = send_fcm_notification(
                fcm_token=employee.fcm_token,
                title="New Notification",
                body=message,
            )
            print("FCM Response:", fcm_response)

        return jsonify({"message": "Notification created successfully!", "notification": notification.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create notification: {str(e)}"}), 500
# GET: Ambil semua notifikasi
@notifikasi_bp.route('/', methods=['GET'])
def get_notifications():
    try:
        notifications = Notification.query.all()
        return jsonify([notification.to_dict() for notification in notifications])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch notifications: {str(e)}"}), 500

# GET: Ambil notifikasi berdasarkan ID
@notifikasi_bp.route('/<int:id_notifikasi>', methods=['GET'])
def get_notification_by_id(id_notifikasi):
    try:
        notification = Notification.query.get(id_notifikasi)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404

        return jsonify(notification.to_dict()), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch notification: {str(e)}"}), 500

# Fungsi untuk mengirim notifikasi via FCM
def send_fcm_notification(fcm_token, title, body):
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": fcm_token,
        "notification": {
            "title": title,
            "body": body,
        },
    }
    response = requests.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers)
    return response.json()


# POST: Buat notifikasi baru
@notifikasi_bp.route('/tambah', methods=['POST'])
def create_notification_tambah():
    try:
        data = request.get_json()
        employees_id = data.get('employees_id')
        message = data.get('message')
        type = data.get('type')

        if not all([employees_id, message, type]):
            return jsonify({"error": "Missing required fields"}), 400

        # Simpan notifikasi ke database
        notification = Notification(
            employees_id=employees_id,
            message=message,
            type=type,
        )
        db.session.add(notification)
        db.session.commit()

        # Kirim notifikasi ke FCM (jika ada token)
        employee = Employee.query.get(employees_id)
        if employee and employee.fcm_token:
            fcm_response = send_fcm_notification(
                fcm_token=employee.fcm_token,
                title="New Notification",
                body=message,
            )
            print("FCM Response:", fcm_response)

        return jsonify({"message": "Notification created successfully!", "notification": notification.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create notification: {str(e)}"}), 500

# PUT: Perbarui notifikasi berdasarkan ID
@notifikasi_bp.route('/<int:id_notifikasi>', methods=['PUT'])
def update_notification(id_notifikasi):
    notification = Notification.query.get(id_notifikasi)
    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    try:
        data = request.get_json()
        if 'message' in data:
            notification.message = data['message']
        if 'type' in data:
            notification.type = data['type']
        if 'is_read' in data:
            notification.is_read = data['is_read']

        notification.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Notification updated successfully!", "notification": notification.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update notification: {str(e)}"}), 500

# DELETE: Hapus notifikasi berdasarkan ID
@notifikasi_bp.route('/<int:id_notifikasi>', methods=['DELETE'])
def delete_notification(id_notifikasi):
    notification = Notification.query.get(id_notifikasi)
    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    try:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({"message": "Notification deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete notification: {str(e)}"}), 500

# POST: Kirim notifikasi manual ke FCMa
@notifikasi_bp.route('/send-fcm', methods=['POST'])
def send_manual_fcm():
    try:
        data = request.get_json()
        employees_id = data.get('employees_id')
        title = data.get('title')
        body = data.get('body')

        if not all([employees_id, title, body]):
            return jsonify({"error": "Missing required fields"}), 400

        # Ambil token FCM dari database
        employee = Employee.query.get(employees_id)
        if not employee or not employee.fcm_token:
            return jsonify({"error": "FCM token not found for this employee"}), 404

        # Kirim notifikasi ke FCM
        fcm_response = send_fcm_notification(
            fcm_token=employee.fcm_token,
            title=title,
            body=body,
        )
        return jsonify({"message": "FCM Notification sent successfully!", "response": fcm_response}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send FCM Notification: {str(e)}"}), 500
