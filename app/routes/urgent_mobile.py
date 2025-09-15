import os    
from flask import Blueprint, jsonify, request    
from app.database import db    
from app.models.urgent import Urgent    
from werkzeug.utils import secure_filename    
from datetime import datetime    
  
urgent_mobile_bp = Blueprint('urgent_mobile', __name__, url_prefix='/api/urgent_mobile')    
  
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')    
os.makedirs(UPLOAD_FOLDER, exist_ok=True)    
  
def delete_file(file_path):    
    """Helper function to delete a file if it exists."""    
    if file_path and os.path.exists(file_path):    
        os.remove(file_path)    
  
@urgent_mobile_bp.route('/', methods=['GET'])    
def get_urgents():    
    """    
    Retrieve all urgent records.    
    """    
    try:    
        urgents = Urgent.query.order_by(Urgent.id_urgent.desc()).all()    
        return jsonify([urgent.to_dict() for urgent in urgents]), 200    
    except Exception as e:    
        return jsonify({"error": "Failed to fetch urgent records", "details": str(e)}), 500    
  
@urgent_mobile_bp.route('/<int:id_urgent>', methods=['GET'])    
def get_urgent_by_id(id_urgent):    
    """    
    Retrieve a specific urgent record by ID.    
    """    
    try:    
        urgent = Urgent.query.get(id_urgent)    
        if not urgent:    
            return jsonify({"error": "Urgent record not found"}), 404    
  
        return jsonify(urgent.to_dict()), 200    
    except Exception as e:    
        return jsonify({"error": "Failed to fetch urgent record", "details": str(e)}), 500    

def get_sorted_data(building_id, tanggal_awal=None, tanggal_akhir=None, sort_order='asc'):
    """
    Helper function untuk query data dengan filter dan sorting.
    """
    query = Urgent.query.filter(Urgent.building_id == building_id)

    if tanggal_awal:
        query = query.filter(Urgent.urgent_date >= tanggal_awal)
    if tanggal_akhir:
        query = query.filter(Urgent.urgent_date <= tanggal_akhir)

    if sort_order == 'asc':
        query = query.order_by(Urgent.urgent_date.asc())
    elif sort_order == 'desc':
        query = query.order_by(Urgent.urgent_date.desc())
    else:
        raise ValueError("Invalid sort_order. Use 'asc' or 'desc'")

    return query.all()

def get_sorted_data_now(building_id, tanggal_awal=None, sort_order='asc'):
    """
    Helper function untuk query data dengan filter dan sorting.
    """
    query = Urgent.query.filter(Urgent.building_id == building_id)

    if tanggal_awal:
        query = query.filter(Urgent.urgent_date >= tanggal_awal)
        
    if sort_order == 'asc':
        query = query.order_by(Urgent.urgent_date.asc())
    elif sort_order == 'desc':
        query = query.order_by(Urgent.urgent_date.desc())
    else:
        raise ValueError("Invalid sort_order. Use 'asc' or 'desc'")

    return query.all()

