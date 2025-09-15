import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app.database import db
from app.models.handover import Handover
from app.models.employees import Employee
from datetime import datetime, timedelta, date
from sqlalchemy.sql import text
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
from PIL import Image as PILImage

handover_bp = Blueprint('handover', __name__, url_prefix='/api/handover')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def format_date(date):
    return date.strftime("%Y-%m-%d") if date else None

def format_datetime(dt):
    return dt.strftime("%d %B %Y Jam %H:%M") if dt else None

def format_table_date(date):
    """Format date for table display in PDF."""
    if not date:
        return "-"
    parsed_date = datetime.strptime(str(date), "%Y-%m-%d") if isinstance(date, str) else date
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{parsed_date.day} {months[parsed_date.month-1]} {parsed_date.year}"

def serialize_result(result):
    result_dict = dict(result._mapping)
    for key, value in result_dict.items():
        if isinstance(value, datetime):
            result_dict[key] = format_datetime(value)
        elif isinstance(value, timedelta):
            result_dict[key] = str(value)
        elif isinstance(value, date):
            result_dict[key] = format_date(value)
    return result_dict

@handover_bp.route('/export_pdf', methods=['GET'])
def export_pdf():
    try:
        # Get filter parameters
        customer_id = request.args.get('customer_id', type=int)
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')

        # Default dates: last 30 days to today
        today = datetime.now().date()
        last_month = today - timedelta(days=30)

        # Parse start date
        if not tanggal_awal:
            start_date = last_month
        else:
            start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d').date()

        # Parse end date
        if not tanggal_akhir:
            end_date = today
        else:
            end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d').date()

        # Validate dates
        if start_date > end_date:
            return jsonify({"error": "tanggal_awal cannot be after tanggal_akhir"}), 400

        # Format dates for filename and header
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Build SQL query with join to employees table
        sql = text("""
            SELECT handover.*, employees.employees_name
            FROM handover
            JOIN employees ON employees.id = handover.id
            WHERE handover.handover_date >= :start_date
              AND handover.handover_date <= :end_date
              AND (:customer_id IS NULL OR employees.customer_id = :customer_id)
            ORDER BY handover.id_handover DESC
        """)

        # Execute query
        results = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'customer_id': customer_id
        }).fetchall()

        if not results:
            return jsonify({"error": "Tidak ada data"}), 404

        # Prepare PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=20*mm)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        normal_style = styles['Normal']
        normal_style.fontSize = 10

        # Style for text fields with word wrapping
        text_style = styles['Normal']
        text_style.fontSize = 8
        text_style.leading = 10
        text_style.wordWrap = 'CJK'

        # Add header
        elements.append(Paragraph(f"Data Serah Terima: {start_date_str} - {end_date_str}", title_style))
        elements.append(Spacer(1, 10*mm))

        # Build table data
        table_data = [
            ['No', 'Tanggal', 'Nama Barang', 'Pemberi', 'Penyerah', 'Posisi Pemberi', 'Penerima', 'Foto Awal', 'Foto Akhir']
        ]

        for idx, row in enumerate(results, 1):
            # Prepare text fields with word wrapping
            item_name = Paragraph(row.item_name or '-', text_style)
            givers_name = Paragraph(row.givers_name or '-', text_style)
            givers_name_end = Paragraph(row.givers_name_end or '-', text_style)
            givers_position = Paragraph(row.givers_position or '-', text_style)
            employees_name = Paragraph(row.employees_name or '-', text_style)

            # Format date
            formatted_date = format_table_date(row.handover_date)

            # Prepare photo fields
            photo_awal = '-'
            if row.handover_photo:
                # Handle relative path correctly
                photo_path = os.path.join(os.getcwd(), row.handover_photo) if row.handover_photo.startswith('uploads/') else row.handover_photo
                if os.path.exists(photo_path):
                    try:
                        with PILImage.open(photo_path) as img:
                            img = img.convert('RGB')
                            target_size = int(20 * mm * 75 / 25.4)  # 75 DPI for 20mm (~118 pixels)
                            img.thumbnail((target_size, target_size), PILImage.Resampling.LANCZOS)
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='JPEG', quality=95)
                            img_buffer.seek(0)
                            photo_awal = Image(img_buffer, width=20*mm, height=20*mm, kind='proportional')
                    except Exception as e:
                        print(f"Error processing photo_awal for {row.handover_photo}: {e}")
                        photo_awal = '-'

            photo_akhir = '-'
            if row.handover_photo_end:
                # Handle relative path correctly
                photo_path = os.path.join(os.getcwd(), row.handover_photo_end) if row.handover_photo_end.startswith('uploads/') else row.handover_photo_end
                if os.path.exists(photo_path):
                    try:
                        with PILImage.open(photo_path) as img:
                            img = img.convert('RGB')
                            target_size = int(20 * mm * 75 / 25.4)
                            img.thumbnail((target_size, target_size), PILImage.Resampling.LANCZOS)
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='JPEG', quality=95)
                            img_buffer.seek(0)
                            photo_akhir = Image(img_buffer, width=20*mm, height=20*mm, kind='proportional')
                    except Exception as e:
                        print(f"Error processing photo_akhir for {row.handover_photo_end}: {e}")
                        photo_akhir = '-'

            # Add row to table
            table_data.append([
                str(idx),
                formatted_date,
                item_name,
                givers_name,
                givers_name_end,
                givers_position,
                employees_name,
                photo_awal,
                photo_akhir
            ])

        # Define column widths
        colWidths = [15*mm, 30*mm, 30*mm, 30*mm, 30*mm, 30*mm, 30*mm, 25*mm, 25*mm]

        # Create table
        table = Table(table_data, colWidths=colWidths, rowHeights=25*mm)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALTERNATEBACKGROUND', (0, 1), (-1, -1), colors.whitesmoke, 0.5),
            ('LEFTPADDING', (2, 1), (6, -1), 5),
            ('RIGHTPADDING', (2, 1), (6, -1), 5),
            ('BOX', (7, 1), (8, -1), 0.5, colors.black),
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Return PDF file
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"data_serah_terima_{start_date_str}_{end_date_str}.pdf",
            mimetype='application/pdf'
        )

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500

