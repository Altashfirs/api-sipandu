from flask import Blueprint, jsonify, request
from app.database import db
from app.models.msp_table import MSPTable
from app.models.topic import Topic
import os
from werkzeug.utils import secure_filename

msp_table_bp = Blueprint('msp_table', __name__, url_prefix='/api/msp_table')

# Define the upload folder and create it if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def delete_file(file_path):
    """Helper function to delete a file if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

@msp_table_bp.route('/', methods=['GET'])
def get_all_msp_entries():
    try:
        # Retrieve the 'kategori' query parameter
        kategori = request.args.get('kategori')
        
        # Define the allowed categories
        allowed_categories = ['Reguler', 'Head Office', 'Customer']
        
        # Check if 'kategori' is one of the allowed categories
        if kategori and kategori in allowed_categories:
            entries = MSPTable.query.filter_by(kategori=kategori).order_by(MSPTable.msp_id_table.desc()).all()
        else:
            # If no 'kategori' is specified or it's not in the allowed list, retrieve all entries
            entries = MSPTable.query.order_by(MSPTable.msp_id_table.desc()).all()
        
        # Convert entries to a list of dictionaries and return
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP entries", "details": str(e)}), 500

@msp_table_bp.route('/<int:msp_id_table>', methods=['GET'])
def get_msp_entry_by_id(msp_id_table):
    try:
        entry = MSPTable.query.get(msp_id_table)
        if not entry:
            return jsonify({"error": "MSP entry not found"}), 404
        return jsonify(entry.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP entry", "details": str(e)}), 500

# Endpoint untuk mobile: Get semua data dengan topic_name
@msp_table_bp.route('/mobile', methods=['GET'])
def get_all_msp_entries_mobile():
    try:
        # Join MSPTable dengan Topic untuk ambil topic_name
        entries = db.session.query(MSPTable, Topic.topic_name).join(
            Topic, MSPTable.topic_id == Topic.id_topic
        ).order_by(MSPTable.msp_id_table.desc()).all()

        # Format hasilnya
        result = [{
            "msp_id_table": entry.MSPTable.msp_id_table,
            "letter_number": entry.MSPTable.letter_number,
            "topic_id": entry.MSPTable.topic_id,
            "topic_name": entry.topic_name,  # Langsung dari join
            "building_id": entry.MSPTable.building_id,
            "khusus_building": entry.MSPTable.khusus_building,
            "khusus_pic": entry.MSPTable.khusus_pic,
            "tampil_building": entry.MSPTable.tampil_building,
            "tampil_pic": entry.MSPTable.tampil_pic,
            "kategori": entry.MSPTable.kategori,
            "implementation": entry.MSPTable.implementation,
            "msp_date": str(entry.MSPTable.msp_date),
            "msp_status": entry.MSPTable.msp_status,
            "daily": entry.MSPTable.daily,
            "weekly": entry.MSPTable.weekly,
            "msp_sr": entry.MSPTable.msp_sr,
            "msp_surat": entry.MSPTable.msp_surat,
            "id_admin": entry.MSPTable.id_admin
        } for entry in entries]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP entries for mobile", "details": str(e)}), 500

# Endpoint untuk mobile: Get data berdasarkan ID dengan topic_name
@msp_table_bp.route('/mobile/<int:msp_id_table>', methods=['GET'])
def get_msp_entry_by_id_mobile(msp_id_table):
    try:
        # Join MSPTable dengan Topic untuk ambil topic_name
        entry = db.session.query(MSPTable, Topic.topic_name).join(
            Topic, MSPTable.topic_id == Topic.id_topic
        ).filter(MSPTable.msp_id_table == msp_id_table).first()

        if not entry:
            return jsonify({"error": "MSP entry not found"}), 404

        # Format hasilnya
        result = {
            "msp_id_table": entry.MSPTable.msp_id_table,
            "letter_number": entry.MSPTable.letter_number,
            "topic_id": entry.MSPTable.topic_id,
            "topic_name": entry.topic_name,  # Langsung dari join
            "building_id": entry.MSPTable.building_id,
            "khusus_building": entry.MSPTable.khusus_building,
            "khusus_pic": entry.MSPTable.khusus_pic,
            "tampil_building": entry.MSPTable.tampil_building,
            "tampil_pic": entry.MSPTable.tampil_pic,
            "kategori": entry.MSPTable.kategori,
            "implementation": entry.MSPTable.implementation,
            "msp_date": str(entry.MSPTable.msp_date),
            "msp_status": entry.MSPTable.msp_status,
            "daily": entry.MSPTable.daily,
            "weekly": entry.MSPTable.weekly,
            "msp_sr": entry.MSPTable.msp_sr,
            "msp_surat": entry.MSPTable.msp_surat,
            "id_admin": entry.MSPTable.id_admin
        }

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch MSP entry for mobile", "details": str(e)}), 500

@msp_table_bp.route('/', methods=['POST'])
def create_msp_entry():
    try:
        # Access form data
        data = request.form

        # Check for required fields
        required_fields = ['letter_number', 'topic_id', 'msp_date', 'id_admin']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 422

        # Handle file upload if present
        msp_surat_file = request.files.get('msp_surat')
        msp_surat_path = None
        if msp_surat_file:
            # Secure the filename
            secure_name = secure_filename(msp_surat_file.filename)
            # Define the new file path
            new_file_path = os.path.join(UPLOAD_FOLDER, secure_name)
            # Save the file to the uploads directory
            msp_surat_file.save(new_file_path)
            # Store the file path in the database
            msp_surat_path = f'uploads/{secure_name}'

        # Create a new MSPTable entry
        entry = MSPTable(
            letter_number=data.get('letter_number'),
            topic_id=data.get('topic_id'),
            building_id=data.get('building_id'),
            khusus_building=data.get('khusus_building'),
            khusus_pic=data.get('khusus_pic'),
            tampil_building=data.get('tampil_building'),
            tampil_pic=data.get('tampil_pic'),
            kategori=data.get('kategori'),
            implementation=data.get('implementation'),
            msp_date=data.get('msp_date'),
            msp_status=data.get('msp_status'),
            daily=data.get('daily'),
            weekly=data.get('weekly'),
            msp_sr=data.get('msp_sr'),
            msp_surat=msp_surat_path,
            id_admin=data.get('id_admin')
        )

        # Add and commit the entry to the database
        db.session.add(entry)
        db.session.commit()
        return jsonify({"message": "MSP entry created successfully", "entry": entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create MSP entry", "details": str(e)}), 500

@msp_table_bp.route('/<int:msp_id_table>', methods=['PUT'])
def update_msp_entry(msp_id_table):
    try:
        # Access form data
        data = request.form

        # Retrieve the entry from the database
        entry = MSPTable.query.get(msp_id_table)

        if not entry:
            return jsonify({"error": "MSP entry not found"}), 404

        # Update the entry with form data
        entry.letter_number = data.get('letter_number', entry.letter_number)
        entry.topic_id = data.get('topic_id', entry.topic_id)
        entry.building_id = data.get('building_id', entry.building_id)
        entry.khusus_building = data.get('khusus_building', entry.khusus_building)
        entry.khusus_pic = data.get('khusus_pic', entry.khusus_pic)
        entry.tampil_building = data.get('tampil_building', entry.tampil_building)
        entry.tampil_pic = data.get('tampil_pic', entry.tampil_pic)
        entry.kategori = data.get('kategori', entry.kategori)
        entry.implementation = data.get('implementation', entry.implementation)
        entry.msp_date = data.get('msp_date', entry.msp_date)
        entry.msp_status = data.get('msp_status', entry.msp_status)
        entry.daily = data.get('daily', entry.daily)
        entry.weekly = data.get('weekly', entry.weekly)
        entry.msp_sr = data.get('msp_sr', entry.msp_sr)

        # Handle file upload if present
        msp_surat_file = request.files.get('msp_surat')
        if msp_surat_file:
            # Secure the filename
            secure_name = secure_filename(msp_surat_file.filename)
            # Define the new file path
            new_file_path = os.path.join(UPLOAD_FOLDER, secure_name)
            # Save the file to the uploads directory
            msp_surat_file.save(new_file_path)
            # Store the file path in the database
            entry.msp_surat = f'uploads/{secure_name}'

            # Delete the old file if it exists
            old_file_path = os.path.join(os.getcwd(), entry.msp_surat) if entry.msp_surat else None
            delete_file(old_file_path)

        # Commit the changes to the database
        db.session.commit()
        return jsonify({"message": "MSP entry updated successfully", "entry": entry.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update MSP entry", "details": str(e)}), 500

@msp_table_bp.route('/<int:msp_id_table>', methods=['DELETE'])
def delete_msp_entry(msp_id_table):
    try:
        entry = MSPTable.query.get(msp_id_table)
        if not entry:
            return jsonify({"error": "MSP entry not found"}), 404

        # Delete the associated file if it exists
        file_path = os.path.join(os.getcwd(), entry.msp_surat) if entry.msp_surat else None
        delete_file(file_path)

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "MSP entry deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete MSP entry", "details": str(e)}), 500
