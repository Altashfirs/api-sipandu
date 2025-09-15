import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.database import db
from app.models.business_card import BusinessCard
from datetime import datetime
from pytz import timezone
import mimetypes  # Untuk mendeteksi tipe file secara otomatis

# Zona waktu Asia/Jakarta
jakarta_tz = timezone('Asia/Jakarta')

business_card_bp = Blueprint('business_card', __name__, url_prefix='/api/business-cards')

@business_card_bp.route('/photo', methods=['GET'])
def get_latest_active_photo():
    try:
        # Ambil business card terakhir dengan active="2", diurutkan berdasarkan updated_at descending
        latest_card = BusinessCard.query.filter_by(active="2").order_by(BusinessCard.updated_at.desc()).first()

        if not latest_card or not latest_card.photo:
            return jsonify({"error": "No business card with active status 2 found or no photo available"}), 404

        # Dapatkan path absolut dari foto
        photo_path = os.path.join(os.getcwd(), latest_card.photo)

        if not os.path.exists(photo_path):
            return jsonify({"error": "Photo file not found"}), 404

        # Deteksi tipe file secara otomatis
        mimetype, _ = mimetypes.guess_type(photo_path)
        if not mimetype:
            mimetype = 'application/octet-stream'  # Default jika tipe tidak dikenali

        # Kirim file foto sebagai respons
        return send_file(
            photo_path,
            mimetype=mimetype,
            as_attachment=False  # Jangan memaksa download, tampilkan langsung di browser
        )
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve photo: {str(e)}"}), 500
 

@business_card_bp.route('/', methods=['GET'])
def get_business_cards():
    try:
        business_cards = BusinessCard.query.all()
        return jsonify([card.to_dict() for card in business_cards])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch business cards: {str(e)}"}), 500

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@business_card_bp.route('/', methods=['POST'])
def create_business_card():
    try:
        name = request.form.get('name')
        active = request.form.get('active')
        photo = request.files.get('photo')

        if not name or not active or not photo:
            return jsonify({"error": "Missing required fields: 'name', 'active', or 'photo'"}), 400

        # Save file using absolute path
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(photo_path)

        # Save relative path to database
        relative_path = f'uploads/{filename}'

        # Save data to database
        card = BusinessCard(
            name=name,
            photo=relative_path,
            active=active,
            created_at=datetime.now(jakarta_tz),
            updated_at=datetime.now(jakarta_tz)
        )
        db.session.add(card)
        db.session.commit()

        return jsonify({"message": "Business card created successfully!", "business_card": card.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create business card: {str(e)}"}), 500
        
        
@business_card_bp.route('/<int:id>', methods=['PUT'])
def update_business_card(id):
    card = BusinessCard.query.get(id)
    if not card:
        return jsonify({"error": "Business card not found"}), 404

    try:
        # Tangani data JSON
        if request.content_type == 'application/json':
            data = request.json
            if 'name' in data:
                card.name = data['name']
            if 'active' in data:
                card.active = data['active']

        # Tangani multipart/form-data
        elif request.content_type.startswith('multipart/form-data'):
            if 'name' in request.form:
                card.name = request.form['name']
            if 'photo' in request.files:  # Jika ada file foto baru
                photo = request.files['photo']
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(UPLOAD_FOLDER, filename)
                
                # Hapus foto lama jika ada
                if card.photo and os.path.exists(os.path.join(os.getcwd(), card.photo)):
                    os.remove(os.path.join(os.getcwd(), card.photo))
                
                # Simpan foto baru
                photo.save(photo_path)
                card.photo = f"uploads/{filename}"
            if 'active' in request.form:
                card.active = request.form['active']
        else:
            return jsonify({"error": "Unsupported Content-Type"}), 415

        card.updated_at = datetime.now(jakarta_tz)
        db.session.commit()
        return jsonify({"message": "Business card updated successfully!", "business_card": card.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update business card: {str(e)}"}), 500


@business_card_bp.route('/<int:id>', methods=['DELETE'])
def delete_business_card(id):
    card = BusinessCard.query.get(id)
    if not card:
        return jsonify({"error": "Business card not found"}), 404

    try:
        # Hapus gambar jika ada
        if card.photo and os.path.exists(os.path.join(os.getcwd(), card.photo)):
            os.remove(os.path.join(os.getcwd(), card.photo))

        db.session.delete(card)
        db.session.commit()
        return jsonify({"message": "Business card deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete business card: {str(e)}"}), 500
