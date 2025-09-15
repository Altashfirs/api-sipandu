from flask import Blueprint, jsonify, request, make_response
from app.database import db
from app.models.journal_book import JournalBook
from app.models.employees import Employee
from app.models.shift import Shift
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm  # Import mm for unit conversion
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, KeepTogether, Paragraph, Image
from PIL import Image as PILImage
import csv
from datetime import datetime, timedelta
from sqlalchemy.sql import text
from werkzeug.utils import secure_filename
import os

journal_book_bp = Blueprint('journal_book', __name__, url_prefix='/api/journal_book')

# Pastikan folder uploads ada
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@journal_book_bp.route('/export', methods=['GET'])
def export_journal_entries():
    month = request.args.get("from")
    year = request.args.get("to")
    customer_id = request.args.get("customer_id")

    # Validasi input
    if month is None or year is None or customer_id is None:
        return jsonify({"error": "Semua parameter harus diisi."}), 400

    if not month.isdigit() or not (1 <= int(month) <= 12):
        return jsonify({"error": "Bulan harus berupa angka antara 1 dan 12."}), 400
    if not year.isdigit():
        return jsonify({"error": "Tahun harus berupa angka."}), 400
    if not customer_id.isdigit():
        return jsonify({"error": "Customer ID harus berupa angka."}), 400

    query = JournalBook.query
    query = query.filter(db.extract('month', JournalBook.journal_date) == int(month))
    query = query.filter(db.extract('year', JournalBook.journal_date) == int(year))
    query = query.join(Employee).filter(Employee.customer_id == int(customer_id))
    query = query.join(Shift, JournalBook.shift_id == Shift.shift_id)  # Join dengan tabel Shift

    try:
        journal_entries = query.all()
        if not journal_entries:
            return jsonify({"message": "Tidak ada entri jurnal ditemukan."}), 404

        # Buat PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []

        # Definisikan gaya paragraf untuk wrapping text
        para_style = ParagraphStyle(
            name='Normal',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            wordWrap='CJK'
        )

        # Tentukan path ke folder uploads
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..', 'uploads')

        # Data untuk tabel
        data = [['No', 'Tanggal', 'Shift', 'Nama Petugas', 'Jam', 'Deskripsi Kejadian', 'Keterangan', 'Foto']]
        for index, entry in enumerate(journal_entries, start=1):
            # Gunakan Paragraph untuk kolom dengan teks panjang
            incident_desc = Paragraph(entry.incident_description or '-', para_style)
            info = Paragraph(entry.information or '-', para_style)

            # Ambil nama shift dari relasi Shift
            shift_name = Paragraph(entry.employee.shift.shift_name if entry.employee and entry.employee.shift else '-', para_style)

            # Ambil nama petugas dari relasi Employee
            employee_name = Paragraph(entry.employee.employees_name if entry.employee else '-', para_style)

            # Handle foto
            photo = '-'
            if entry.journal_book_photo:
                # Normalisasi path, ambil hanya nama file
                photo_filename = os.path.basename(entry.journal_book_photo)
                photo_path = os.path.join(upload_folder, photo_filename)

                if os.path.exists(photo_path):
                    try:
                        with PILImage.open(photo_path) as img:
                            img = img.convert('RGB')  # Convert to RGB for compatibility
                            img_buffer = BytesIO()
                            img.thumbnail((12*mm, 12*mm), PILImage.Resampling.LANCZOS)  # Resize to fit column
                            img.save(img_buffer, format='JPEG')
                            img_buffer.seek(0)
                            photo = Image(img_buffer, width=12*mm, height=12*mm)
                            photo.hAlign = 'CENTER'
                    except Exception as e:
                        photo = '-'
                else:
                    photo = '-'

            data.append([
                str(index),  # Kolom No
                str(entry.journal_date) if entry.journal_date else '-',  # Kolom Tanggal
                shift_name,  # Kolom Shift (menggunakan shift_name dari model Shift)
                employee_name,  # Kolom Nama Petugas (menggunakan employees_name dari model Employee)
                str(entry.o_clock) if entry.o_clock else '-',  # Kolom Jam
                incident_desc,  # Kolom Deskripsi Kejadian
                info,  # Kolom Keterangan
                photo  # Kolom Foto
            ])

        # Tentukan lebar kolom (total ~535 points untuk A4 dengan margin)
        col_widths = [30, 80, 60, 80, 50, 100, 100, 35]

        # Buat tabel
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('ALIGN', (5, 1), (6, -1), 'LEFT'),
            ('VALIGN', (7, 1), (7, -1), 'MIDDLE'),
        ]))

        elements.append(KeepTogether(table))
        doc.build(elements)

        # Siapkan respons PDF
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=journal_entries_{year}_{month}.pdf'
        return response

    except Exception as e:
        return jsonify({"error": f"Gagal mengambil data atau membuat PDF: {str(e)}"}), 500
        