@handover_bp.route('/', methods=['GET'])
def get_handovers():
    try:
        handovers = Handover.query.all()
        result_list = []
        for handover in handovers:
            handover_dict = handover.to_dict()
            handover_dict['handover_date'] = format_date(handover.handover_date)
            handover_dict['handover_date_end'] = format_datetime(handover.handover_date_end)
            result_list.append(handover_dict)
        return jsonify(result_list)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch handovers: {str(e)}"}), 500

@handover_bp.route('/check', methods=['GET'])
def check_handover_entries():
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("tanggal_awal")

    if not start_date:
        return jsonify({"error": "tanggal_awal is required"}), 400

    try:
        parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "tanggal_awal harus dalam format YYYY-MM-DD"}), 400

    if customer_id:
        sql = text("""
            SELECT handover.*, employees.customer_id
            FROM handover
            JOIN employees ON employees.id = handover.id
            WHERE employees.customer_id = :customer_id
              AND DATE(handover.handover_date) = :parsed_date
        """)

        results = db.session.execute(sql, {'customer_id': customer_id, 'parsed_date': parsed_date}).fetchall()

        if results:
            result_list = []
            for result in results:
                result_dict = serialize_result(result)
                result_list.append(result_dict)

            return jsonify(result_list)

    return jsonify({"message": "Tidak Ada Data..."}), 404

@handover_bp.route('/filter', methods=['GET'])
def filter_handover_entries():
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("tanggal_awal")
    end_date = request.args.get("tanggal_akhir")

    if not start_date:
        return jsonify({"error": "tanggal_awal is required"}), 400

    try:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "tanggal_awal harus dalam format YYYY-MM-DD"}), 400

    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            if parsed_end_date < parsed_start_date:
                return jsonify({"error": "tanggal_akhir tidak boleh sebelum tanggal_awal"}), 400
        except ValueError:
            return jsonify({"error": "tanggal_akhir harus dalam format YYYY-MM-DD"}), 400
    else:
        parsed_end_date = parsed_start_date

    if customer_id:
        sql = text("""
            SELECT handover.*
            FROM handover
            JOIN employees ON employees.id = handover.id
            WHERE employees.customer_id = :customer_id
              AND handover.handover_date >= :parsed_start_date
              AND handover.handover_date <= :parsed_end_date
        """)

        result = db.session.execute(sql, {
            'customer_id': customer_id,
            'parsed_start_date': parsed_start_date,
            'parsed_end_date': parsed_end_date
        }).fetchall()

        if result:
            result_list = []
            for row in result:
                result_dict = serialize_result(row)
                result_list.append(result_dict)
            return jsonify(result_list)

    return jsonify({"message": "Tidak Ada Data..."}), 404

