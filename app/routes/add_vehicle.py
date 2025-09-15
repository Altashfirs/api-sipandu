from flask import Blueprint, jsonify, request
from app.database import db
from app.models.add_vehicle import AddVehicle
from werkzeug.utils import secure_filename
import os

add_vehicle_bp = Blueprint('add_vehicle', __name__, url_prefix='/api/add_vehicle')

UPLOAD_FOLDER = './uploads'

def delete_file_if_exists(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

@add_vehicle_bp.route('/', methods=['GET'])
def get_all_add_vehicles():
    try:
        vehicles = AddVehicle.query.order_by(AddVehicle.id_add_vehicle.desc()).all()
        return jsonify([vehicle.to_dict() for vehicle in vehicles]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicles", "details": str(e)}), 500

@add_vehicle_bp.route('/<int:id_add_vehicle>', methods=['GET'])
def get_add_vehicle_by_id(id_add_vehicle):
    try:
        vehicle = AddVehicle.query.get(id_add_vehicle)
        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404
        return jsonify(vehicle.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicle", "details": str(e)}), 500

@add_vehicle_bp.route('/area/<int:id_area>', methods=['GET'])
def get_add_vehicle_by_area(id_area):
    try:
        vehicles = AddVehicle.query.filter_by(id_area=id_area).order_by(AddVehicle.id_add_vehicle.desc()).all()
        return jsonify([vehicle.to_dict() for vehicle in vehicles]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch vehicles for the area", "details": str(e)}), 500

@add_vehicle_bp.route('/', methods=['POST'])
def create_add_vehicle():
    try:
        data = request.form
        id_area = data.get('id_area')
        id_vehicle_book = data.get('id_vehicle_book')
        model_type = data.get('model_type')
        nopol = data.get('nopol')
        wheel = data.get('wheel')
        spy = data.get('spy')
        tire = data.get('tire')
        condition_vehicle = data.get('condition_vehicle')
        glass_door = data.get('glass_door')
        information = data.get('information')
        photo = request.files.get('photo_add_vehicle')

        if not all([id_area, id_vehicle_book, model_type, nopol, wheel, spy, tire, condition_vehicle, glass_door]):
            return jsonify({"error": "Missing required fields"}), 422

        photo_filename = None
        if photo:
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            photo.save(photo_path)

        vehicle = AddVehicle(
            id_area=id_area,
            id_vehicle_book=id_vehicle_book,
            model_type=model_type,
            nopol=nopol,
            wheel=wheel,
            spy=spy,
            tire=tire,
            condition_vehicle=condition_vehicle,
            glass_door=glass_door,
            information=information,
            photo_add_vehicle=photo_filename
        )
        db.session.add(vehicle)
        db.session.commit()
        return jsonify({"message": "Vehicle added successfully!", "vehicle": vehicle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add vehicle", "details": str(e)}), 500

@add_vehicle_bp.route('/<int:id_add_vehicle>', methods=['PUT'])
def update_add_vehicle(id_add_vehicle):
    try:
        data = request.form
        vehicle = AddVehicle.query.get(id_add_vehicle)
        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        vehicle.id_area = data.get('id_area') or vehicle.id_area
        vehicle.id_vehicle_book = data.get('id_vehicle_book') or vehicle.id_vehicle_book
        vehicle.model_type = data.get('model_type') or vehicle.model_type
        vehicle.nopol = data.get('nopol') or vehicle.nopol
        vehicle.wheel = data.get('wheel') or vehicle.wheel
        vehicle.spy = data.get('spy') or vehicle.spy
        vehicle.tire = data.get('tire') or vehicle.tire
        vehicle.condition_vehicle = data.get('condition_vehicle') or vehicle.condition_vehicle
        vehicle.glass_door = data.get('glass_door') or vehicle.glass_door
        vehicle.information = data.get('information') or vehicle.information

        photo = request.files.get('photo_add_vehicle')
        if photo:
            if vehicle.photo_add_vehicle:
                delete_file_if_exists(vehicle.photo_add_vehicle)
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            photo.save(photo_path)
            vehicle.photo_add_vehicle = photo_filename

        db.session.commit()
        return jsonify({"message": "Vehicle updated successfully!", "vehicle": vehicle.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update vehicle", "details": str(e)}), 500

@add_vehicle_bp.route('/<int:id_add_vehicle>', methods=['DELETE'])
def delete_add_vehicle(id_add_vehicle):
    try:
        vehicle = AddVehicle.query.get(id_add_vehicle)
        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        if vehicle.photo_add_vehicle:
            delete_file_if_exists(vehicle.photo_add_vehicle)

        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({"message": "Vehicle deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete vehicle", "details": str(e)}), 500