@journal_book_bp.route('/', methods=['GET'])
def get_all_journal_entries():
    journal_entries = JournalBook.query.order_by(JournalBook.id_journal.desc()).all()
    
    # Format journal_date ke YYYY-MM-DD
    formatted_entries = []
    for entry in journal_entries:
        entry_dict = entry.to_dict()
        if entry_dict.get("journal_date"):
            # Konversi string ke datetime
            try:
                journal_date_obj = datetime.strptime(entry_dict["journal_date"], "%Y-%m-%d")
                # Ubah format journal_date ke YYYY-MM-DD
                entry_dict["journal_date"] = journal_date_obj.strftime("%Y-%m-%d")
            except ValueError:
                # Jika format tanggal tidak valid, lewati atau beri nilai default
                entry_dict["journal_date"] = "Invalid date"
        formatted_entries.append(entry_dict)
    
    return jsonify(formatted_entries)

@journal_book_bp.route('/<int:id_journal>', methods=['GET'])
def get_journal_entry_by_id(id_journal):
    journal_entry = JournalBook.query.get(id_journal)
    if not journal_entry:
        return jsonify({"error": "Journal entry not found"}), 404

    # Format journal_date ke YYYY-MM-DD
    entry_dict = journal_entry.to_dict()
    if entry_dict.get("journal_date"):
        # Konversi string ke datetime
        try:
            journal_date_obj = datetime.strptime(entry_dict["journal_date"], "%Y-%m-%d")
            # Ubah format journal_date ke YYYY-MM-DD
            entry_dict["journal_date"] = journal_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # Jika format tanggal tidak valid, lewati atau beri nilai default
            entry_dict["journal_date"] = "Invalid date"
    
    return jsonify(entry_dict)

# @journal_book_bp.route('/check', methods=['GET'])  
# def check_journal_entries():  
#     employee_id = request.args.get("employee_id")  
#     customer_id = request.args.get("customer_id")
#     start_date = request.args.get("tanggal_awal")  
    
#     if not start_date:
#         return jsonify({"error": "tanggal_awal is required"}), 400  

#     try:
#         parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#     except ValueError:
#         return jsonify({"error": "tanggal_awal harus dalam format YYYY-MM-DD"}), 400

#     # Cek berdasarkan employee_id
#     if employee_id:
#         employee_entry = JournalBook.query.filter_by(id=employee_id).filter(
#             db.func.date(JournalBook.journal_date) == parsed_date
#         ).first()

#         if employee_entry:
#             return jsonify(employee_entry.to_dict())

#     # Jika employee_id tidak ditemukan, cek customer_id
#     if customer_id:
#         sql = text("""
#             SELECT journal_book.*, employees.customer_id
#             FROM journal_book
#             JOIN employees ON employees.id = journal_book.id
#             WHERE employees.customer_id = :customer_id
#               AND DATE(journal_book.journal_date) = :parsed_date
#         """)  # Wrap query in text()
        
#         result = db.session.execute(sql, {'customer_id': customer_id, 'parsed_date': parsed_date}).fetchone()

#         if result:
#             # Konversi result ke dictionary
#             result_dict = dict(result._mapping)

#             # Tangani tipe data yang tidak bisa di-serialize
#             for key, value in result_dict.items():
#                 if isinstance(value, datetime):
#                     result_dict[key] = value.isoformat()  # Ubah datetime ke string ISO
#                 elif isinstance(value, timedelta):
#                     result_dict[key] = str(value)  # Ubah timedelta ke string

#             return jsonify(result_dict)

#     return jsonify({"message": "Tidak Ada Data..."}), 404

@journal_book_bp.route('/check', methods=['GET'])
def check_journal_entries():
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("tanggal_awal")

    if not start_date:
        return jsonify({"error": "tanggal_awal is required"}), 400

    try:
        parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "tanggal_awal harus dalam format YYYY-MM-DD"}), 400

    # Cek berdasarkan customer_id
    if customer_id:
        sql = text("""
            SELECT journal_book.*, employees.customer_id
            FROM journal_book
            JOIN employees ON employees.id = journal_book.id
            WHERE employees.customer_id = :customer_id
              AND DATE(journal_book.journal_date) = :parsed_date
        """)  # Wrap query in text()

        results = db.session.execute(sql, {'customer_id': customer_id, 'parsed_date': parsed_date}).fetchall()  # Ambil semua data

        if results:
            # Konversi hasil ke list of dictionaries
            result_list = []
            for result in results:
                result_dict = dict(result._mapping)

                # Format journal_date ke YYYY-MM-DD
                if "journal_date" in result_dict and result_dict["journal_date"]:
                    result_dict["journal_date"] = result_dict["journal_date"].strftime("%Y-%m-%d")

                # Tangani tipe data yang tidak bisa di-serialize
                for key, value in result_dict.items():
                    if isinstance(value, timedelta):
                        result_dict[key] = str(value)  # Ubah timedelta ke string

                result_list.append(result_dict)

            return jsonify(result_list)  # Kembalikan list of dictionaries

    return jsonify({"message": "Tidak Ada Data..."}), 404 
    
