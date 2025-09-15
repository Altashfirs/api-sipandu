import datetime, random, string
from flask import Blueprint, jsonify, request
from app.database import db
from app.models.customers import Customer
from app.models.employees import Employee

customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')

@customers_bp.route('/', methods=['GET'])
def get_customers():
    """Retrieve all customers."""
    # Query sinkron tanpa 'await'
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers])

@customers_bp.route('/total', methods=['GET'])
def get_customers_total():
    """Retrieve all customers with the total number of employees."""
    # Query all customers
    customers = Customer.query.all()
    
    # Prepare the response with total employees count
    response = []
    for customer in customers:
        # Count the number of employees for each customer
        total_employees = Employee.query.filter_by(customer_id=customer.customer_id).count()
        
        # Add the customer data along with total_employees to the response
        customer_data = customer.to_dict()
        customer_data['total_employees'] = total_employees
        response.append(customer_data)
    
    return jsonify(response)

@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Retrieve a single customer by ID."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer.to_dict())

def generate_code():
    """Generate unique customer code"""
    today = datetime.date.today()
    random_str = ''.join(random.choices(string.ascii_uppercase, k=5))
    return f"{today.year}/{random_str}/{today.year}-{today.month}-{today.day}"

@customers_bp.route('/', methods=['POST'])
def create_customer():
    """Create a new customer."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    try:
        # kalau code kosong/null → generate otomatis
        if not data.get("code"):
            data["code"] = generate_code()

        customer = Customer(**data)
        db.session.add(customer)
        db.session.commit()
        return jsonify({
            "message": "Customer created successfully!",
            "customer": customer.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update an existing customer."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    try:
        # Update field customer berdasarkan input
        for key, value in data.items():
            setattr(customer, key, value)
        db.session.commit()
        return jsonify({"message": "Customer updated successfully!", "customer": customer.to_dict()})
    except Exception as e:
        db.session.rollback()  # Rollback jika terjadi error
        return jsonify({"error": str(e)}), 500

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    try:
        # Hapus customer
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": "Customer deleted successfully!"})
    except Exception as e:
        db.session.rollback()  # Rollback jika terjadi error
        return jsonify({"error": str(e)}), 500
