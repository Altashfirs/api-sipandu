from flask import Blueprint, jsonify, request
from app.database import db
from app.models.area import Area

area_bp = Blueprint('area', __name__, url_prefix='/api/areas')

@area_bp.route('/', methods=['GET'])
def get_areas():
    """
    Retrieve all areas.
    """
    try:
        areas = Area.query.order_by(Area.id_area.desc()).all()
        return jsonify([area.to_dict() for area in areas]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch areas", "details": str(e)}), 500
        
@area_bp.route('/building/<int:building_id>', methods=['GET'])
def get_areas_by_building(building_id):
    """
    Retrieve areas by building ID.
    """
    try:
        areas = Area.query.filter_by(building_id=building_id).order_by(Area.id_area.desc()).all()
        return jsonify([area.to_dict() for area in areas]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch areas", "details": str(e)}), 500
        
@area_bp.route('/<int:id_area>', methods=['GET'])
def get_area_by_id(id_area):
    """
    Retrieve a specific area by ID.
    """
    try:
        area = Area.query.get(id_area)
        if not area:
            return jsonify({"error": "Area not found"}), 404

        return jsonify(area.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch area", "details": str(e)}), 500

@area_bp.route('/', methods=['POST'])
def create_area():
    """
    Create a new area.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate input
        area_name = data.get("area_name")
        building_id = data.get("building_id")
        if not area_name or not building_id:
            return jsonify({"error": "Missing required fields", "fields": ["area_name", "building_id"]}), 422

        area = Area(
            area_name=area_name,
            building_id=building_id
        )
        db.session.add(area)
        db.session.commit()
        return jsonify({"message": "Area created successfully!", "area": area.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create area", "details": str(e)}), 500

@area_bp.route('/<int:id_area>', methods=['PUT'])
def update_area(id_area):
    """
    Update an existing area.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        area = Area.query.get(id_area)
        if not area:
            return jsonify({"error": "Area not found"}), 404

        area_name = data.get("area_name")
        building_id = data.get("building_id")
        if area_name:
            area.area_name = area_name
        if building_id:
            area.building_id = building_id

        db.session.commit()
        return jsonify({"message": "Area updated successfully!", "area": area.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update area", "details": str(e)}), 500

@area_bp.route('/<int:id_area>', methods=['DELETE'])
def delete_area(id_area):
    """
    Delete an area by ID.
    """
    try:
        area = Area.query.get(id_area)
        if not area:
            return jsonify({"error": "Area not found"}), 404

        db.session.delete(area)
        db.session.commit()
        return jsonify({"message": "Area deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete area", "details": str(e)}), 500
