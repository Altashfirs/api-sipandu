from flask import Blueprint, jsonify, request
from app.database import db
from app.models.shift import Shift
from app.models.employees import Employee

shift_bp = Blueprint('shift', __name__, url_prefix='/api/shifts')

@shift_bp.route('/', methods=['GET'])
def get_shifts():
    shifts = Shift.query.all()
    return jsonify([shift.to_dict() for shift in shifts])

@shift_bp.route('/total', methods=['GET'])
def get_shifts_total():
    shifts = Shift.query.all()
    shift_list = []

    for shift in shifts:
        # Count the number of employees for the current shift
        total_employees = Employee.query.filter_by(shift_id=shift.shift_id).count()
        
        # Create a dictionary for the shift including the total_employees count
        shift_dict = shift.to_dict()
        shift_dict['total_employees'] = total_employees
        
        # Append the dictionary to the list
        shift_list.append(shift_dict)

    return jsonify(shift_list)
    
@shift_bp.route('/<int:shift_id>', methods=['GET'])
def get_shift_by_id(shift_id):
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({"error": "Shift not found"}), 404
    return jsonify(shift.to_dict())

@shift_bp.route('/', methods=['POST'])
def create_shift():
    data = request.json
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        shift = Shift(
            shift_name=data.get("shift_name"),
            time_in=data.get("time_in"),
            time_out=data.get("time_out"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
        db.session.add(shift)
        db.session.commit()
        return jsonify({"message": "Shift created successfully!", "shift": shift.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@shift_bp.route('/<int:shift_id>', methods=['PUT'])
def update_shift(shift_id):
    data = request.json
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({"error": "Shift not found"}), 404

    try:
        # Update only the provided fields
        if "shift_name" in data:
            shift.shift_name = data["shift_name"]
        if "time_in" in data:
            shift.time_in = data["time_in"]
        if "time_out" in data:
            shift.time_out = data["time_out"]
        shift.updated_at = db.func.now()  # Update the updated_at timestamp

        db.session.commit()
        return jsonify({"message": "Shift updated successfully!", "shift": shift.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@shift_bp.route('/<int:shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({"error": "Shift not found"}), 404

    try:
        db.session.delete(shift)
        db.session.commit()
        return jsonify({"message": "Shift deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