@urgent_mobile_bp.route('/filter_customer', methods=['GET'])
def filter_customer_by_date_range():
    """
    Filter urgent data by building_id and date range (tanggal_awal to tanggal_akhir).
    """
    try:
        building_id = request.args.get('building_id')
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')

        # Validasi parameter
        if not building_id or not tanggal_awal or not tanggal_akhir:
            return jsonify({"error": "building_id, tanggal_awal, and tanggal_akhir are required"}), 400

        try:
            tanggal_awal = datetime.strptime(tanggal_awal, "%Y-%m-%d")
            tanggal_akhir = datetime.strptime(tanggal_akhir, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Query data
        data = get_sorted_data(building_id=int(building_id), tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir)
        return jsonify([record.to_dict() for record in data]), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to filter data", "details": str(e)}), 500


@urgent_mobile_bp.route('/filter_tanggal', methods=['GET'])
def filter_customer_by_start_date():
    """
    Filter urgent data by building_id and start date (tanggal_awal).
    """
    try:
        building_id = request.args.get('building_id')
        tanggal_awal = request.args.get('tanggal_awal')

        # Validasi parameter
        if not building_id or not tanggal_awal:
            return jsonify({"error": "building_id and tanggal_awal are required"}), 400

        try:
            tanggal_awal = datetime.strptime(tanggal_awal, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Query data
        data = get_sorted_data_now(building_id=int(building_id), tanggal_awal=tanggal_awal)
        return jsonify([record.to_dict() for record in data]), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to filter data", "details": str(e)}), 500



@urgent_mobile_bp.route('/', methods=['POST'])        
def create_urgent():        
    """        
    Create a new urgent record.        
    """        
    try:        
        # Ambil data dari request.form untuk FormData    
        urgent_photo = request.files.get("urgent_photo")  # Ambil file dari request.files  
  
        # Simpan file jika ada  
        if urgent_photo:  
            filename = secure_filename(urgent_photo.filename)  
            file_path = os.path.join(UPLOAD_FOLDER, filename)  
            urgent_photo.save(file_path)  # Simpan file ke server  
  
        urgent = Urgent(        
            id=request.form.get("id"),        
            checkpoint_id=request.form.get("checkpoint_id"),        
            urgent_date=request.form.get("urgent_date"),        
            urgent_result_user=request.form.get("urgent_result_user"),        
            urgent_photo=filename,  # Simpan nama file  
            status=request.form.get("status"),        
            building_id=request.form.get("building_id"),        
        )        
        db.session.add(urgent)        
        db.session.commit()        
        return jsonify({"message": "Urgent record created successfully!", "urgent": urgent.to_dict()}), 201        
    except Exception as e:        
        db.session.rollback()        
        return jsonify({"error": "Failed to create urgent record", "details": str(e)}), 500      

@urgent_mobile_bp.route('/<int:id_urgent>', methods=['PUT'])    
def update_urgent(id_urgent):    
    """    
    Update an existing urgent record.    
    """    
    try:    
        data = request.json    
        urgent = Urgent.query.get(id_urgent)    
        if not urgent:    
            return jsonify({"error": "Urgent record not found"}), 404    
  
        # Update allowed fields only    
        urgent.checkpoint_id = data.get("checkpoint_id", urgent.checkpoint_id)    
        urgent.urgent_date = data.get("urgent_date", urgent.urgent_date)    
        urgent.urgent_date_process = data.get("urgent_date_process", urgent.urgent_date_process)    
        urgent.urgent_date_end = data.get("urgent_date_end", urgent.urgent_date_end)    
        urgent.urgent_result_user = data.get("urgent_result_user", urgent.urgent_result_user) 
        urgent.urgent_result_user_end = data.get("urgent_result_user", urgent.urgent_result_user_end)
        urgent.urgent_result_admin = data.get("urgent_result_admin", urgent.urgent_result_admin)    
        urgent.urgent_photo = data.get("urgent_photo", urgent.urgent_photo)    
        urgent.status = data.get("status", urgent.status)    
        urgent.id_admin = data.get("id_admin", urgent.id_admin)    
        urgent.id_user_terima = data.get("id_user_terima", urgent.id_user_terima)    
        urgent.id_user_selesai = data.get("id_user_selesai", urgent.id_user_selesai)    
        urgent.building_id = data.get("building_id", urgent.building_id)    
  
        db.session.commit()    
        return jsonify({"message": "Urgent record updated successfully!", "urgent": urgent.to_dict()}), 200    
    except Exception as e:    
        db.session.rollback()    
        return jsonify({"error": "Failed to update urgent record", "details": str(e)}), 500    
  
@urgent_mobile_bp.route('/<int:id_urgent>', methods=['DELETE'])    
def delete_urgent(id_urgent):    
    """    
    Delete an urgent record by ID.    
    """    
    try:    
        urgent = Urgent.query.get(id_urgent)    
        if not urgent:    
            return jsonify({"error": "Urgent record not found"}), 404    
  
        db.session.delete(urgent)    
        db.session.commit()    
        return jsonify({"message": "Urgent record deleted successfully!"}), 200    
    except Exception as e:    
        db.session.rollback()    
        return jsonify({"error": "Failed to delete urgent record", "details": str(e)}), 500    
