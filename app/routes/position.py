from flask import Blueprint, jsonify, request
from app.database import db
from app.models.position import Position
from app.models.employees import Employee

position_bp = Blueprint('position', __name__, url_prefix='/api/positions')

@position_bp.route('/', methods=['GET'])
def get_positions():
    positions = Position.query.all()
    return jsonify([position.to_dict() for position in positions])

@position_bp.route('/total', methods=['GET'])
def get_positions_total():
    """Retrieve all positions with the total number of employees."""
    # Query all positions
    positions = Position.query.all()
    
    # Prepare the response with total employees count
    response = []
    for position in positions:
        # Count the number of employees for each position
        total_employees = Employee.query.filter_by(position_id=position.position_id).count()
        
        # Add the position data along with total_employees to the response
        position_data = position.to_dict()
        position_data['total_employees'] = total_employees
        response.append(position_data)
    
    return jsonify(response)

@position_bp.route('/<int:position_id>', methods=['GET'])
def get_position_by_id(position_id):
    position = Position.query.get(position_id)
    if not position:
        return jsonify({"error": "Position not found"}), 404
    return jsonify(position.to_dict())

@position_bp.route('/', methods=['POST'])
def create_position():
    data = request.json
    position = Position(
        position_name=data.get("position_name"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )
    db.session.add(position)
    db.session.commit()
    return jsonify({"message": "Position created successfully!", "position": position.to_dict()}), 201

@position_bp.route('/<int:position_id>', methods=['PUT'])
def update_position(position_id):
    data = request.json
    position = Position.query.get(position_id)
    if not position:
        return jsonify({"error": "Position not found"}), 404
    for key, value in data.items():
        setattr(position, key, value)
    db.session.commit()
    return jsonify({"message": "Position updated successfully!", "position": position.to_dict()})

@position_bp.route('/<int:position_id>', methods=['DELETE'])
def delete_position(position_id):
    position = Position.query.get(position_id)
    if not position:
        return jsonify({"error": "Position not found"}), 404
    db.session.delete(position)
    db.session.commit()
    return jsonify({"message": "Position deleted successfully!"})
