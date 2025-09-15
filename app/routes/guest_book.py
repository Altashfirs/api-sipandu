import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app.database import db
from app.models.guest_book import GuestBook
from datetime import datetime, timedelta, date
from sqlalchemy.sql import text
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
from PIL import Image as PILImage

guest_book_bp = Blueprint('guest_book', __name__, url_prefix='/api/guest-book')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def format_date(date):
    return date.strftime("%Y-%m-%d") if date else None

def format_table_date(date):
    """Format date for table display in PDF."""
    if not date:
        return "-"
    parsed_date = datetime.strptime(str(date), "%Y-%m-%d") if isinstance(date, str) else date
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{parsed_date.day} {months[parsed_date.month-1]} {parsed_date.year}"

def format_timedelta(td):
    """Convert timedelta to HH:MM:SS string."""
    if not td:
        return "-"
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return str(td)

def serialize_result(result):
    result_dict = dict(result._mapping)
    for key, value in result_dict.items():
        if isinstance(value, datetime):
            result_dict[key] = format_date(value)
        elif isinstance(value, timedelta):
            result_dict[key] = format_timedelta(value)
        elif isinstance(value, date):
            result_dict[key] = format_date(value)
    return result_dict

@guest_book_bp.route('/export_pdf', methods=['GET'])
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
            SELECT guest_book.*, employees.employees_name
            FROM guest_book
            JOIN employees ON employees.id = guest_book.id
            WHERE guest_book.guest_date >= :start_date
              AND guest_book.guest_date <= :end_date
              AND (:customer_id IS NULL OR employees.customer_id = :customer_id)
            ORDER BY guest_book.id_guest DESC
        """)

        # Execute query
        results = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'customer_id': customer_id
        }).fetchall()

        if not results:
            return jsonify({"error": "Tidak ada data tamu"}), 404

        # Prepare PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=20*mm)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        text_style = styles['Normal']
        text_style.fontSize = 7
        text_style.leading = 9
        text_style.wordWrap = 'CJK'

        # Header style for bold text
        header_style = styles['Normal']
        header_style.fontName = 'Helvetica'
        header_style.fontSize = 7
        header_style.leading = 10
        header_style.wordWrap = 'CJK'
        header_style.alignment = 1  # Center alignment

        # Add header
        elements.append(Paragraph(f"Data Buku Tamu: {start_date_str} - {end_date_str}", title_style))
        elements.append(Spacer(1, 10*mm))

        # Build table data with wrapped headers
        table_data = [
            [
                Paragraph('No', header_style),
                Paragraph('Tanggal', header_style),
                Paragraph('Nama', header_style),
                Paragraph('Nomor Identitas', header_style),
                Paragraph('No HP', header_style),
                Paragraph('Asal Perusahaan', header_style),
                Paragraph('Alamat', header_style),
                Paragraph('Tujuan Unit', header_style),
                Paragraph('Keperluan', header_style),
                Paragraph('Jumlah Pengunjung', header_style),
                Paragraph('Jam Masuk', header_style),
                Paragraph('Jam Keluar', header_style),
                Paragraph('Foto', header_style),
                Paragraph('Foto KTP', header_style)
            ]
        ]

        for idx, row in enumerate(results, 1):
            # Prepare text fields with word wrapping
            guest_name = Paragraph(row.guest_name or '-', text_style)
            identity_number = Paragraph(row.identity_number or '-', text_style)
            hp_number = Paragraph(row.hp_number or '-', text_style)
            from_company = Paragraph(row.from_company or '-', text_style)
            address = Paragraph(row.address or '-', text_style)
            unit_goals = Paragraph(row.unit_goals or '-', text_style)
            necessity = Paragraph(row.necessity or '-', text_style)
            visitor_number = Paragraph(str(row.visitor_number) if row.visitor_number else '-', text_style)
            clock_in = Paragraph(format_timedelta(row.clock_in), text_style)
            clock_out = Paragraph(format_timedelta(row.clock_out), text_style)

            # Format date
            formatted_date = format_table_date(row.guest_date)

            # Prepare photo fields
            photo = '-'
            if row.guest_book_photo:
                photo_path = os.path.join(os.getcwd(), row.guest_book_photo) if row.guest_book_photo.startswith('uploads/') else row.guest_book_photo
                if os.path.exists(photo_path):
                    try:
                        with PILImage.open(photo_path) as img:
                            img = img.convert('RGB')
                            target_size = int(20 * mm * 75 / 25.4)  # 75 DPI for 20mm (~118 pixels)
                            img.thumbnail((target_size, target_size), PILImage.Resampling.LANCZOS)
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='JPEG', quality=95)
                            img_buffer.seek(0)
                            photo = Image(img_buffer, width=20*mm, height=20*mm, kind='proportional')
                    except Exception as e:
                        print(f"Error processing guest_book_photo for {row.guest_book_photo}: {e}")
                        photo = '-'

            photo_ktp = '-'
            if row.guest_book_photo_ktp:
                photo_path = os.path.join(os.getcwd(), row.guest_book_photo_ktp) if row.guest_book_photo_ktp.startswith('uploads/') else row.guest_book_photo_ktp
                if os.path.exists(photo_path):
                    try:
                        with PILImage.open(photo_path) as img:
                            img = img.convert('RGB')
                            target_size = int(20 * mm * 75 / 25.4)
                            img.thumbnail((target_size, target_size), PILImage.Resampling.LANCZOS)
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='JPEG', quality=95)
                            img_buffer.seek(0)
                            photo_ktp = Image(img_buffer, width=20*mm, height=20*mm, kind='proportional')
                    except Exception as e:
                        print(f"Error processing guest_book_photo_ktp for {row.guest_book_photo_ktp}: {e}")
                        photo_ktp = '-'

            # Add row to table
            table_data.append([
                str(idx),
                formatted_date,
                guest_name,
                identity_number,
                hp_number,
                from_company,
                address,
                unit_goals,
                necessity,
                visitor_number,
                clock_in,
                clock_out,
                photo,
                photo_ktp
            ])

        # Define column widths (total = 246mm)
        colWidths = [12*mm, 20*mm, 25*mm, 25*mm, 20*mm, 25*mm, 25*mm, 20*mm, 20*mm, 18*mm, 18*mm, 18*mm, 20*mm, 20*mm]

        # Create table
        table = Table(table_data, colWidths=colWidths, rowHeights=20*mm)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALTERNATEBACKGROUND', (0, 1), (-1, -1), colors.whitesmoke, 0.5),
            ('LEFTPADDING', (2, 1), (11, -1), 3),
            ('RIGHTPADDING', (2, 1), (11, -1), 3),
            ('BOX', (12, 1), (13, -1), 0.5, colors.black),
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Return PDF file
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"data_buku_tamu_{start_date_str}_{end_date_str}.pdf",
            mimetype='application/pdf'
        )

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500

@guest_book_bp.route('/', methods=['GET'])
def get_guest_books():
    try:
        guest_books = GuestBook.query.all()
        return jsonify([book.to_dict() for book in guest_books])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch guest books: {str(e)}"}), 500

@guest_book_bp.route('/check', methods=['GET'])
def check_guest_book_entries():
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
            SELECT guest_book.*, employees.customer_id
            FROM guest_book
            JOIN employees ON employees.id = guest_book.id
            WHERE employees.customer_id = :customer_id
              AND DATE(guest_book.guest_date) = :parsed_date
        """)

        results = db.session.execute(sql, {'customer_id': customer_id, 'parsed_date': parsed_date}).fetchall()

        if results:
            result_list = []
            for result in results:
                result_dict = serialize_result(result)
                result_list.append(result_dict)
            return jsonify(result_list)

    return jsonify({"message": "Tidak Ada Data..."}), 404

