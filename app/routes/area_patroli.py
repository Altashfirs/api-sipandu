from flask import Blueprint, jsonify, request
from app.database import db
from app.models.area_patroli import AreaPatroli

area_patroli_bp = Blueprint('area_patroli', __name__, url_prefix='/api/area-patroli')

@area_patroli_bp.route('/', methods=['GET'])
def get_area_patroli():
    """
    Retrieve all area patroli ordered by descending id_area_patroli.
    """
    try:
        areas = AreaPatroli.query.order_by(AreaPatroli.id_area_patroli.desc()).all()
        return jsonify([area.to_dict() for area in areas]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch area patroli", "details": str(e)}), 500
@area_patroli_bp.route('/<int:id>', methods=['GET'])
def get_area_patroli_by_id(id):
    """
    Retrieve an area patroli by id_area_patroli.
    """
    try:
        area = AreaPatroli.query.filter_by(id_area_patroli=id).first()

        if not area:
            return jsonify({"error": "Area Patroli not found"}), 404

        return jsonify(area.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch area patroli", "details": str(e)}), 500

@area_patroli_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_area_patroli_by_customer_id(customer_id):
    """
    Retrieve an area patroli by customer_id.
    """
    try:
        area = AreaPatroli.query.filter_by(customer_id=customer_id).first()

        if not area:
            return jsonify({"error": "Area Patroli not found"}), 404

        return jsonify(area.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch area patroli", "details": str(e)}), 500



@area_patroli_bp.route('/', methods=['POST'])
def create_area_patroli():
    """
    Create a new area patroli.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validasi input
        desc_area_patroli = data.get("desc_area_patroli")
        customer_id = data.get("customer_id")
        if not desc_area_patroli or not customer_id:
            return jsonify({"error": "Missing required fields", "fields": ["desc_area_patroli", "customer_id"]}), 422

        area = AreaPatroli(
            desc_area_patroli=desc_area_patroli,
            customer_id=customer_id,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
        db.session.add(area)
        db.session.commit()
        return jsonify({"message": "Area Patroli created successfully!", "area": area.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create area patroli", "details": str(e)}), 500

@area_patroli_bp.route('/<int:id_area_patroli>', methods=['PUT'])
def update_area_patroli(id_area_patroli):
    """
    Update an existing area patroli.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        area = AreaPatroli.query.get(id_area_patroli)
        if not area:
            return jsonify({"error": "Area Patroli not found"}), 404

        for key, value in data.items():
            setattr(area, key, value)

        db.session.commit()
        return jsonify({"message": "Area Patroli updated successfully!", "area": area.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update area patroli", "details": str(e)}), 500

@area_patroli_bp.route('/<int:id_area_patroli>', methods=['DELETE'])
def delete_area_patroli(id_area_patroli):
    """
    Delete an area patroli by ID.
    """
    try:
        area = AreaPatroli.query.get(id_area_patroli)
        if not area:
            return jsonify({"error": "Area Patroli not found"}), 404

        db.session.delete(area)
        db.session.commit()
        return jsonify({"message": "Area Patroli deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete area patroli", "details": str(e)}), 500
