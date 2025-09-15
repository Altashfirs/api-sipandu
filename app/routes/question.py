from flask import Blueprint, jsonify, request
from app.database import db
from app.models.question import Question

question_bp = Blueprint('questions', __name__, url_prefix='/api/questions')

@question_bp.route('/', methods=['GET'])
def get_all_questions():
    """
    Retrieve all questions ordered by descending question_id or filtered by matrix_id and position_id.
    """
    matrix_id = request.args.get('matrix_id')
    position_id = request.args.get('position_id')

    query = Question.query
    if matrix_id:
        query = query.filter_by(matrix_id=matrix_id)
    if position_id:
        query = query.filter_by(position_id=position_id)

    questions = query.order_by(Question.question_id.desc()).all()
    return jsonify([question.to_dict() for question in questions])


@question_bp.route('/<int:question_id>', methods=['GET'])
def get_question_by_id(question_id):
    """
    Retrieve a single question by ID.
    """
    question = Question.query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(question.to_dict())

@question_bp.route('/', methods=['POST'])
def create_question():
    """
    Create a new question.
    """
    data = request.json
    if not data.get("question_text"):
        return jsonify({"error": "Question text is required"}), 400

    question = Question(
        question_text=data.get("question_text"),
        position_id=data.get("position_id"),
        building_id=data.get("building_id"),
        matrix_id=data.get("matrix_id"),
        answer_a=data.get("answer_a"),
        answer_b=data.get("answer_b"),
        answer_c=data.get("answer_c"),
        answer=data.get("answer"),
    )
    db.session.add(question)
    db.session.commit()
    return jsonify({"message": "Question created successfully!", "question": question.to_dict()}), 201


@question_bp.route('/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    """
    Update an existing question by ID.
    """
    data = request.json
    question = Question.query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    if data.get("question_text"):
        question.question_text = data.get("question_text")
    if "position_id" in data:
        question.position_id = data.get("position_id")
    if "building_id" in data:
        question.building_id = data.get("building_id")
    if "matrix_id" in data:
        question.matrix_id = data.get("matrix_id")
    if "answer_a" in data:
        question.answer_a = data.get("answer_a")
    if "answer_b" in data:
        question.answer_b = data.get("answer_b")
    if "answer_c" in data:
        question.answer_c = data.get("answer_c")
    if "answer" in data:
        question.answer = data.get("answer")
    
    db.session.commit()
    return jsonify({"message": "Question updated successfully!", "question": question.to_dict()})


@question_bp.route('/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """
    Delete a question by ID.
    """
    question = Question.query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    db.session.delete(question)
    db.session.commit()
    return jsonify({"message": "Question deleted successfully!"})
