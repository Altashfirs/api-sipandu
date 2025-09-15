from flask import Blueprint, jsonify, request
from app.database import db
from app.models.absence import Absence
from app.models.employees import Employee
from app.models.position import Position
from app.models.customers import Customer
from datetime import datetime
import os
import math
import logging
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import aliased
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)

absence_bp = Blueprint('absence', __name__, url_prefix='/api/absence')

def _draw_single_page(page_data, page_num, total_pages, start_index, headers, col_widths, output_dir, customer_id):
    """
    Draw a single page of the absence report as a PNG image.
    """
    SCALE = 2
    margin = 40 * SCALE
    row_height = 70 * SCALE
    table_header_height = 75 * SCALE
    image_width = sum(col_widths) + (margin * 2)
    num_rows_on_page = len(page_data)
    image_height = table_header_height + (num_rows_on_page * row_height) + (margin * 2)

    img = Image.new('RGB', (image_width, image_height), 'white')
    draw = ImageDraw.Draw(img)

    try:
        base_path = os.path.dirname(__file__)
        font_path = os.path.join(base_path, '..', 'fonts', 'Monomakh-Regular.ttf')
        font_header = ImageFont.truetype(font_path, 22 * SCALE)
        font_row = ImageFont.truetype(font_path, 20 * SCALE)
    except IOError:
        logging.error("Font Monomakh not found. Ensure 'Monomakh-Regular.ttf' exists in 'app/fonts'.")
        raise Exception("Font file not found")

    table_start_y = margin

    # Draw table header
    current_x = margin
    for i, header in enumerate(headers):
        draw.rectangle(
            [current_x, table_start_y, current_x + col_widths[i], table_start_y + table_header_height],
            fill='#4472C4', outline='white', width=1 * SCALE
        )
        bbox = draw.textbbox((0, 0), header, font=font_header)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        text_x = current_x + (col_widths[i] - text_width) / 2
        text_y = table_start_y + (table_header_height - text_height) / 2
        draw.text((text_x, text_y), header, font=font_header, fill='white')
        current_x += col_widths[i]

    # Draw table rows
    current_y = table_start_y + table_header_height
    for i, row in enumerate(page_data):
        current_x = margin
        row_number = str(start_index + i + 1)
        row_content = [
            row_number,
            row.employee_absen_name or '-',
            row.position_name or '-',
            row.tanggal_absen.strftime("%d-%m-%Y") if row.tanggal_absen else '-',
            row.keterangan or '-',
            row.employee_backup_name or '-',
            row.tanggal_backup.strftime("%d-%m-%Y") if row.tanggal_backup else '-'
        ]
        
        row_color = '#F2F2F2' if i % 2 == 1 else 'white'
        
        for j, cell in enumerate(row_content):
            draw.rectangle(
                [current_x, current_y, current_x + col_widths[j], current_y + row_height],
                fill=row_color, outline='#D9D9D9', width=1 * SCALE
            )
            
            text_to_draw = str(cell)
            bbox = draw.textbbox((0, 0), text_to_draw, font=font_row)
            text_height = bbox[3] - bbox[1]
            text_y = current_y + (row_height - text_height) / 2
            text_x = current_x + (20 * SCALE) if j != 0 else current_x + (col_widths[j] - (bbox[2] - bbox[0])) / 2

            draw.text((text_x, text_y), text_to_draw, font=font_row, fill='black')
            current_x += col_widths[j]

        current_y += row_height

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"absence_report_{customer_id}_{timestamp}_page_{page_num}_of_{total_pages}.png"
    file_path = os.path.join(output_dir, filename)
    
    img.save(file_path, dpi=(300, 300))
    
    file_url = f"/laporan/laporan-absence/{filename}"
    return file_url

