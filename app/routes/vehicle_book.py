from flask import Blueprint, jsonify, request
from app.database import db
from app.models.vehicle_book import VehicleBook
from werkzeug.utils import secure_filename
import os
from sqlalchemy.orm import joinedload

vehicle_book_bp = Blueprint('vehicle_book', __name__, url_prefix='/api/vehicle_book')

UPLOAD_FOLDER = './uploads'

def delete_file_if_exists(filename):
    """
    Helper function to delete a file if it exists.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

@vehicle_book_bp.route('/', methods=['GET'])
def get_all_vehicle_books():
    """
    Retrieve all vehicle books ordered by descending id_vehicle_book.
    """
    try:
        vehicle_books = VehicleBook.query.order_by(VehicleBook.id_vehicle_book.desc()).all()
        return jsonify([vehicle_book.to_dict() for vehicle_book in vehicle_books]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicle books", "details": str(e)}), 500

@vehicle_book_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_vehicle_books_by_customer_id(customer_id):
       """
       Retrieve vehicle books for a specific customer by customer_id.
       """
       try:
           vehicle_books = VehicleBook.query.options(joinedload(VehicleBook.employee)).filter(Employee.customer_id == customer_id).order_by(VehicleBook.id_vehicle_book.desc()).all()
           if not vehicle_books:
               return jsonify({"error": "No vehicle books found for this customer"}), 404

           return jsonify([vehicle_book.to_dict() for vehicle_book in vehicle_books]), 200
       except Exception as e:
           return jsonify({"error": "Failed to fetch vehicle books", "details": str(e)}), 500

@vehicle_book_bp.route('/<int:id_vehicle_book>', methods=['GET'])
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


@vehicle_book_bp.route('/', methods=['POST'])
def create_vehicle_book():
    """
    Create a new vehicle book entry.
    """
    try:
        data = request.form
        vehicle_book_date = data.get('vehicle_book_date')
        id_area = data.get('id_area')
        shift_id = data.get('shift_id')
        user_id = data.get('id')
        foto = request.files.get('foto')

        if not all([id_area, shift_id, user_id, foto]):
            return jsonify({"error": "Missing required fields"}), 422

        # Save photo
        filename = secure_filename(foto.filename)
        foto_path = os.path.join(UPLOAD_FOLDER, filename)
        foto.save(foto_path)

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


@vehicle_book_bp.route('/<int:id_vehicle_book>', methods=['PUT'])
def update_vehicle_book(id_vehicle_book):
    """
    Update an existing vehicle book entry.
    """
    try:
        data = request.form
        vehicle_book = VehicleBook.query.get(id_vehicle_book)
        if not vehicle_book:
            return jsonify({"error": "Vehicle book not found"}), 404

        # Update fields if provided
        vehicle_book.vehicle_book_date = data.get('vehicle_book_date') or vehicle_book.vehicle_book_date
        vehicle_book.id_area = data.get('id_area') or vehicle_book.id_area
        vehicle_book.shift_id = data.get('shift_id') or vehicle_book.shift_id
        vehicle_book.id = data.get('id') or vehicle_book.id

        # Update photo if provided
        foto = request.files.get('foto')
        if foto:
            # Delete old photo if it exists
            if vehicle_book.foto:
                delete_file_if_exists(vehicle_book.foto)

            # Save new photo
            filename = secure_filename(foto.filename)
            foto_path = os.path.join(UPLOAD_FOLDER, filename)
            foto.save(foto_path)
            vehicle_book.foto = filename

        db.session.commit()
        return jsonify({"message": "Vehicle book updated successfully!", "vehicle_book": vehicle_book.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update vehicle book", "details": str(e)}), 500


@vehicle_book_bp.route('/<int:id_vehicle_book>', methods=['DELETE'])
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