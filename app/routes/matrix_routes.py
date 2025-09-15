from flask import Blueprint, jsonify, request
from app.database import db
from app.models.matrix import Matrix

matrix_bp = Blueprint('matrix', __name__, url_prefix='/api/matrix')

@matrix_bp.route('/', methods=['GET'])
def get_all_matrices():
    matrices = Matrix.query.order_by(Matrix.matrix_id.desc()).all()
    return jsonify([matrix.to_dict() for matrix in matrices])

@matrix_bp.route('/<int:matrix_id>', methods=['GET'])
def get_matrix_by_id(matrix_id):
    """
    Retrieve a single matrix by its ID.
    """
    matrix = Matrix.query.get(matrix_id)
    if not matrix:
        return jsonify({"error": "Matrix not found"}), 404

    return jsonify(matrix.to_dict()), 200


@matrix_bp.route('/', methods=['POST'])
def create_matrix():
    data = request.json
    if not data.get("matrix_name"):
        return jsonify({"error": "Matrix name is required"}), 400

    matrix = Matrix(matrix_name=data.get("matrix_name"))
    db.session.add(matrix)
    db.session.commit()
    return jsonify({"message": "Matrix created successfully!", "matrix": matrix.to_dict()}), 201

@matrix_bp.route('/<int:matrix_id>', methods=['PUT'])
def update_matrix(matrix_id):
    data = request.json
    matrix = Matrix.query.get(matrix_id)
    if not matrix:
        return jsonify({"error": "Matrix not found"}), 404

    if data.get("matrix_name"):
        matrix.matrix_name = data.get("matrix_name")
    db.session.commit()
    return jsonify({"message": "Matrix updated successfully!", "matrix": matrix.to_dict()})

@matrix_bp.route('/<int:matrix_id>', methods=['DELETE'])
def delete_matrix(matrix_id):
    matrix = Matrix.query.get(matrix_id)
    if not matrix:
        return jsonify({"error": "Matrix not found"}), 404

    db.session.delete(matrix)
    db.session.commit()
    return jsonify({"message": "Matrix deleted successfully!"})