@journal_book_bp.route('/filter', methods=['GET'])
def filter_journal_entries():
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("tanggal_awal")
    end_date = request.args.get("tanggal_akhir")

    if not start_date:
        return jsonify({"error": "tanggal_awal is required"}), 400

    try:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "tanggal_awal harus dalam format YYYY-MM-DD"}), 400

    # Validate and parse end_date if provided
    if end_date:
        try:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            if parsed_end_date < parsed_start_date:
                return jsonify({"error": "tanggal_akhir tidak boleh sebelum tanggal_awal"}), 400
        except ValueError:
            return jsonify({"error": "tanggal_akhir harus dalam format YYYY-MM-DD"}), 400
    else:
        parsed_end_date = parsed_start_date  # Default to start date if no end date provided

    # Check based on customer_id
    if customer_id:
        sql = text("""
            SELECT journal_book.*
            FROM journal_book
            JOIN employees ON employees.id = journal_book.id
            WHERE employees.customer_id = :customer_id
              AND journal_book.journal_date >= :parsed_start_date
              AND journal_book.journal_date <= :parsed_end_date
        """)

        result = db.session.execute(sql, {
            'customer_id': customer_id,
            'parsed_start_date': parsed_start_date,
            'parsed_end_date': parsed_end_date
        }).fetchall()

        if result:
            # Convert result to a list of dictionaries
            result_list = []
            for row in result:
                result_dict = dict(row._mapping)

                # Format journal_date ke YYYY-MM-DD
                if "journal_date" in result_dict and result_dict["journal_date"]:
                    result_dict["journal_date"] = result_dict["journal_date"].strftime("%Y-%m-%d")

                # Tangani tipe data yang tidak bisa di-serialize
                for key, value in result_dict.items():
                    if isinstance(value, timedelta):
                        result_dict[key] = str(value)  # Ubah timedelta ke string

                result_list.append(result_dict)
            return jsonify(result_list)

    # If no entries found for customer_id
    return jsonify({"message": "Tidak Ada Data..."}), 404   

