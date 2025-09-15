from flask import Blueprint, jsonify, request
from app.database import db
from app.models.template_rekap import TemplateRekap
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)

template_rekap_bp = Blueprint('template_rekap', __name__, url_prefix='/api/template-rekap')

@template_rekap_bp.route('/', methods=['POST'])
def create_template_rekap():
    """
    Create a new template_rekap record.
    """
    try:
        data = request.get_json()
        required_fields = ['section_template']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required field: section_template"}), 400

        new_template = TemplateRekap(
            section_template=data['section_template'],
            content=data.get('content'),
            image=data.get('image')
        )
        db.session.add(new_template)
        db.session.commit()

        return jsonify({
            "message": "Template rekap record created successfully!",
            "data": new_template.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating template rekap: {traceback.format_exc()}")
        return jsonify({"error": "Failed to create template rekap record", "message": str(e)}), 500

@template_rekap_bp.route('/', methods=['GET'])
def get_all_template_rekap():
    """
    Retrieve all template_rekap records.
    """
    try:
        templates = TemplateRekap.query.order_by(TemplateRekap.created_at.desc()).all()
        return jsonify([template.to_dict() for template in templates]), 200

    except Exception as e:
        logging.error(f"Error retrieving template rekap records: {traceback.format_exc()}")
        return jsonify({"error": "Failed to retrieve template rekap records", "message": str(e)}), 500

@template_rekap_bp.route('/<int:id>', methods=['GET'])
def get_template_rekap_by_id(id):
    """
    Retrieve a single template_rekap record by id_template.
    """
    try:
        template = TemplateRekap.query.get(id)
        if not template:
            return jsonify({"error": "Template rekap record not found"}), 404

        return jsonify(template.to_dict()), 200

    except Exception as e:
        logging.error(f"Error retrieving template rekap record: {traceback.format_exc()}")
        return jsonify({"error": "Failed to retrieve template rekap record", "message": str(e)}), 500

@template_rekap_bp.route('/<int:id>', methods=['PUT'])
def update_template_rekap(id):
    """
    Update an existing template_rekap record.
    """
    try:
        template = TemplateRekap.query.get(id)
        if not template:
            return jsonify({"error": "Template rekap record not found"}), 404

        data = request.get_json()

        if 'section_template' in data:
            template.section_template = data['section_template']
        if 'content' in data:
            template.content = data.get('content')  # Allow null content
        if 'image' in data:
            template.image = data.get('image')  # Allow null image

        db.session.commit()

        return jsonify({
            "message": "Template rekap record updated successfully!",
            "data": template.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating template rekap record: {traceback.format_exc()}")
        return jsonify({"error": "Failed to update template rekap record", "message": str(e)}), 500

@template_rekap_bp.route('/<int:id>', methods=['DELETE'])
def delete_template_rekap(id):
    """
    Delete a template_rekap record.
    """
    try:
        template = TemplateRekap.query.get(id)
        if not template:
            return jsonify({"error": "Template rekap record not found"}), 404

        db.session.delete(template)
        db.session.commit()

        return jsonify({"message": "Template rekap record deleted successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting template rekap record: {traceback.format_exc()}")
        return jsonify({"error": "Failed to delete template rekap record", "message": str(e)}), 500