from flask import Blueprint, jsonify, request
from app.database import db
from app.models.results_test import ResultsTest

results_test_bp = Blueprint('results_test', __name__, url_prefix='/api/results_test')

@results_test_bp.route('/', methods=['GET'])
def get_all_results():
    """
    Retrieve all results.
    """
    results = ResultsTest.query.all()
    return jsonify([result.to_dict() for result in results])

@results_test_bp.route('/<int:id_result>', methods=['GET'])
def get_result_by_id(id_result):
    """
    Retrieve a single result by ID.
    """
    result = ResultsTest.query.get(id_result)
    if not result:
        return jsonify({"error": "Result not found"}), 404
    return jsonify(result.to_dict())

@results_test_bp.route('/test/<int:id_test>', methods=['GET'])
def get_results_by_test(id_test):
    """
    Retrieve all results for a specific test.
    """
    results = ResultsTest.query.filter_by(id_test=id_test).all()
    if not results:
        return jsonify([])  # Return an empty array if no results are found
    return jsonify([result.to_dict() for result in results]), 200
    
@results_test_bp.route('/bulk', methods=['POST'])
def create_multiple_results():
    """
    Submit multiple results.
    """
    data = request.json  # Expecting a list of results
    try:
        for result in data:
            new_result = ResultsTest(
                id_test=result['id_test'],
                id_question=result['id_question'],
                answer=result['answer']
            )
            db.session.add(new_result)
        db.session.commit()
        return jsonify({"message": "All results submitted successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error creating results: {str(e)}"}), 500

@results_test_bp.route('/', methods=['POST'])
def create_result():
    """
    Create a new result.
    """
    data = request.json
    if not data.get("id_test") or not data.get("id_question") or not data.get("answer"):
        return jsonify({"error": "id_test, id_question, and answer are required."}), 400

    try:
        result = ResultsTest(
            id_test=data.get("id_test"),
            id_question=data.get("id_question"),
            answer=data.get("answer")
        )
        db.session.add(result)
        db.session.commit()
        return jsonify({"message": "Result created successfully!", "result": result.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error creating result: {str(e)}"}), 500

@results_test_bp.route('/<int:id_result>', methods=['PUT'])
def update_result(id_result):
    """
    Update an existing result by ID.
    """
    data = request.json
    result = ResultsTest.query.get(id_result)
    if not result:
        return jsonify({"error": "Result not found"}), 404

    try:
        if "id_test" in data:
            result.id_test = data["id_test"]
        if "id_question" in data:
            result.id_question = data["id_question"]
        if "answer" in data:
            result.answer = data["answer"]

        db.session.commit()
        return jsonify({"message": "Result updated successfully!", "result": result.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error updating result: {str(e)}"}), 500

@results_test_bp.route('/<int:id_result>', methods=['DELETE'])
def delete_result(id_result):
    """
    Delete a result by ID.
    """
    result = ResultsTest.query.get(id_result)
    if not result:
        return jsonify({"error": "Result not found"}), 404

    try:
        db.session.delete(result)
        db.session.commit()
        return jsonify({"message": "Result deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error deleting result: {str(e)}"}), 500

@results_test_bp.route('/test/<int:id_test>', methods=['DELETE'])
def delete_test(id_test):
    """
    Delete all results for a specific test by id_test.
    """
    results = ResultsTest.query.filter_by(id_test=id_test).all()
    if not results:
        return jsonify({"error": "No results found for the specified test ID."}), 404

    try:
        for result in results:
            db.session.delete(result)
        db.session.commit()
        return jsonify({"message": f"All results for test ID {id_test} deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error deleting results: {str(e)}"}), 500
