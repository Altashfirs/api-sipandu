from flask import Blueprint, request, jsonify, send_file
from app.database import db
from app.models.start_test import StartTest
from app.models.employees import Employee
from app.models.position import Position
from app.models.customers import Customer
from app.models.question import Question
from app.models.results_test import ResultsTest
from app.models.matrix import Matrix
from datetime import datetime, timedelta
import pytz
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
import os
import json
from werkzeug.utils import secure_filename
from PIL import Image as PILImage

start_test_bp = Blueprint('start_test', __name__, url_prefix='/api/start-tests')

# Timezone untuk Asia/Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

# Setup folder upload
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
@start_test_bp.route('/', methods=['GET'])
def get_start_tests():
    try:
        tests = StartTest.query.all()
        return jsonify([test.to_dict() for test in tests]), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch tests: {str(e)}"}), 500

@start_test_bp.route('/<int:id_test>', methods=['GET'])
def get_start_test_by_id(id_test):
    try:
        test = StartTest.query.get(id_test)
        if not test:
            return jsonify({"error": "Test not found"}), 404
        return jsonify(test.to_dict()), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch test: {str(e)}"}), 500

@start_test_bp.route('/employees/<int:id_employees>', methods=['GET'])  
def get_tests_by_employee_id(id_employees):  
    try:  
        tests = StartTest.query.filter_by(id_employees=id_employees).all()  
        if not tests:  
            return jsonify({"error": "No tests found for this employee"}), 404  
        return jsonify([test.to_dict() for test in tests]), 200  
    except Exception as e:  
        return jsonify({"error": f"Failed to fetch tests: {str(e)}"}), 500  
        
