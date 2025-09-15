from flask import Blueprint, jsonify, request
from app.database import db
from app.models.topic import Topic
from datetime import datetime

topic_bp = Blueprint('topic', __name__, url_prefix='/api/topic')

# Get all topics
@topic_bp.route('/', methods=['GET'])
def get_all_topics():
    """
    Retrieve all topics, ordered by descending id_topic.
    """
    topics = Topic.query.order_by(Topic.id_topic.desc()).all()
    return jsonify([topic.to_dict() for topic in topics])

# Create a new topic
@topic_bp.route('/', methods=['POST'])
def create_topic():
    """
    Create a new topic.
    """
    data = request.json
    if not data.get("topic_name"):
        return jsonify({"error": "Topic name is required"}), 400

    topic = Topic(
        topic_name=data.get("topic_name"),
        created_at=datetime.utcnow()
    )
    db.session.add(topic)
    db.session.commit()
    return jsonify({"message": "Topic created successfully!", "topic": topic.to_dict()}), 201

# Get a topic by its unique id_topic
@topic_bp.route('/<int:id_topic>', methods=['GET'])
def get_topic_by_id(id_topic):
    """
    Retrieve a topic by its unique id_topic.
    """
    topic = Topic.query.get(id_topic)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    return jsonify(topic.to_dict())

# Update an existing topic
@topic_bp.route('/<int:id_topic>', methods=['PUT'])
def update_topic(id_topic):
    """
    Update an existing topic by ID.
    """
    data = request.json
    topic = Topic.query.get(id_topic)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    if "topic_name" in data:
        topic.topic_name = data.get("topic_name")
    topic.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "Topic updated successfully!", "topic": topic.to_dict()})

# Delete a topic
@topic_bp.route('/<int:id_topic>', methods=['DELETE'])
def delete_topic(id_topic):
    """
    Delete a topic by ID.
    """
    topic = Topic.query.get(id_topic)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    db.session.delete(topic)
    db.session.commit()
    return jsonify({"message": "Topic deleted successfully!"})