@journal_book_bp.route('/', methods=['POST'])
def create_journal_entry():
    try:
        # Ambil data dari form (bukan JSON)
        journal_date = request.form.get('journal_date')
        shift_id = request.form.get('shift_id')
        employee_id = request.form.get('employee_id')
        o_clock = request.form.get('o_clock')
        incident_description = request.form.get('incident_description')
        information = request.form.get('information')
        photo = request.files.get('journal_book_photo')

        # Validasi field wajib
        required_fields = {
            "journal_date": "Harap mengisi tanggal",
            "shift_id": "Harap mengisi shift",
            "employee_id": "Harap mengisi ID karyawan",
            "o_clock": "Harap mengisi jam",
            "incident_description": "Harap mengisi deskripsi kejadian",
            "information": "Harap mengisi informasi"
        }
        for field, message in required_fields.items():
            if not locals().get(field):
                return jsonify({"error": message}), 400

        # Handle upload foto
        filename = secure_filename(photo.filename) if photo else None
        photo_path = os.path.join(UPLOAD_FOLDER, filename) if filename else None
        if photo_path:
            photo.save(photo_path)
        relative_path = f'uploads/{filename}' if filename else None

        # Buat entry journal
        journal_entry = JournalBook(
            journal_date=journal_date,
            shift_id=shift_id,
            id=employee_id,
            o_clock=o_clock,
            incident_description=incident_description,
            information=information,
            journal_book_photo=relative_path
        )
        db.session.add(journal_entry)
        db.session.commit()
        return jsonify({"message": "Journal entry created successfully!", "journal_entry": journal_entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create journal entry: {str(e)}"}), 500

@journal_book_bp.route('/<int:id_journal>', methods=['PUT'])
def update_journal_entry(id_journal):
    try:
        journal_entry = JournalBook.query.get(id_journal)
        if not journal_entry:
            return jsonify({"error": "Journal entry not found"}), 404

        # Ambil data dari form
        journal_date = request.form.get('journal_date')
        shift_id = request.form.get('shift_id')
        employee_id = request.form.get('employee_id')
        o_clock = request.form.get('o_clock')
        incident_description = request.form.get('incident_description')
        information = request.form.get('information')
        photo = request.files.get('journal_book_photo')

        # Update field yang dikirim
        if journal_date:
            journal_entry.journal_date = journal_date
        if shift_id:
            journal_entry.shift_id = shift_id
        if employee_id:
            journal_entry.id = employee_id
        if o_clock:
            journal_entry.o_clock = o_clock
        if incident_description:
            journal_entry.incident_description = incident_description
        if information:
            journal_entry.information = information

        # Handle update foto
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            # Hapus foto lama kalau ada
            if journal_entry.journal_book_photo and os.path.exists(os.path.join(os.getcwd(), journal_entry.journal_book_photo)):
                os.remove(os.path.join(os.getcwd(), journal_entry.journal_book_photo))
            photo.save(photo_path)
            journal_entry.journal_book_photo = f'uploads/{filename}'

        db.session.commit()
        return jsonify({"message": "Journal entry updated successfully!", "journal_entry": journal_entry.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update journal entry: {str(e)}"}), 500

@journal_book_bp.route('/create_mobile', methods=['POST'])
def create_journal_entry_mobile():
    try:
        # Ambil data dari form
        journal_date = request.form.get('journal_date')
        shift_id = request.form.get('shift_id')
        employee_id = request.form.get('employee_id')
        o_clock = request.form.get('o_clock')
        incident_description = request.form.get('incident_description')
        information = request.form.get('information')
        photo = request.files.get('journal_book_photo')

        # Validasi field wajib
        required_fields = {
            "journal_date": "Harap mengisi tanggal",
            "shift_id": "Harap mengisi shift",
            "employee_id": "Harap mengisi ID karyawan",
            "o_clock": "Harap mengisi jam",
            "incident_description": "Harap mengisi deskripsi kejadian",
            "information": "Harap mengisi informasi"
        }
        for field, message in required_fields.items():
            if not locals().get(field):
                return jsonify({"error": message}), 400

        # Handle upload foto
        filename = secure_filename(photo.filename) if photo else None
        photo_path = os.path.join(UPLOAD_FOLDER, filename) if filename else None
        if photo_path:
            photo.save(photo_path)
        relative_path = f'uploads/{filename}' if filename else None

        # Buat entry journal
        journal_entry = JournalBook(
            journal_date=journal_date,
            shift_id=shift_id,
            id=employee_id,
            o_clock=o_clock,
            incident_description=incident_description,
            information=information,
            journal_book_photo=relative_path
        )
        db.session.add(journal_entry)
        db.session.commit()
        return jsonify({"message": "Journal entry created successfully!", "journal_entry": journal_entry.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create journal entry: {str(e)}"}), 500

@journal_book_bp.route('/update_mobile/<int:id_journal>', methods=['PUT'])
def update_journal_entry_mobile(id_journal):
    try:
        journal_entry = JournalBook.query.get(id_journal)
        if not journal_entry:
            return jsonify({"error": "Journal entry not found"}), 404

        # Ambil data dari form
        journal_date = request.form.get('journal_date')
        shift_id = request.form.get('shift_id')
        employee_id = request.form.get('employee_id')
        o_clock = request.form.get('o_clock')
        incident_description = request.form.get('incident_description')
        information = request.form.get('information')
        photo = request.files.get('journal_book_photo')

        # Update field yang dikirim
        if journal_date:
            journal_entry.journal_date = journal_date
        if shift_id:
            journal_entry.shift_id = shift_id
        if employee_id:
            journal_entry.id = employee_id
        if o_clock:
            journal_entry.o_clock = o_clock
        if incident_description:
            journal_entry.incident_description = incident_description
        if information:
            journal_entry.information = information

        # Handle update foto
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)
            # Hapus foto lama kalau ada
            if journal_entry.journal_book_photo and os.path.exists(os.path.join(os.getcwd(), journal_entry.journal_book_photo)):
                os.remove(os.path.join(os.getcwd(), journal_entry.journal_book_photo))
            photo.save(photo_path)
            journal_entry.journal_book_photo = f'uploads/{filename}'

        db.session.commit()
        return jsonify({"message": "Journal entry updated successfully!", "journal_entry": journal_entry.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update journal entry: {str(e)}"}), 500

@journal_book_bp.route('/<int:id_journal>', methods=['DELETE'])
def delete_journal_entry(id_journal):
    journal_entry = JournalBook.query.get(id_journal)
    if not journal_entry:
        return jsonify({"error": "Journal entry not found"}), 404

    try:
        # Hapus foto kalau ada
        if journal_entry.journal_book_photo and os.path.exists(os.path.join(os.getcwd(), journal_entry.journal_book_photo)):
            os.remove(os.path.join(os.getcwd(), journal_entry.journal_book_photo))

        db.session.delete(journal_entry)
        db.session.commit()
        return jsonify({"message": "Journal entry deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete journal entry: {str(e)}"}), 500