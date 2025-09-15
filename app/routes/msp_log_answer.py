import json
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.msp_log_answer import MSPLogAnswer
from app.models.employees import Employee
from app.models.position import Position

msp_log_answer_bp = Blueprint('msp_log_answer', __name__, url_prefix='/api/msp_log_answer')

@msp_log_answer_bp.route('/detailed/<int:msp_id_table>', methods=['GET'])
def get_detailed_msp_log_answers(msp_id_table):
    try:
        entries = (
            MSPLogAnswer.query
            .join(Employee, MSPLogAnswer.employees_id == Employee.id)
            .join(Position, Employee.position_id == Position.position_id)
            .filter(MSPLogAnswer.msp_id_table == msp_id_table)  # Filter by msp_id_table
            .all()
        )

        results = []
        
        for entry in entries:
            # Parse JSON strings into dictionaries
            answer_real_dict = json.loads(entry.answer_real)
            answer_user_dict = json.loads(entry.answer_user)

            # Calculate score (number of correct answers / total questions)
            correct_answers_count = sum(1 for key in answer_real_dict if answer_real_dict[key] == answer_user_dict.get(key))
            
            total_questions_count = len(answer_real_dict)  # Assuming all keys represent questions
            
            score_string = f"{correct_answers_count}/{total_questions_count}" if total_questions_count > 0 else "0/0"

            results.append({
                "id": entry.id,
                "created_at": entry.created_at.isoformat(),
                "employees_name": entry.employee.employees_name,  # Assuming Employee model has a 'name' attribute
                "position_name": entry.employee.position.position_name,  # Assuming Position model has a 'name' attribute
                "score": score_string
             })

        return jsonify(results), 200
    
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log jawaban dengan detail", "details": str(e)}), 500

@msp_log_answer_bp.route('/msp_table/<int:msp_id_table>', methods=['GET'])
def get_msp_log_answers_by_msp_id_table(msp_id_table):
    try:
        entries = MSPLogAnswer.query.filter_by(msp_id_table=msp_id_table).order_by(MSPLogAnswer.id.desc()).all()
        if not entries:
            return jsonify({"message": "Data tidak ditemukan..."}), 404
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log jawaban", "details": str(e)}), 500


@msp_log_answer_bp.route('/msp_table/<int:msp_id_table>/employees/<int:employees_id>', methods=['GET'])
def get_msp_log_answers_by_msp_id_table_and_employees_id(msp_id_table, employees_id):
    try:
        entries = MSPLogAnswer.query.filter_by(msp_id_table=msp_id_table, employees_id=employees_id).order_by(MSPLogAnswer.id.desc()).all()
        if not entries:
            return jsonify({"message": "Data tidak ditemukan..."}), 404
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log jawaban", "details": str(e)}), 500

@msp_log_answer_bp.route('/msp_table/<int:msp_id_table>/employees/<int:employees_id>/asc', methods=['GET'])
def get_msp_log_answers_by_msp_id_table_and_employees_id_asc(msp_id_table, employees_id):
    try:
        entries = MSPLogAnswer.query.filter_by(msp_id_table=msp_id_table, employees_id=employees_id).order_by(MSPLogAnswer.id.asc()).all()
        if not entries:
            return jsonify({"message": "Data tidak ditemukan..."}), 404
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log jawaban", "details": str(e)}), 500

@msp_log_answer_bp.route('/', methods=['GET'])
def get_all_msp_log_answers():
    try:
        entries = MSPLogAnswer.query.order_by(MSPLogAnswer.id.desc()).all()
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log jawaban", "details": str(e)}), 500


@msp_log_answer_bp.route('/<int:id>', methods=['GET'])
def get_msp_log_answer_by_id(id):
    try:
        entry = MSPLogAnswer.query.get(id)
        if not entry:
            return jsonify({"error": "Entri log jawaban tidak ditemukan"}), 404
        return jsonify(entry.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Gagal mengambil entri log jawaban", "details": str(e)}), 500


@msp_log_answer_bp.route('/', methods=['POST'])
def create_msp_log_answer():
    try:
        data = request.json

        # Cek field yang diperlukan
        required_fields = ['msp_id_table', 'msp_id_surat', 'answer_real', 'answer_user', 'employees_id']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Field yang diperlukan hilang"}), 422

        # Pastikan answer_real dan answer_user adalah dictionary
        if not isinstance(data.get('answer_real'), dict) or not isinstance(data.get('answer_user'), dict):
            return jsonify({"error": "answer_real dan answer_user harus berupa JSON"}), 422

        # Pastikan employees_id adalah integer
        if not isinstance(data.get('employees_id'), int):
            return jsonify({"error": "employees_id harus berupa integer"}), 422

        # Konversi dictionary ke string JSON
        answer_real_json = json.dumps(data.get('answer_real'))
        answer_user_json = json.dumps(data.get('answer_user'))

        # Buat entri baru
        entry = MSPLogAnswer(
            msp_id_table=data.get('msp_id_table'),
            msp_id_surat=data.get('msp_id_surat'),
            answer_real=answer_real_json,
            answer_user=answer_user_json,
            employees_id=data.get('employees_id')  # Tambahkan employees_id
        )

        # Tambahkan dan komit entri ke database
        db.session.add(entry)
        db.session.commit()
        return jsonify({"message": "Entri log jawaban berhasil dibuat", "entry": entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Gagal membuat entri log jawaban", "details": str(e)}), 500

@msp_log_answer_bp.route('/<int:id>', methods=['PUT'])
def update_msp_log_answer(id):
    try:
        data = request.json
        entry = MSPLogAnswer.query.get(id)

        if not entry:
            return jsonify({"error": "Entri log jawaban tidak ditemukan"}), 404

        # Validasi jika ada pembaruan pada answer_real atau answer_user
        if 'answer_real' in data:
            if not isinstance(data.get('answer_real'), dict):
                return jsonify({"error": "answer_real harus berupa JSON"}), 422
            entry.answer_real = json.dumps(data.get('answer_real'))

        if 'answer_user' in data:
            if not isinstance(data.get('answer_user'), dict):
                return jsonify({"error": "answer_user harus berupa JSON"}), 422
            entry.answer_user = json.dumps(data.get('answer_user'))

        # Update kolom lain jika ada
        entry.msp_id_table = data.get('msp_id_table', entry.msp_id_table)
        entry.msp_id_surat = data.get('msp_id_surat', entry.msp_id_surat)

        # Periksa apakah employees_id ada di permintaan
        if 'employees_id' in data:
            if not isinstance(data.get('employees_id'), int):
                return jsonify({"error": "employees_id harus berupa integer"}), 422
            entry.employees_id = data.get('employees_id')

        # Komit perubahan ke database
        db.session.commit()
        return jsonify({"message": "Entri log jawaban berhasil diperbarui", "entry": entry.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Gagal memperbarui entri log jawaban", "details": str(e)}), 500


@msp_log_answer_bp.route('/<int:id>', methods=['DELETE'])
def delete_msp_log_answer(id):
    try:
        entry = MSPLogAnswer.query.get(id)
        if not entry:
            return jsonify({"error": "Entri log jawaban tidak ditemukan"}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Entri log jawaban berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Gagal menghapus entri log jawaban", "details": str(e)}), 500