@handover_bp.route('/<int:id_handover>', methods=['GET'])
def get_handover_by_id(id_handover):
    try:
        handover = Handover.query.get(id_handover)
        if not handover:
            return jsonify({"error": "Handover entry not found"}), 404

        handover_dict = handover.to_dict()
        handover_dict['handover_date'] = format_date(handover.handover_date)
        handover_dict['handover_date_end'] = format_datetime(handover.handover_date_end)
        return jsonify(handover_dict), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch handover: {str(e)}"}), 500

@handover_bp.route('/', methods=['POST'])
def create_handover():
    try:
        handover_date = request.form.get('handover_date')
        o_clock_handover = request.form.get('o_clock_handover')
        givers_name = request.form.get('givers_name')
        givers_position = request.form.get('givers_position')
        telephone_number_giver = request.form.get('telephone_number_giver')
        id = request.form.get('id')
        address = request.form.get('address')
        telephone_number_recipient = request.form.get('telephone_number_recipient')
        item_name = request.form.get('item_name')
        amount = request.form.get('amount')
        information = request.form.get('information')
        handover_photo = request.files.get('handover_photo')
        status = request.form.get('status')

        if not all([handover_date, o_clock_handover, givers_name, givers_position, telephone_number_giver, id, address, item_name, amount, information]):
            return jsonify({"error": "Missing required fields"}), 400

        filename = secure_filename(handover_photo.filename) if handover_photo else None
        photo_path = os.path.join(UPLOAD_FOLDER, filename) if filename else None
        if photo_path:
            handover_photo.save(photo_path)

        relative_path = f'uploads/{filename}' if filename else None

        handover = Handover(
            handover_date=handover_date,
            o_clock_handover=o_clock_handover,
            givers_name=givers_name,
            givers_position=givers_position,
            telephone_number_giver=telephone_number_giver,
            id=id,
            address=address,
            telephone_number_recipient=telephone_number_recipient,
            item_name=item_name,
            amount=amount,
            information=information,
            handover_photo=relative_path,
            status=status
        )

        db.session.add(handover)
        db.session.commit()
        return jsonify({"message": "Handover entry created successfully!", "handover": handover.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create handover: {str(e)}"}), 500

@handover_bp.route('/mobile', methods=['POST'])
def create_handover_mobile():
    try:
        handover_date = request.form.get('handover_date')
        o_clock_handover = request.form.get('o_clock_handover')
        givers_name = request.form.get('givers_name')
        givers_position = request.form.get('givers_position')
        telephone_number_giver = request.form.get('telephone_number_giver')
        id = request.form.get('id')
        address = request.form.get('address')
        telephone_number_recipient = request.form.get('telephone_number_recipient')
        item_name = request.form.get('item_name')
        amount = request.form.get('amount')
        information = request.form.get('information')
        handover_photo = request.files.get('handover_photo')
        status = request.form.get('status')

        missing_fields = []
        if not handover_date:
            missing_fields.append("handover_date")
        if not o_clock_handover:
            missing_fields.append("o_clock_handover")
        if not givers_name:
            missing_fields.append("givers_name")
        if not givers_position:
            missing_fields.append("givers_position")
        if not telephone_number_giver:
            missing_fields.append("telephone_number_giver")
        if not id:
            missing_fields.append("id")
        if not address:
            missing_fields.append("address")
        if not item_name:
            missing_fields.append("item_name")
        if not amount:
            missing_fields.append("amount")
        if not information:
            missing_fields.append("information")

        if missing_fields:
            return jsonify({"error": "Missing required fields", "missing_fields": missing_fields}), 400

        filename = secure_filename(handover_photo.filename) if handover_photo else None
        photo_path = os.path.join(UPLOAD_FOLDER, filename) if filename else None
        if photo_path:
            handover_photo.save(photo_path)

        relative_path = f'uploads/{filename}' if filename else None

        handover = Handover(
            handover_date=handover_date,
            o_clock_handover=o_clock_handover,
            givers_name=givers_name,
            givers_position=givers_position,
            telephone_number_giver=telephone_number_giver,
            id=id,
            address=address,
            telephone_number_recipient=telephone_number_recipient,
            item_name=item_name,
            amount=amount,
            information=information,
            handover_photo=relative_path,
            status=status
        )

        db.session.add(handover)
        db.session.commit()
        return jsonify({"message": "Handover entry created successfully!", "handover": handover.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create handover: {str(e)}"}), 500

@handover_bp.route('/<int:id_handover>', methods=['PUT'])
def update_handover(id_handover):
    handover = Handover.query.get(id_handover)
    if not handover:
        return jsonify({"error": "Handover entry not found"}), 404

    try:
        if request.content_type.startswith('multipart/form-data'):
            if 'handover_date' in request.form:
                handover.handover_date = request.form['handover_date']
            if 'o_clock_handover' in request.form:
                handover.o_clock_handover = request.form['o_clock_handover']
            if 'givers_name' in request.form:
                handover.givers_name = request.form['givers_name']
            if 'givers_position' in request.form:
                handover.givers_position = request.form['givers_position']
            if 'telephone_number_giver' in request.form:
                handover.telephone_number_giver = request.form['telephone_number_giver']
            if 'id' in request.form:
                handover.id = request.form['id']
            if 'address' in request.form:
                handover.address = request.form['address']
            if 'telephone_number_recipient' in request.form:
                handover.telephone_number_recipient = request.form['telephone_number_recipient']
            if 'item_name' in request.form:
                handover.item_name = request.form['item_name']
            if 'amount' in request.form:
                handover.amount = request.form['amount']
            if 'information' in request.form:
                handover.information = request.form['information']
            if 'status' in request.form:
                handover.status = request.form['status']

            if 'handover_photo' in request.files:
                photo = request.files['handover_photo']
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(UPLOAD_FOLDER, filename)

                if handover.handover_photo and os.path.exists(os.path.join(os.getcwd(), handover.handover_photo)):
                    os.remove(os.path.join(os.getcwd(), handover.handover_photo))

                photo.save(photo_path)
                handover.handover_photo = f"uploads/{filename}"

            if 'handover_photo_end' in request.files:
                photo_end = request.files['handover_photo_end']
                filename_end = secure_filename(photo_end.filename)
                photo_path_end = os.path.join(UPLOAD_FOLDER, filename_end)

                if handover.handover_photo_end and os.path.exists(os.path.join(os.getcwd(), handover.handover_photo_end)):
                    os.remove(os.path.join(os.getcwd(), handover.handover_photo_end))

                photo_end.save(photo_path_end)
                handover.handover_photo_end = f"uploads/{filename_end}"

            if 'handover_date_end' in request.form:
                handover.handover_date_end = request.form['handover_date_end']
            if 'id_user_end' in request.form:
                handover.id_user_end = request.form['id_user_end']
            if 'information_end' in request.form:
                handover.information_end = request.form['information_end']
            if 'givers_name_end' in request.form:
                handover.givers_name_end = request.form['givers_name_end']

        handover.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Handover entry updated successfully!", "handover": handover.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update handover: {str(e)}"}), 500

@handover_bp.route('/<int:id_handover>', methods=['DELETE'])
def delete_handover(id_handover):
    handover = Handover.query.get(id_handover)
    if not handover:
        return jsonify({"error": "Handover entry not found"}), 404

    try:
        if handover.handover_photo and os.path.exists(os.path.join(os.getcwd(), handover.handover_photo)):
            os.remove(os.path.join(os.getcwd(), handover.handover_photo))
        if handover.handover_photo_end and os.path.exists(os.path.join(os.getcwd(), handover.handover_photo_end)):
            os.remove(os.path.join(os.getcwd(), handover.handover_photo_end))

        db.session.delete(handover)
        db.session.commit()
        return jsonify({"message": "Handover entry deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete handover: {str(e)}"}), 500