from flask import Blueprint, jsonify, request
from app.database import db
from app.models.soal_surat import SoalSurat

soal_surat_bp = Blueprint('soal_surat', __name__, url_prefix='/api/soal_surat')

@soal_surat_bp.route('/', methods=['GET'])
def get_all_soal_surat_entries():
    try:
        entries = SoalSurat.query.order_by(SoalSurat.id.desc()).all()
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch Soal Surat entries", "details": str(e)}), 500

@soal_surat_bp.route('/letter_number/<string:letter_number>', methods=['GET'])
def get_soal_surat_entries_by_letter_number(letter_number):
    try:
        entries = SoalSurat.query.filter_by(letter_number=letter_number).all()
        if not entries:
            return jsonify({"error": "Data tidak ditemukan..."}), 404
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Gagal untuk mengambil entri Soal Surat", "details": str(e)}), 500


@soal_surat_bp.route('/<int:id>', methods=['GET'])
def get_soal_surat_entry_by_id(id):
    try:
        entry = SoalSurat.query.get(id)
        if not entry:
            return jsonify({"error": "Soal Surat entry not found"}), 404
        return jsonify(entry.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch Soal Surat entry", "details": str(e)}), 500

@soal_surat_bp.route('/', methods=['POST'])
def create_soal_surat_entry():
    try:
        data = request.json

        required_fields = ['letter_number', 'pertanyaan', 'pilihan', 'kunci_jawaban', 'created_by', 'updated_by']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 422

        entry = SoalSurat(
            letter_number=data.get('letter_number'),
            pertanyaan=data.get('pertanyaan'),
            pilihan=data.get('pilihan'),
            kunci_jawaban=data.get('kunci_jawaban'),
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by')
        )

        db.session.add(entry)
        db.session.commit()
        return jsonify({"message": "Soal Surat entry created successfully", "entry": entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create Soal Surat entry", "details": str(e)}), 500

@soal_surat_bp.route('/<int:id>', methods=['PUT'])
def update_soal_surat_entry(id):
    try:
        data = request.json
        entry = SoalSurat.query.get(id)

        if not entry:
            return jsonify({"error": "Soal Surat entry not found"}), 404

        entry.letter_number = data.get('letter_number', entry.letter_number)
        entry.pertanyaan = data.get('pertanyaan', entry.pertanyaan)
        entry.pilihan = data.get('pilihan', entry.pilihan)
        entry.kunci_jawaban = data.get('kunci_jawaban', entry.kunci_jawaban)
        entry.updated_by = data.get('updated_by', entry.updated_by)

        db.session.commit()
        return jsonify({"message": "Soal Surat entry updated successfully", "entry": entry.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update Soal Surat entry", "details": str(e)}), 500

@soal_surat_bp.route('/<int:id>', methods=['DELETE'])
def delete_soal_surat_entry(id):
    try:
        entry = SoalSurat.query.get(id)
        if not entry:
            return jsonify({"error": "Soal Surat entry not found"}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Soal Surat entry deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete Soal Surat entry", "details": str(e)}), 500