@guest_book_bp.route('/filter', methods=['GET'])
def filter_guest_book_entries():
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
            SELECT guest_book.*
            FROM guest_book
            JOIN employees ON employees.id = guest_book.id
            WHERE employees.customer_id = :customer_id
              AND guest_book.guest_date >= :parsed_start_date
              AND guest_book.guest_date <= :parsed_end_date
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

@guest_book_bp.route('/<int:id_guest>', methods=['GET'])
def get_guest_book(id_guest):
    try:
        guest_book = GuestBook.query.get(id_guest)
        if guest_book:
            return jsonify(guest_book.to_dict()), 200

        guest_books = GuestBook.query.filter_by(id=id_guest).all()
        if not guest_books:
            return jsonify({"error": "Guest book entry not found for both ID and ID_Guest"}), 404

        return jsonify([guest_book.to_dict() for guest_book in guest_books]), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to fetch guest book: {str(e)}"}), 500

@guest_book_bp.route('/', methods=['POST'])
def create_guest_book():
    try:
        guest_date = request.form.get('guest_date')
        guest_name = request.form.get('guest_name')
        identity_number = request.form.get('identity_number')
        hp_number = request.form.get('hp_number')
        from_company = request.form.get('from_company')
        address = request.form.get('address')
        necessity = request.form.get('necessity')
        visitor_number = request.form.get('visitor_number')
        clock_in = request.form.get('clock_in')
        clock_out = request.form.get('clock_out')
        photo = request.files.get('guest_book_photo')
        photo_ktp = request.files.get('guest_book_photo_ktp')

        if not all([guest_date, guest_name, identity_number, hp_number, from_company, address, necessity, visitor_number, clock_in]):
            return jsonify({"error": "Missing required fields"}), 400

        filename = secure_filename(photo.filename) if photo else None
        photo_path = os.path.join(UPLOAD_FOLDER, filename) if filename else None
        if photo_path:
            photo.save(photo_path)
        relative_path = f'uploads/{filename}' if filename else None

        filename_ktp = secure_filename(photo_ktp.filename) if photo_ktp else None
        photo_ktp_path = os.path.join(UPLOAD_FOLDER, filename_ktp) if filename_ktp else None
        if photo_ktp_path:
            photo_ktp.save(photo_ktp_path)
        relative_path_ktp = f'uploads/{filename_ktp}' if filename_ktp else None

        guest_book = GuestBook(
            guest_date=guest_date,
            guest_name=guest_name,
            identity_number=identity_number,
            hp_number=hp_number,
            from_company=from_company,
            address=address,
            unit_goals=request.form.get('unit_goals'),
            necessity=necessity,
            visitor_number=visitor_number,
            clock_in=clock_in,
            clock_out=clock_out,
            guest_book_photo=relative_path,
            guest_book_photo_ktp=relative_path_ktp
        )

        db.session.add(guest_book)
        db.session.commit()
        return jsonify({"message": "Guest book entry created successfully!", "guest_book": guest_book.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create guest book: {str(e)}"}), 500

@guest_book_bp.route('/<int:id_guest>', methods=['PUT'])
def update_guest_book(id_guest):
    try:
        guest_book = GuestBook.query.get(id_guest)
        if not guest_book:
            return jsonify({"error": "Guest book entry not found"}), 404

        guest_date = request.form.get('guest_date')
        guest_name = request.form.get('guest_name')
        identity_number = request.form.get('identity_number')
        hp_number = request.form.get('hp_number')
        from_company = request.form.get('from_company')
        address = request.form.get('address')
        necessity = request.form.get('necessity')
        visitor_number = request.form.get('visitor_number')
        clock_in = request.form.get('clock_in')
        clock_out = request.form.get('clock_out')
        photo = request.files.get('guest_book_photo')
        photo_ktp = request.files.get('guest_book_photo_ktp')

        if guest_date:
            guest_book.guest_date = guest_date
        if guest_name:
            guest_book.guest_name = guest_name
        if identity_number:
            guest_book.identity_number = identity_number
        if hp_number:
            guest_book.hp_number = hp_number
        if from_company:
            guest_book.from_company = from_company
        if address:
            guest_book.address = address
        if necessity:
            guest_book.necessity = necessity
        if visitor_number:
            guest_book.visitor_number = visitor_number
        if clock_in:
            guest_book.clock_in = clock_in
        if clock_out:
            guest_book.clock_out = clock_out

        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            if guest_book.guest_book_photo and os.path.exists(os.path.join(os.getcwd(), guest_book.guest_book_photo)):
                os.remove(os.path.join(os.getcwd(), guest_book.guest_book_photo))
            photo.save(photo_path)
            guest_book.guest_book_photo = f'uploads/{filename}'

        if photo_ktp:
            filename_ktp = secure_filename(photo_ktp.filename)
            photo_ktp_path = os.path.join(UPLOAD_FOLDER, filename_ktp)
            if guest_book.guest_book_photo_ktp and os.path.exists(os.path.join(os.getcwd(), guest_book.guest_book_photo_ktp)):
                os.remove(os.path.join(os.getcwd(), guest_book.guest_book_photo_ktp))
            photo_ktp.save(photo_ktp_path)
            guest_book.guest_book_photo_ktp = f'uploads/{filename_ktp}'

        guest_book.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Guest book entry updated successfully!", "guest_book": guest_book.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update guest book: {str(e)}"}), 500

