import os
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.feedback import Feedback
from werkzeug.utils import secure_filename
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')

# Folder untuk menyimpan foto feedback
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'feedback')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@feedback_bp.route('/', methods=['GET'])
def get_all_feedback():
    """Mengambil semua entri feedback."""
    feedback_entries = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in feedback_entries]), 200

@feedback_bp.route('/<int:id>', methods=['GET'])
def get_feedback_by_id(id):
    """Mengambil entri feedback berdasarkan ID."""
    feedback_entry = Feedback.query.get(id)
    if not feedback_entry:
        return jsonify({"error": "Feedback tidak ditemukan"}), 404
    return jsonify(feedback_entry.to_dict()), 200

@feedback_bp.route('/', methods=['POST'])
def create_feedback():
    """Membuat entri feedback baru."""
    try:
        data = request.form
        photo = request.files.get('photo')

        # Simpan foto jika ada
        photo_filename = None
        if photo:
            secure_name = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, secure_name)
            photo.save(photo_path)
            photo_filename = f'uploads/feedback/{secure_name}'  # Simpan path di kolom photo_feedback

        feedback_entry = Feedback(
            employee_id=data.get("employee_id"),
            category=data.get("category"),
            information=data.get("information"),
            photo_feedback=photo_filename,  # Simpan path foto
        )
        
        db.session.add(feedback_entry)
        db.session.commit()
        return jsonify({"message": "Feedback berhasil dibuat!", "feedback": feedback_entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal membuat feedback: {str(e)}"}), 500

@feedback_bp.route('/<int:id>', methods=['PUT'])
def update_feedback(id):
    """Memperbarui entri feedback berdasarkan ID."""
    feedback_entry = Feedback.query.get(id)
    if not feedback_entry:
        return jsonify({"error": "Feedback tidak ditemukan"}), 404
    
    data = request.form
    photo = request.files.get('photo')

    # Update foto jika ada
    if photo:
        secure_name = secure_filename(photo.filename)
        photo_path = os.path.join(UPLOAD_FOLDER, secure_name)
        photo.save(photo_path)
        feedback_entry.photo_feedback = f'uploads/feedback/{secure_name}'  # Update path foto

    # Update field lainnya
    if "employee_id" in data:
        feedback_entry.employee_id = data.get("employee_id")
    if "category" in data:
        feedback_entry.category = data.get("category")
    if "information" in data:
        feedback_entry.information = data.get("information")

    db.session.commit()
    return jsonify({"message": "Feedback berhasil diperbarui!", "feedback": feedback_entry.to_dict()}), 200

@feedback_bp.route('/<int:id>', methods=['DELETE'])
def delete_feedback(id):
    """Menghapus entri feedback berdasarkan ID."""
    feedback_entry = Feedback.query.get(id)
    if not feedback_entry:
        return jsonify({"error": "Feedback tidak ditemukan"}), 404

    db.session.delete(feedback_entry)
    db.session.commit()
    return jsonify({"message": "Feedback berhasil dihapus!"}), 200
