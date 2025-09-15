from flask import Blueprint, jsonify, request
from app.database import db
from app.models.vehicle_book import VehicleBook
from app.models.employees import Employee  # Pastikan model Employee diimpor
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Ganti blueprint name dan url_prefix
vehicle_book_mobile_bp = Blueprint('vehicle_book_mobile', __name__, url_prefix='/api/vehicle_book_mobile')

UPLOAD_FOLDER = './uploads'

# Pastikan direktori upload ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def delete_file_if_exists(filename):
    """
    Helper function to delete a file if it exists.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

@vehicle_book_mobile_bp.route('/', methods=['GET'])
def get_all_vehicle_books():
    """
    Retrieve all vehicle books ordered by descending id_vehicle_book.
    """
    try:
        vehicle_books = VehicleBook.query.order_by(VehicleBook.id_vehicle_book.desc()).all()
        return jsonify([vehicle_book.to_dict() for vehicle_book in vehicle_books]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicle books", "details": str(e)}), 500

@vehicle_book_mobile_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_vehicle_books_by_customer_id(customer_id):
    """
    Retrieve vehicle books for a specific customer by customer_id.
    """
    try:
        vehicle_books = (
            VehicleBook.query
            .join(Employee, VehicleBook.id == Employee.id)
            .filter(Employee.customer_id == customer_id)
            .order_by(VehicleBook.id_vehicle_book.desc())
            .all()
        )
        if not vehicle_books:
            return jsonify({"error": "No vehicle books found for this customer"}), 404
        return jsonify([vehicle_book.to_dict() for vehicle_book in vehicle_books]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicle books", "details": str(e)}), 500

@vehicle_book_mobile_bp.route('/<int:id_vehicle_book>', methods=['GET'])
def get_vehicle_book_by_id(id_vehicle_book):
    """
    Retrieve a specific vehicle book entry by ID.
    """
    try:
        vehicle_book = VehicleBook.query.get(id_vehicle_book)
        if not vehicle_book:
            return jsonify({"error": "Vehicle book not found"}), 404
        return jsonify(vehicle_book.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicle book", "details": str(e)}), 500

@vehicle_book_mobile_bp.route('/', methods=['POST'])
def create_vehicle_book():
    """
    Create a new vehicle book entry.
    """
    try:
        data = request.get_json()  # Changed to request.get_json to handle JSON data
        vehicle_book_date = data.get('vehicle_book_date')
        id_area = data.get('id_area')
        user_id = data.get('user_id')
        foto = data.get('foto', 'default.jpg')  # Default to 'default.jpg' if foto is not provided

        employee = Employee.query.get(user_id)
        if not employee:
            return jsonify({"error": "Employee not found"}), 404
        shift_id = employee.shift_id

        missing_fields = []
        if not id_area:
            missing_fields.append('id_area')
        if not shift_id:
            missing_fields.append('shift_id')
        if not user_id:
            missing_fields.append('user_id')
        if not foto:
            missing_fields.append('foto')

        if missing_fields:
            return jsonify({"error": "Missing required fields", "missing_fields": missing_fields}), 422

        # Save photo if it's not avatar.png
        if foto != 'avatar.png':
            filename = secure_filename(foto.filename)
            foto_path = os.path.join(UPLOAD_FOLDER, filename)
            foto.save(foto_path)
        else:
            filename = foto

        # Create a new entry
        vehicle_book = VehicleBook(
            vehicle_book_date=vehicle_book_date,
            id_area=id_area,
            shift_id=shift_id,
            id=user_id,
            foto=filename
        )
        db.session.add(vehicle_book)
        db.session.commit()

        return jsonify({"message": "Vehicle book created successfully!", "vehicle_book": vehicle_book.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create vehicle book", "details": str(e)}), 500

@vehicle_book_mobile_bp.route('/<int:id_vehicle_book>', methods=['PUT'])
def update_vehicle_book(id_vehicle_book):
    """
    Update an existing vehicle book entry.
    """
    try:
        # Mengambil data dari request.form dan request.files
        user_id = request.form.get('user_id')
        vehicle_book_date = request.form.get('vehicle_book_date')
        id_area = request.form.get('id_area')
        shift_id = request.form.get('shift_id')

        # Mengambil file foto jika ada
        photo = request.files.get('foto')

        vehicle_book = VehicleBook.query.get(id_vehicle_book)
        if not vehicle_book:
            return jsonify({"error": "Vehicle book not found"}), 404

        # Update data kendaraan
        vehicle_book.id = user_id or vehicle_book.id
        vehicle_book.vehicle_book_date = vehicle_book_date or vehicle_book.vehicle_book_date
        vehicle_book.id_area = id_area or vehicle_book.id_area
        vehicle_book.shift_id = shift_id or vehicle_book.shift_id

        # Jika ada foto yang diunggah, simpan foto tersebut
        if photo:
            # Simpan foto ke lokasi yang diinginkan
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            photo.save(photo_path)
            vehicle_book.foto = photo_filename  # Atur nama file foto di database

        db.session.commit()
        return jsonify({"message": "Vehicle book updated successfully", "vehicle_book": vehicle_book.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

        
@vehicle_book_mobile_bp.route('/<int:id_vehicle_book>', methods=['DELETE'])
def delete_vehicle_book(id_vehicle_book):
    """
    Delete a vehicle book entry.
    """
    try:
        vehicle_book = VehicleBook.query.get(id_vehicle_book)
        if not vehicle_book:
            return jsonify({"error": "Vehicle book not found"}), 404

        # Delete photo if it exists
        if vehicle_book.foto:
            delete_file_if_exists(vehicle_book.foto)

        db.session.delete(vehicle_book)
        db.session.commit()
        return jsonify({"message": "Vehicle book deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete vehicle book", "details": str(e)}), 500

@vehicle_book_mobile_bp.route('/filter', methods=['GET'])
def filter_vehicle_books():
    """
    Filter vehicle books by customer_id, start_date, and end_date.
    """
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date:
        return jsonify({"error": "start_date is required"}), 400

    try:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "start_date harus dalam format YYYY-MM-DD"}), 400

    # Validate and parse end_date if provided
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            if parsed_end_date < parsed_start_date:
                return jsonify({"error": "end_date tidak boleh sebelum start_date"}), 400
        except ValueError:
            return jsonify({"error": "end_date harus dalam format YYYY-MM-DD"}), 400
    else:
        parsed_end_date = parsed_start_date  # Default to start date if no end date provided

    # Check based on customer_id
    if customer_id:
        vehicle_books = (
            VehicleBook.query
            .join(Employee, VehicleBook.id == Employee.id)
            .filter(Employee.customer_id == customer_id)
            .filter(VehicleBook.vehicle_book_date >= parsed_start_date)
            .filter(VehicleBook.vehicle_book_date <= parsed_end_date)
            .order_by(VehicleBook.id_vehicle_book.desc())
            .all()
        )

        if vehicle_books:
            return jsonify([vehicle_book.to_dict() for vehicle_book in vehicle_books]), 200

    return jsonify({"message": "Tidak Ada Data..."}), 404


@vehicle_book_mobile_bp.route('/check', methods=['GET'])
def check_vehicle_books():
    """
    Check for the existence of vehicle books by customer_id and start_date.
    Returns all matching records.
    """
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("start_date")

    # Validasi bahwa start_date wajib ada
    if not start_date:
        return jsonify({"error": "start_date is required"}), 400

    try:
        # Parsing tanggal dari string ke objek date
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "start_date harus dalam format YYYY-MM-DD"}), 400

    # Query untuk mencari semua data berdasarkan customer_id dan start_date
    if customer_id:
        vehicle_books = (
            VehicleBook.query
            .join(Employee, VehicleBook.id == Employee.id)
            .filter(Employee.customer_id == customer_id)
            .filter(VehicleBook.vehicle_book_date == parsed_start_date)
            .order_by(VehicleBook.id_vehicle_book.desc())  # Mengurutkan berdasarkan id_vehicle_book desc
            .all()  # Mengambil semua hasil
        )

        # Jika ada data, konversi ke list of dictionaries
        if vehicle_books:
            result = [book.to_dict() for book in vehicle_books]  # Pastikan ada method to_dict() di model
            return jsonify(result), 200

    # Jika tidak ada data yang ditemukan
    return jsonify({"message": "Tidak Ada Data..."}), 404