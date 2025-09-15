from flask import Blueprint, jsonify, request
from app.database import db
from app.models.turn_over import TurnOver
from app.models.employees import Employee # Diperlukan untuk mengambil nama karyawan
from app.models.customers import Customer # Diperlukan untuk mengambil nama customer
from app.models.position import Position
from datetime import datetime
import os
import math
import logging
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import aliased
import traceback

# Membuat Blueprint untuk turn_over
turn_over_bp = Blueprint('turn_over', __name__, url_prefix='/api/turn-over')

def _draw_single_page(page_data, page_num, total_pages, start_index, headers, col_widths, output_dir, customer_id):
    """
    Draw a single page of the turnover report as a PNG image.
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
            row.employee_old_name or '-',
            row.employee_old_nip or '-',
            row.position_name or '-',
            row.turn_over_date.strftime("%d-%m-%Y") if row.turn_over_date else '-',
            row.turn_over_reason or '-',
            row.employee_new_name or '-',
            row.employee_new_nip or '-',
            row.employee_new_join_date.strftime("%d-%m-%Y") if row.employee_new_join_date else '-'
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
    filename = f"turnover_report_{customer_id}_{timestamp}_page_{page_num}_of_{total_pages}.png"
    file_path = os.path.join(output_dir, filename)
    
    img.save(file_path, dpi=(300, 300))
    
    file_url = f"/laporan/laporan-turnover/{filename}"
    return file_url

@turn_over_bp.route('/create-turnover-report-image', methods=['POST'])
def create_turnover_report_image():
    """
    Generate PNG images for turnover data by customer_id.
    """
    try:
        data = request.get_json()
        if not data or 'customer_id' not in data:
            return jsonify({"error": "customer_id is required"}), 400

        customer_id = data.get('customer_id')

        EmployeeNew = aliased(Employee)
        EmployeeOld = aliased(Employee)

        turnover_data = db.session.query(
            EmployeeOld.employees_name.label("employee_old_name"),
            EmployeeOld.employees_nip.label("employee_old_nip"),
            Position.position_name.label("position_name"),
            TurnOver.turn_over_date,
            TurnOver.turn_over_reason,
            EmployeeNew.employees_name.label("employee_new_name"),
            EmployeeNew.employees_nip.label("employee_new_nip"),
            EmployeeNew.tanggal_join.label("employee_new_join_date")
        ).join(EmployeeOld, TurnOver.id_employee_old == EmployeeOld.id) \
         .join(EmployeeNew, TurnOver.id_employee == EmployeeNew.id) \
         .join(Position, EmployeeOld.position_id == Position.position_id, isouter=True) \
         .join(Customer, TurnOver.id_customer == Customer.customer_id) \
         .filter(TurnOver.id_customer == customer_id) \
         .order_by(TurnOver.turn_over_date.desc()).all()

        if not turnover_data:
            return jsonify({"error": "No turnover data found for the given customer_id"}), 404

        ROWS_PER_PAGE = 20
        total_rows = len(turnover_data)
        total_pages = math.ceil(total_rows / ROWS_PER_PAGE)
        
        output_dir = os.path.join(os.getcwd(), 'laporan', 'laporan-turnover')
        os.makedirs(output_dir, exist_ok=True)
        
        SCALE = 2
        headers = [
            "No", "Nama Karyawan", "NIK", "Jabatan", "Tanggal Resign",
            "Keterangan", "Karyawan Pengganti", "NIK", "Tanggal Joint"
        ]
        col_widths = [w * SCALE for w in [80, 320, 240, 240, 180, 300, 320, 240, 180]]
        
        generated_urls = []
        for page_num in range(total_pages):
            start_index = page_num * ROWS_PER_PAGE
            end_index = start_index + ROWS_PER_PAGE
            page_data = turnover_data[start_index:end_index]
            
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
            logging.info(f"Generated turnover page {page_num + 1}/{total_pages} at {file_url}")

        return jsonify({
            "message": f"Successfully generated {total_pages} page(s).",
            "image_urls": generated_urls
        }), 200

    except Exception as e:
        logging.error(f"Error generating turnover report image: {traceback.format_exc()}")
        return jsonify({"error": "Failed to generate turnover report image", "message": str(e)}), 500

@turn_over_bp.route('/', methods=['POST'])
def create_turn_over():
    """
    Endpoint untuk membuat data turn over baru.
    """
    try:
        data = request.get_json()
        required_fields = ['id_customer', 'id_employee', 'id_employee_old', 'turn_over_date', 'turn_over_desc', 'turn_over_reason']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        turn_over_date_obj = datetime.strptime(data['turn_over_date'], '%Y-%m-%d').date()

        new_turn_over = TurnOver(
            id_customer=data['id_customer'],
            id_employee=data['id_employee'],
            id_employee_old=data['id_employee_old'],
            turn_over_date=turn_over_date_obj,
            turn_over_desc=data['turn_over_desc'],
            turn_over_reason=data['turn_over_reason']
        )
        db.session.add(new_turn_over)
        db.session.commit()

        return jsonify({
            "message": "Turn over record created successfully!",
            "data": new_turn_over.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create turn over record", "message": str(e)}), 500

@turn_over_bp.route('/', methods=['GET'])
def get_all_turn_overs():
    """
    Endpoint untuk mengambil semua data turn over dengan informasi nama.
    """
    try:
        EmployeeNew = aliased(Employee)
        EmployeeOld = aliased(Employee)

        results = db.session.query(
            TurnOver,
            Customer.name.label('customer_name'), # <-- DIPERBAIKI: Menggunakan Customer.name dan diberi label
            EmployeeNew.employees_name.label('employee_new_name'),
            EmployeeOld.employees_name.label('employee_old_name')
        ).join(Customer, TurnOver.id_customer == Customer.customer_id)\
         .join(EmployeeNew, TurnOver.id_employee == EmployeeNew.id)\
         .join(EmployeeOld, TurnOver.id_employee_old == EmployeeOld.id)\
         .order_by(TurnOver.turn_over_date.desc()).all()

        if not results:
            return jsonify([]), 200 # Return list kosong jika tidak ada data

        output = []
        for record, customer_name, new_name, old_name in results:
            data = record.to_dict()
            data['customer_name'] = customer_name # <-- DIPERBAIKI: Key JSON dibuat konsisten
            data['employee_new_name'] = new_name
            data['employee_old_name'] = old_name
            output.append(data)

        return jsonify(output), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve turn over records", "message": str(e)}), 500

@turn_over_bp.route('/<int:id>', methods=['GET'])
def get_turn_over_by_id(id):
    """
    Endpoint untuk mengambil satu data turn over berdasarkan ID-nya.
    """
    try:
        EmployeeNew = aliased(Employee)
        EmployeeOld = aliased(Employee)

        result = db.session.query(
            TurnOver,
            Customer.name.label('customer_name'), # <-- DIPERBAIKI: Menggunakan Customer.name dan diberi label
            EmployeeNew.employees_name.label('employee_new_name'),
            EmployeeOld.employees_name.label('employee_old_name')
        ).join(Customer, TurnOver.id_customer == Customer.customer_id)\
         .join(EmployeeNew, TurnOver.id_employee == EmployeeNew.id)\
         .join(EmployeeOld, TurnOver.id_employee_old == EmployeeOld.id)\
         .filter(TurnOver.id_turn_over == id).first()

        if not result:
            return jsonify({"error": "Turn over record not found"}), 404

        record, customer_name, new_name, old_name = result
        data = record.to_dict()
        data['customer_name'] = customer_name # <-- DIPERBAIKI: Key JSON dibuat konsisten
        data['employee_new_name'] = new_name
        data['employee_old_name'] = old_name
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve turn over record", "message": str(e)}), 500

@turn_over_bp.route('/<int:id>', methods=['PUT'])
def update_turn_over(id):
    """
    Endpoint untuk memperbarui data turn over.
    """
    try:
        record = TurnOver.query.get(id)
        if not record:
            return jsonify({"error": "Turn over record not found"}), 404

        data = request.get_json()
        
        record.id_customer = data.get('id_customer', record.id_customer)
        record.id_employee = data.get('id_employee', record.id_employee)
        record.id_employee_old = data.get('id_employee_old', record.id_employee_old)
        record.turn_over_desc = data.get('turn_over_desc', record.turn_over_desc)
        record.turn_over_reason = data.get('turn_over_reason', record.turn_over_reason)
        
        if 'turn_over_date' in data:
            record.turn_over_date = datetime.strptime(data['turn_over_date'], '%Y-%m-%d').date()

        db.session.commit()

        return jsonify({
            "message": "Turn over record updated successfully!",
            "data": record.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update turn over record", "message": str(e)}), 500

@turn_over_bp.route('/<int:id>', methods=['DELETE'])
def delete_turn_over(id):
    """
    Endpoint untuk menghapus data turn over.
    """
    try:
        record = TurnOver.query.get(id)
        if not record:
            return jsonify({"error": "Turn over record not found"}), 404

        db.session.delete(record)
        db.session.commit()

        return jsonify({"message": "Turn over record deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete turn over record", "message": str(e)}), 500