@absence_bp.route('/create-absence-report-image', methods=['POST'])
def create_absence_report_image():
    """
    Generate PNG images for absence data by customer_id.
    """
    try:
        data = request.get_json()
        if not data or 'customer_id' not in data:
            return jsonify({"error": "customer_id is required"}), 400

        customer_id = data.get('customer_id')
        keterangan = data.get('keterangan', '-')  # Default to '-' if keterangan not provided

        EmployeeAbsen = aliased(Employee)
        EmployeeBackup = aliased(Employee)

        absence_data = db.session.query(
            EmployeeAbsen.employees_name.label("employee_absen_name"),
            Position.position_name.label("position_name"),
            Absence.tanggal_absen,
            Absence.tanggal_backup,
            EmployeeBackup.employees_name.label("employee_backup_name")
        ).join(EmployeeAbsen, Absence.id_employee_absen == EmployeeAbsen.id) \
         .join(EmployeeBackup, Absence.id_employee_backup == EmployeeBackup.id) \
         .join(Position, EmployeeAbsen.position_id == Position.position_id, isouter=True) \
         .join(Customer, Absence.id_customer == Customer.customer_id) \
         .filter(Absence.id_customer == customer_id) \
         .order_by(Absence.tanggal_absen.desc()).all()

        if not absence_data:
            return jsonify({"error": "No absence data found for the given customer_id"}), 404

        # Add keterangan to each row
        absence_data_with_keterangan = [
            type('Row', (), {
                'employee_absen_name': row.employee_absen_name,
                'position_name': row.position_name,
                'tanggal_absen': row.tanggal_absen,
                'keterangan': keterangan,
                'employee_backup_name': row.employee_backup_name,
                'tanggal_backup': row.tanggal_backup
            }) for row in absence_data
        ]

        ROWS_PER_PAGE = 20
        total_rows = len(absence_data_with_keterangan)
        total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
        
        output_dir = os.path.join(os.getcwd(), 'laporan', 'laporan-absence')
        os.makedirs(output_dir, exist_ok=True)
        
        SCALE = 2
        headers = [
            "No", "Nama Karyawan", "Jabatan", "Tanggal Ketidakhadiran",
            "Keterangan", "Karyawan Pengganti", "Tanggal Backup"
        ]
        col_widths = [w * SCALE for w in [80, 320, 240, 180, 300, 320, 180]]
        
        generated_urls = []
        for page_num in range(total_pages):
            start_index = page_num * ROWS_PER_PAGE
            end_index = start_index + ROWS_PER_PAGE
            page_data = absence_data_with_keterangan[start_index:end_index]
            
            file_url = _draw_single_page(
                page_data=page_data,
                page_num=page_num + 1,
                total_pages=total_pages,
                start_index=start_index,
                headers=headers,
                col_widths=col_widths,
                output_dir=output_dir,
                customer_id=customer_id
            )
            generated_urls.append(file_url)
            logging.info(f"Generated absence page {page_num + 1}/{total_pages} at {file_url}")

        return jsonify({
            "message": f"Successfully generated {total_pages} page(s).",
            "image_urls": generated_urls
        }), 200

    except Exception as e:
        logging.error(f"Error generating absence report image: {traceback.format_exc()}")
        return jsonify({"error": "Failed to generate absence report image", "message": str(e)}), 500