@guest_book_bp.route('/create_mobile', methods=['POST'])
def create_guest_book_mobile():
    try:
        id = request.form.get('employees_id')
        guest_date = request.form.get('guest_date')
        guest_name = request.form.get('guest_name')
        identity_number = request.form.get('identity_number')
        hp_number = request.form.get('hp_number')
        from_company = request.form.get('from_company')
        address = request.form.get('address')
        necessity = request.form.get('necessity')
        visitor_number = request.form.get('visitor_number')
        clock_in = request.form.get('clock_in')
        photo = request.files.get('guest_book_photo')
        photo_ktp = request.files.get('guest_book_photo_ktp')

        if not all([guest_date, guest_name, identity_number, hp_number, from_company, address, necessity, visitor_number, clock_in]):
            return jsonify({"error": "Missing required fields"}), 400

        filename = secure_filename(photo.filename) if photo else None
        photo_path = os.path.join(UPLOAD_FOLDER, filename) if filename else None
        if photo_path:
            photo.save(photo_path)
        relative_path = f'uploads/{filename}' if filename else None

        filename_ktp = secure_filename(photo_ktp.filename) if photo_ktp else None
        photo_ktp_path = os.path.join(UPLOAD_FOLDER, filename_ktp) if filename_ktp else None
        if photo_ktp_path:
            photo_ktp.save(photo_ktp_path)
        relative_path_ktp = f'uploads/{filename_ktp}' if filename_ktp else None

        guest_book = GuestBook(
            id=id,
            guest_date=guest_date,
            guest_name=guest_name,
            identity_number=identity_number,
            hp_number=hp_number,
            from_company=from_company,
            address=address,
            unit_goals=request.form.get('unit_goals'),
            necessity=necessity,
            visitor_number=visitor_number,
            clock_in=clock_in,
            guest_book_photo=relative_path,
            guest_book_photo_ktp=relative_path_ktp
        )

        db.session.add(guest_book)
        db.session.commit()
        return jsonify({"message": "Guest book entry created successfully!", "guest_book": guest_book.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create guest book: {str(e)}"}), 500

@guest_book_bp.route('/update_mobile/<int:id_guest>', methods=['PUT'])
def update_guest_book_mobile(id_guest):
    try:
        guest_book = GuestBook.query.get(id_guest)
        if not guest_book:
            return jsonify({"error": "Guest book entry not found"}), 404

        id = request.form.get('employees_id')
        guest_date = request.form.get('guest_date')
        guest_name = request.form.get('guest_name')
        identity_number = request.form.get('identity_number')
        hp_number = request.form.get('hp_number')
        from_company = request.form.get('from_company')
        address = request.form.get('address')
        necessity = request.form.get('necessity')
        visitor_number = request.form.get('visitor_number')
        clock_in = request.form.get('clock_in')
        clock_out = request.form.get('clock_out')
        photo = request.files.get('guest_book_photo')
        photo_ktp = request.files.get('guest_book_photo_ktp')

        if id:
            guest_book.id = id
        if guest_date:
            guest_book.guest_date = guest_date
        if guest_name:
            guest_book.guest_name = guest_name
        if identity_number:
            guest_book.identity_number = identity_number
        if hp_number:
            guest_book.hp_number = hp_number
        if from_company:
            guest_book.from_company = from_company
        if address:
            guest_book.address = address
        if necessity:
            guest_book.necessity = necessity
        if visitor_number:
            guest_book.visitor_number = visitor_number
        if clock_in:
            guest_book.clock_in = clock_in
        if clock_out:
            guest_book.clock_out = clock_out

        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            if guest_book.guest_book_photo and os.path.exists(os.path.join(os.getcwd(), guest_book.guest_book_photo)):
                os.remove(os.path.join(os.getcwd(), guest_book.guest_book_photo))
            photo.save(photo_path)
            guest_book.guest_book_photo = f'uploads/{filename}'

        if photo_ktp:
            filename_ktp = secure_filename(photo_ktp.filename)
            photo_ktp_path = os.path.join(UPLOAD_FOLDER, filename_ktp)
            if guest_book.guest_book_photo_ktp and os.path.exists(os.path.join(os.getcwd(), guest_book.guest_book_photo_ktp)):
                os.remove(os.path.join(os.getcwd(), guest_book.guest_book_photo_ktp))
            photo_ktp.save(photo_ktp_path)
            guest_book.guest_book_photo_ktp = f'uploads/{filename_ktp}'

        guest_book.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Guest book entry updated successfully!", "guest_book": guest_book.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update guest book: {str(e)}"}), 500

@guest_book_bp.route('/<int:id_guest>', methods=['DELETE'])
def delete_guest_book(id_guest):
    guest_book = GuestBook.query.get(id_guest)
    if not guest_book:
        return jsonify({"error": "Guest book entry not found"}), 404

    try:
        if guest_book.guest_book_photo and os.path.exists(os.path.join(os.getcwd(), guest_book.guest_book_photo)):
            os.remove(os.path.join(os.getcwd(), guest_book.guest_book_photo))
        if guest_book.guest_book_photo_ktp and os.path.exists(os.path.join(os.getcwd(), guest_book.guest_book_photo_ktp)):
            os.remove(os.path.join(os.getcwd(), guest_book.guest_book_photo_ktp))

        db.session.delete(guest_book)
        db.session.commit()
        return jsonify({"message": "Guest book entry deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete guest book: {str(e)}"}), 500