@start_test_bp.route('/', methods=['POST'])
def create_start_test():
    try:
        data = request.get_json()
        new_test = StartTest(
            test_date=data.get('test_date'),
            id_examiner=data.get('id_examiner'),
            id_employees=data.get('id_employees'),
            id_admin=data.get('id_admin'),
            status_test=data.get('status_test'),
            id_matrix=data.get('id_matrix'),
            created_at=datetime.now(jakarta_tz)
        )
        db.session.add(new_test)
        db.session.commit()
        return jsonify({
            "message": "Test created successfully!",
            "id_test": new_test.id_test,
            "test": new_test.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create test: {str(e)}"}), 500

@start_test_bp.route('/<int:id_test>', methods=['PUT'])
def update_start_test(id_test):
    try:
        test = StartTest.query.get(id_test)
        if not test:
            return jsonify({"error": "Test not found"}), 404
        data = request.get_json()
        test.test_date = data.get('test_date', test.test_date)
        test.id_examiner = data.get('id_examiner', test.id_examiner)
        test.id_employees = data.get('id_employees', test.id_employees)
        test.id_admin = data.get('id_admin', test.id_admin)
        test.status_test = data.get('status_test', test.status_test)
        test.id_matrix = data.get('id_matrix', test.id_matrix)
        test.updated_at = datetime.now(jakarta_tz)
        db.session.commit()
        return jsonify({"message": "Test updated successfully!", "test": test.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update test: {str(e)}"}), 500

@start_test_bp.route('/<int:id_test>', methods=['DELETE'])
def delete_start_test(id_test):
    try:
        test = StartTest.query.get(id_test)
        if not test:
            return jsonify({"error": "Test not found"}), 404
        db.session.delete(test)
        db.session.commit()
        return jsonify({"message": "Test deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete test: {str(e)}"}), 500

@start_test_bp.route('/mobile', methods=['POST'])
def create_start_test_mobile():
    try:
        # Ambil data dari form dan file
        data = request.form
        files = request.files.getlist('dokumentasi')  # Ambil daftar file

        # Validasi field wajib
        required_fields = ['test_date', 'id_examiner', 'id']
        if not all(data.get(field) for field in required_fields):
            return jsonify({"error": "Field wajib (test_date, id_examiner, id) harus diisi"}), 400

        # Validasi minimal satu file dokumentasi
        if not files or all(not file.filename for file in files):
            return jsonify({"error": "Minimal satu file dokumentasi harus diunggah"}), 400

        # Proses file yang diunggah
        filenames = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                filenames.append(f'uploads/{filename}')

        # Buat entri baru di tabel start_test
        new_test = StartTest(
            test_date=data.get('test_date'),
            id_examiner=data.get('id_examiner'),
            id_employees=data.get('id_employees'),
            id_admin=data.get('id_admin'),
            status_test=data.get('status_test'),
            id_matrix=data.get('id_matrix'),
            dokumentasi=json.dumps(filenames),  # Simpan daftar nama file sebagai JSON
            created_at=datetime.now(jakarta_tz)
        )
        db.session.add(new_test)
        db.session.commit()
        return jsonify({
            "message": "Test berhasil dibuat!",
            "id_test": new_test.id_test,
            "test": new_test.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal membuat test: {str(e)}"}), 500

@start_test_bp.route('/mobile/<int:id_test>', methods=['PUT'])
def update_start_test_mobile(id_test):
    try:
        test = StartTest.query.get(id_test)
        if not test:
            return jsonify({"error": "Test tidak ditemukan"}), 404

        # Ambil data dari form dan file
        data = request.form
        files = request.files.getlist('dokumentasi')  # Ambil daftar file baru

        # Update field non-file jika ada
        test.test_date = data.get('test_date', test.test_date)
        test.id_examiner = data.get('id_examiner', test.id_examiner)
        test.id_employees = data.get('id_employees', test.id_employees)
        test.id_admin = data.get('id_admin', test.id_admin)
        test.status_test = data.get('status_test', test.status_test)
        test.id_matrix = data.get('id_matrix', test.id_matrix)

        # Proses file dokumentasi jika ada file baru
        if files and any(file.filename for file in files):
            # Ambil daftar file lama
            existing_filenames = json.loads(test.dokumentasi) if test.dokumentasi else []

            # Hapus file lama dari disk
            for old_file in existing_filenames:
                file_path = os.path.join(os.getcwd(), old_file)
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Simpan file baru
            new_filenames = []
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    new_filenames.append(f'uploads/{filename}')

            # Update kolom dokumentasi
            test.dokumentasi = json.dumps(new_filenames)

        test.updated_at = datetime.now(jakarta_tz)
        db.session.commit()
        return jsonify({"message": "Test berhasil diperbarui!", "test": test.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal memperbarui test: {str(e)}"}), 500

@start_test_bp.route('/mobile/<int:id_test>', methods=['DELETE'])
def delete_start_test_mobile(id_test):
    try:
        test = StartTest.query.get(id_test)
        if not test:
            return jsonify({"error": "Test tidak ditemukan"}), 404

        # Hapus file terkait jika ada
        if test.dokumentasi:
            filenames = json.loads(test.dokumentasi)
            for filename in filenames:
                file_path = os.path.join(os.getcwd(), filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

        db.session.delete(test)
        db.session.commit()
        return jsonify({"message": "Test berhasil dihapus!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Gagal menghapus test: {str(e)}"}), 500


@start_test_bp.route('/export_pdf', methods=['GET'])
def export_pdf():
    """
    Export test data as a PDF report, grouped by employee and customer, with each combination on a new page.
    Within each employee-customer combination, each new date starts on a new page.
    Columns: No, Tanggal, Nama, Level, Nilai, Dokumentasi.
    Filterable by employee_id, customer_id, tanggal_awal, and tanggal_akhir.
    All text columns are wrapped with Paragraph for word wrapping.
    Dokumentasi column displays the first image from the dokumentasi JSON array.
    """
    try:
        # Ambil parameter filter
        employee_id = request.args.get('employee_id', type=int)
        customer_id = request.args.get('customer_id', type=int)
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')

        # Tentukan tanggal default: 1 bulan ke belakang hingga hari ini
        today = datetime.now(jakarta_tz).date()
        last_month = today - timedelta(days=30)

        # Gunakan tanggal default jika parameter kosong
        try:
            start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d').date() if tanggal_awal else last_month
            end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d').date() if tanggal_akhir else today
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Validasi tanggal
        if start_date > end_date:
            return jsonify({"error": "tanggal_awal cannot be after tanggal_akhir"}), 400

        # Format tanggal untuk nama file dan header
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Query data dengan join ke tabel terkait
        query = db.session.query(
            StartTest, Employee, Position, Customer, Matrix
        ).join(
            Employee, StartTest.id_employees == Employee.id
        ).join(
            Position, Employee.position_id == Position.position_id
        ).join(
            Customer, Employee.customer_id == Customer.customer_id
        ).join(
            Matrix, StartTest.id_matrix == Matrix.matrix_id
        ).filter(
            StartTest.test_date >= start_date,
            StartTest.test_date <= end_date
        )

        # Tambahkan filter employee_id jika ada
        if employee_id:
            query = query.filter(StartTest.id_employees == employee_id)

        # Tambahkan filter customer_id jika ada
        if customer_id:
            query = query.filter(Customer.customer_id == customer_id)

        # Urutkan berdasarkan customer_id, employee_id, test_date, dan id_test
        tests = query.order_by(Customer.customer_id, StartTest.id_employees, StartTest.test_date, StartTest.id_test).all()

        if not tests:
            return jsonify({"error": "Tidak ada data..."}), 404

        # Kelompokkan data per customer dan employee, lalu per tanggal
        customer_employee_tests = defaultdict(lambda: defaultdict(list))
        for test, employee, position, customer, matrix in tests:
            customer_employee_tests[customer.customer_id][employee.id].append((test, employee, position, customer, matrix))

        # Buat PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        normal_style = styles['Normal']
        normal_style.fontSize = 8
        normal_style.leading = 10
        normal_style.wordWrap = 'CJK'  # Enable word wrapping for all text columns

        # Iterasi per customer
        for cust_id, employee_data in customer_employee_tests.items():
            customer = None
            # Iterasi per employee
            for emp_id, test_data in employee_data.items():
                employee = test_data[0][1]
                position = test_data[0][2]
                customer = test_data[0][3]

                # Kelompokkan data per tanggal
                tests_by_date = defaultdict(list)
                for test, emp, pos, cust, matrix in test_data:
                    test_date = test.test_date.strftime('%Y-%m-%d') if test.test_date else "Unknown"
                    tests_by_date[test_date].append((test, emp, pos, cust, matrix))

                # Iterasi per tanggal
                for date_idx, (test_date, date_tests) in enumerate(tests_by_date.items()):
                    # Tambahkan header informasi untuk kombinasi customer-employee
                    if date_idx == 0:
                        elements.append(Paragraph(f"Tanggal: {start_date_str} - {end_date_str}", title_style))
                        elements.append(Paragraph(f"Perusahaan: {customer.name}", normal_style))
                        elements.append(Paragraph(f"Nama: {employee.employees_name}", normal_style))
                        elements.append(Paragraph(f"Jabatan: {position.position_name}", normal_style))
                        elements.append(Spacer(1, 10*mm))

                    # Tambahkan subheader tanggal
                    elements.append(Paragraph(f"Tanggal Test: {test_date}", title_style))
                    elements.append(Spacer(1, 5*mm))

                    # Buat tabel data test untuk tanggal ini
                    table_data = [['No', 'Tanggal', 'Nama', 'Level', 'Nilai', 'Dokumentasi']]
                    for idx, (test, employee, position, _, matrix) in enumerate(date_tests, 1):
                        # Hitung skor
                        questions = Question.query.filter_by(
                            matrix_id=test.id_matrix,
                            position_id=employee.position_id
                        ).all()
                        results = ResultsTest.query.filter_by(id_test=test.id_test).all()
                        
                        correct_answers = 0
                        for question in questions:
                            user_answer = next((result.answer for result in results if result.id_question == question.question_id), None)
                            if user_answer and user_answer == question.answer:
                                correct_answers += 1
                        score = (correct_answers / len(questions) * 100) if questions else 0

                        # Bungkus semua teks dengan Paragraph untuk word wrap
                        row = [
                            Paragraph(str(idx), normal_style),
                            Paragraph(test.test_date.strftime('%Y-%m-%d') if test.test_date else "-", normal_style),
                            Paragraph(employee.employees_name, normal_style),
                            Paragraph(position.position_name, normal_style),
                            Paragraph(f"{score:.2f}%", normal_style),
                            None  # Placeholder untuk kolom Dokumentasi
                        ]

                        # Proses gambar dokumentasi (ambil gambar pertama dari JSON array)
                        if test.dokumentasi:
                            try:
                                filenames = json.loads(test.dokumentasi)
                                if filenames and len(filenames) > 0:
                                    image_path = os.path.join(os.getcwd(), filenames[0])
                                    if os.path.exists(image_path):
                                        with PILImage.open(image_path) as img:
                                            img = img.convert('RGB')
                                            img_buffer = BytesIO()
                                            img.thumbnail((20*mm, 20*mm), PILImage.Resampling.LANCZOS)
                                            img.save(img_buffer, format='JPEG')
                                            img_buffer.seek(0)
                                            row[5] = Image(img_buffer, width=20*mm, height=20*mm)
                                    else:
                                        row[5] = Paragraph("-", normal_style)
                                else:
                                    row[5] = Paragraph("-", normal_style)
                            except Exception as e:
                                print(f"Error processing image: {e}")
                                row[5] = Paragraph("-", normal_style)
                        else:
                            row[5] = Paragraph("-", normal_style)

                        table_data.append(row)

                    # Sesuaikan lebar kolom
                    colWidths = [15*mm, 25*mm, 50*mm, 35*mm, 25*mm, 25*mm]
                    table = Table(table_data, colWidths=colWidths, rowHeights=25*mm)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                        ('TOPPADDING', (0, 0), (-1, 0), 6),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('ALTERNATE_BACKGROUND', (0, 1), (-1, -1), colors.lightgrey, 0.5),
                        ('BOX', (5, 1), (5, -1), 0.5, colors.black),  # Border untuk kolom Dokumentasi
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 10*mm))

                    # Tambahkan PageBreak setelah setiap tanggal, kecuali untuk tanggal terakhir dalam employee-customer
                    if date_idx < len(tests_by_date) - 1:
                        elements.append(PageBreak())

                # Tambahkan PageBreak setelah setiap employee, kecuali untuk employee terakhir dalam customer
                if emp_id != list(employee_data.keys())[-1]:
                    elements.append(PageBreak())

            # Tambahkan PageBreak setelah setiap customer, kecuali untuk customer terakhir
            if cust_id != list(customer_employee_tests.keys())[-1]:
                elements.append(PageBreak())

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"test_report_{start_date_str}_{end_date_str}.pdf",
            mimetype='application/pdf'
        )

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500