@absence_bp.route('/', methods=['POST'])
def create_absence():
    """
    Create a new absence record.
    """
    try:
        data = request.get_json()
        required_fields = ['id_customer', 'id_employee_absen', 'tanggal_absen', 'id_employee_backup', 'tanggal_backup']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Validate customer and employees
        customer = Customer.query.get(data['id_customer'])
        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        employee_absen = Employee.query.get(data['id_employee_absen'])
        if not employee_absen:
            return jsonify({"error": "Absent employee not found"}), 404

        employee_backup = Employee.query.get(data['id_employee_backup'])
        if not employee_backup:
            return jsonify({"error": "Backup employee not found"}), 404

        # Parse dates
        try:
            tanggal_absen = datetime.strptime(data['tanggal_absen'], '%Y-%m-%d').date()
            tanggal_backup = datetime.strptime(data['tanggal_backup'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

        # Create new absence record
        new_absence = Absence(
            id_customer=data['id_customer'],
            id_employee_absen=data['id_employee_absen'],
            tanggal_absen=tanggal_absen,
            id_employee_backup=data['id_employee_backup'],
            tanggal_backup=tanggal_backup
        )
        db.session.add(new_absence)
        db.session.commit()

        return jsonify({
            "message": "Absence record created successfully!",
            "data": new_absence.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create absence record", "message": str(e)}), 500

@absence_bp.route('/', methods=['GET'])
def get_all_absences():
    """
    Retrieve all absence records with related employee and customer names.
    """
    try:
        EmployeeAbsen = aliased(Employee)
        EmployeeBackup = aliased(Employee)

        results = db.session.query(
            Absence,
            Customer.name.label('customer_name'),
            EmployeeAbsen.employees_name.label('employee_absen_name'),
            EmployeeBackup.employees_name.label('employee_backup_name')
        ).join(Customer, Absence.id_customer == Customer.customer_id) \
         .join(EmployeeAbsen, Absence.id_employee_absen == EmployeeAbsen.id) \
         .join(EmployeeBackup, Absence.id_employee_backup == EmployeeBackup.id) \
         .order_by(Absence.tanggal_absen.desc()).all()

        if not results:
            return jsonify([]), 200

        output = []
        for record, customer_name, absen_name, backup_name in results:
            data = record.to_dict()
            data['customer_name'] = customer_name
            data['employee_absen_name'] = absen_name
            data['employee_backup_name'] = backup_name
            output.append(data)

        return jsonify(output), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve absence records", "message": str(e)}), 500

@absence_bp.route('/<int:id>', methods=['GET'])
def get_absence_by_id(id):
    """
    Retrieve a single absence record by id_absence.
    """
    try:
        EmployeeAbsen = aliased(Employee)
        EmployeeBackup = aliased(Employee)

        result = db.session.query(
            Absence,
            Customer.name.label('customer_name'),
            EmployeeAbsen.employees_name.label('employee_absen_name'),
            EmployeeBackup.employees_name.label('employee_backup_name')
        ).join(Customer, Absence.id_customer == Customer.customer_id) \
         .join(EmployeeAbsen, Absence.id_employee_absen == EmployeeAbsen.id) \
         .join(EmployeeBackup, Absence.id_employee_backup == EmployeeBackup.id) \
         .filter(Absence.id_absence == id).first()

        if not result:
            return jsonify({"error": "Absence record not found"}), 404

        record, customer_name, absen_name, backup_name = result
        data = record.to_dict()
        data['customer_name'] = customer_name
        data['employee_absen_name'] = absen_name
        data['employee_backup_name'] = backup_name

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve absence record", "message": str(e)}), 500

@absence_bp.route('/<int:id>', methods=['PUT'])
def update_absence(id):
    """
    Update an existing absence record.
    """
    try:
        record = Absence.query.get(id)
        if not record:
            return jsonify({"error": "Absence record not found"}), 404

        data = request.get_json()

        # Validate customer and employees if provided
        if 'id_customer' in data:
            customer = Customer.query.get(data['id_customer'])
            if not customer:
                return jsonify({"error": "Customer not found"}), 404
            record.id_customer = data['id_customer']

        if 'id_employee_absen' in data:
            employee_absen = Employee.query.get(data['id_employee_absen'])
            if not employee_absen:
                return jsonify({"error": "Absent employee not found"}), 404
            record.id_employee_absen = data['id_employee_absen']

        if 'id_employee_backup' in data:
            employee_backup = Employee.query.get(data['id_employee_backup'])
            if not employee_backup:
                return jsonify({"error": "Backup employee not found"}), 404
            record.id_employee_backup = data['id_employee_backup']

        # Update dates if provided
        if 'tanggal_absen' in data:
            try:
                record.tanggal_absen = datetime.strptime(data['tanggal_absen'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid tanggal_absen format, use YYYY-MM-DD"}), 400

        if 'tanggal_backup' in data:
            try:
                record.tanggal_backup = datetime.strptime(data['tanggal_backup'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid tanggal_backup format, use YYYY-MM-DD"}), 400

        db.session.commit()

        return jsonify({
            "message": "Absence record updated successfully!",
            "data": record.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update absence record", "message": str(e)}), 500

@absence_bp.route('/<int:id>', methods=['DELETE'])
def delete_absence(id):
    """
    Delete an absence record.
    """
    try:
        record = Absence.query.get(id)
        if not record:
            return jsonify({"error": "Absence record not found"}), 404

        db.session.delete(record)
        db.session.commit()

        return jsonify({"message": "Absence record deleted successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete absence record", "message": str(e)}), 500