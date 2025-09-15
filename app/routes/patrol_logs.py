import os
import base64
from flask import Blueprint, jsonify, request, send_file
from app.database import db
from app.models.patrol_logs import PatrolLog
from app.models.checkpoints import Checkpoint
from app.models.employees import Employee
from app.models.customers import Customer
from app.models.position import Position
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
from PIL import Image as PILImage

patrol_logs_bp = Blueprint('patrol_logs', __name__, url_prefix='/api/patrol_logs')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def delete_file(file_path):
    """Helper function to delete a file if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        
def encode_image_to_base64(image_path):
    """Helper function to encode an image to base64."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None


@patrol_logs_bp.route('/export_pdf', methods=['GET'])
def export_pdf():
    try:
        # Ambil parameter filter
        employee_id = request.args.get('employee_id', type=int)
        customer_id = request.args.get('customer_id', type=int)
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')

        # Tentukan tanggal default: 1 bulan ke belakang hingga hari ini
        today = datetime.now().date()
        last_month = today - timedelta(days=30)

        # Gunakan tanggal default jika parameter kosong
        if not tanggal_awal:
            start_date = last_month
        else:
            start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d').date()

        if not tanggal_akhir:
            end_date = today
        else:
            end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d').date()

        # Validasi tanggal
        if start_date > end_date:
            return jsonify({"error": "tanggal_awal cannot be after tanggal_akhir"}), 400

        # Format tanggal untuk nama file dan header
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Query data dengan join ke tabel terkait, termasuk Checkpoint
        query = db.session.query(
            PatrolLog, Employee, Position, Customer, Checkpoint
        ).join(
            Employee, PatrolLog.employee_id == Employee.id
        ).join(
            Position, Employee.position_id == Position.position_id
        ).join(
            Customer, Employee.customer_id == Customer.customer_id
        ).join(
            Checkpoint, PatrolLog.checkpoint_id == Checkpoint.id
        ).filter(
            PatrolLog.checkpoint_date >= start_date,
            PatrolLog.checkpoint_date <= end_date
        )

        # Tambahkan filter employee_id jika ada
        if employee_id:
            query = query.filter(PatrolLog.employee_id == employee_id)

        # Tambahkan filter customer_id jika ada
        if customer_id:
            query = query.filter(Customer.customer_id == customer_id)

        # Urutkan berdasarkan employee_id dan log_id
        patrol_logs = query.order_by(PatrolLog.employee_id, PatrolLog.log_id).limit(1500).all()

        if not patrol_logs:
            return jsonify({"error": "Tidak ada data"}), 404

        # Kelompokkan data per karyawan
        from collections import defaultdict
        employee_logs = defaultdict(list)
        for log, employee, position, customer, checkpoint in patrol_logs:
            employee_logs[employee.id].append((log, employee, position, customer, checkpoint))

        # Buat PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        normal_style = styles['Normal']
        normal_style.fontSize = 10

        # Style khusus untuk keterangan dengan word wrap
        keterangan_style = styles['Normal']
        keterangan_style.fontSize = 8
        keterangan_style.leading = 10
        keterangan_style.wordWrap = 'CJK'

        # Style khusus untuk checkpoints_name dengan word wrap
        checkpoint_style = styles['Normal']
        checkpoint_style.fontSize = 8
        checkpoint_style.leading = 10
        checkpoint_style.wordWrap = 'CJK'

        # Iterasi per karyawan
        for emp_id, logs in employee_logs.items():
            employee = logs[0][1]
            position = logs[0][2]
            customer = logs[0][3]

            # Tambahkan header informasi
            elements.append(Paragraph(f"Tanggal: {start_date_str} - {end_date_str}", title_style))
            elements.append(Paragraph(f"Nama: {employee.employees_name}", normal_style))
            elements.append(Paragraph(f"Jabatan: {position.position_name}", normal_style))
            elements.append(Spacer(1, 10*mm))

            # Buat tabel data log
            table_data = [['No', 'Tanggal', 'Checkpoint', 'Check In', 'Check Out', 'Foto', 'Keterangan', 'On Track', 'On Schedule']]

            for idx, (log, _, _, _, checkpoint) in enumerate(logs, 1):
                keterangan = log.checkpoint_result or "-"
                keterangan_paragraph = Paragraph(keterangan, keterangan_style)

                # Wrap checkpoints_name dalam Paragraph untuk word wrap
                checkpoint_name = checkpoint.checkpoints_name if checkpoint and checkpoint.checkpoints_name else "-"
                checkpoint_paragraph = Paragraph(checkpoint_name, checkpoint_style)

                row = [
                    str(idx),
                    log.checkpoint_date.strftime('%Y-%m-%d') if log.checkpoint_date else "-",
                    checkpoint_paragraph,
                    log.checkpoint_in or "-",
                    log.checkpoint_out or "-",
                    None,
                    keterangan_paragraph,
                    'X' if log.track == 1 else 'V' if log.track == 2 else "-",
                    'X' if log.schedule == 1 else 'V' if log.schedule == 2 else "-",
                ]

                if log.checkpoint_photo:
                    image_path = os.path.join(os.getcwd(), log.checkpoint_photo)
                    if os.path.exists(image_path):
                        try:
                            with PILImage.open(image_path) as img:
                                img = img.convert('RGB')
                                # Calculate target pixels for 75 DPI at 30mm
                                target_size = (int(30 * mm * 75 / 25.4), int(30 * mm * 75 / 25.4))  # ~177 pixels
                                img_buffer = BytesIO()
                                img.thumbnail(target_size, PILImage.Resampling.LANCZOS)
                                img.save(img_buffer, format='JPEG', quality=95, optimize=True, progressive=True)
                                img_buffer.seek(0)
                                row[5] = Image(img_buffer, width=30*mm, height=30*mm, kind='proportional')
                        except Exception as e:
                            print(f"Error processing image: {e}")
                            row[5] = "-"
                    else:
                        row[5] = "-"
                else:
                    row[5] = "-"

                table_data.append(row)

            # Adjust column widths: reduce Check In and Check Out, increase Foto
            colWidths = [15*mm, 25*mm, 25*mm, 20*mm, 20*mm, 35*mm, 40*mm, 20*mm, 20*mm]
            table = Table(table_data, colWidths=colWidths, rowHeights=30*mm)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALTERNATE_BACKGROUND', (0, 1), (-1, -1), colors.lightgrey, 0.5),
                ('BOX', (5, 1), (5, -1), 0.5, colors.black),
                ('LEFTPADDING', (6, 1), (6, -1), 5),
                ('RIGHTPADDING', (6, 1), (6, -1), 5),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20*mm))

            if emp_id != list(employee_logs.keys())[-1]:
                elements.append(Spacer(1, 0))

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"log_patroli_{start_date_str}_{end_date_str}.pdf",
            mimetype='application/pdf'
        )

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500

@patrol_logs_bp.route('/latest', methods=['GET'])
def get_latest_patrol_logs():
    try:
        # Ambil parameter page dan per_page dari query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)

        # Aliasing tabel untuk lebih mudah dibaca
        PL = aliased(PatrolLog)
        Emp = aliased(Employee)
        Cust = aliased(Customer)

        # Subquery: Mendapatkan patrol log terbaru per employee
        latest_subquery = (
            db.session.query(
                PL.employee_id,
                func.max(PL.updated_at).label("latest_updated_at")
            )
            .group_by(PL.employee_id)
            .subquery()
        )

        # Query utama: Mengambil log terbaru, serta join ke Employee dan Customer
        patrol_logs_query = (
            db.session.query(PL, Emp, Cust)
            .join(latest_subquery, 
                  (PL.employee_id == latest_subquery.c.employee_id) &
                  (PL.updated_at == latest_subquery.c.latest_updated_at))
            .join(Emp, PL.employee_id == Emp.id)
            .join(Cust, Emp.customer_id == Cust.customer_id)
            .order_by(PL.updated_at.desc())  # Urut berdasarkan employee_id
        )

        # Paginasi menggunakan offset & limit (opsional jika ingin lebih optimal)
        paginated_logs = patrol_logs_query.offset((page - 1) * per_page).limit(per_page).all()

        # Format hasil query menjadi JSON
        data = []
        for log, employee, customer in paginated_logs:
            log_data = log.to_dict()
            log_data['Employee'] = employee.to_dict()
            log_data['Customer'] = customer.to_dict()

            # Encode the image to base64 and add it to the log_data
            if log.checkpoint_photo:
                image_path = os.path.join(os.getcwd(), log.checkpoint_photo)
                base64_image = encode_image_to_base64(image_path)
                if base64_image:
                    log_data['image_decode'] = base64_image
                else:
                    log_data['image_decode'] = None
            else:
                log_data['image_decode'] = None

            data.append(log_data)

        # Hitung total data tanpa pagination
        total_count = db.session.query(func.count()).select_from(latest_subquery).scalar()

        return jsonify({
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "data": data
        }), 200

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Failed to fetch latest patrol logs", "details": str(e)}), 500

@patrol_logs_bp.route('/check/asc/customer', methods=['GET'])
def check_asc_patrol_logs_customer():
    """
    Check patrol logs by customer_id, checkpoint_date, and optionally employee_id, ordered by log_id ascending.
    """
    try:
        customer_id = request.args.get('customer_id', type=int)
        checkpoint_date = request.args.get('checkpoint_date')
        employee_id = request.args.get('employee_id', type=int)  # Ambil employee_id (opsional)

        if not customer_id or not checkpoint_date:
            return jsonify({"error": "Both customer_id and checkpoint_date are required"}), 400

        # Convert checkpoint_date to datetime object
        checkpoint_date = datetime.strptime(checkpoint_date, '%Y-%m-%d')

        # Build the query
        query = PatrolLog.query\
            .join(Employee, PatrolLog.employee_id == Employee.id)\
            .filter(
                Employee.customer_id == customer_id,
                PatrolLog.checkpoint_date == checkpoint_date
            )

        # Tambahkan filter employee_id jika ada
        if employee_id is not None:
            query = query.filter(PatrolLog.employee_id == employee_id)

        # Urutkan berdasarkan log_id secara ascending
        patrol_logs = query.order_by(PatrolLog.log_id.asc()).all()

        if not patrol_logs:
            return jsonify({"error": "Tidak ada data"}), 404

        return jsonify([log.to_dict() for log in patrol_logs]), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to check patrol logs for customer", "details": str(e)}), 500
        
@patrol_logs_bp.route('/filter/customer', methods=['GET'])
def filter_patrol_logs_customer():
    """
    Filter patrol logs by customer_id, date range, and optionally employee_id, ordered by log_id ascending.
    """
    try:
        customer_id = request.args.get('customer_id', type=int)
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')
        employee_id = request.args.get('employee_id', type=int)  # Ambil employee_id (opsional)

        if not customer_id or not tanggal_awal or not tanggal_akhir:
            return jsonify({"error": "customer_id, tanggal_awal, and tanggal_akhir are required"}), 400

        # Convert string dates to datetime objects
        start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d')
        end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d')

        # Build the query
        query = PatrolLog.query\
            .join(Employee, PatrolLog.employee_id == Employee.id)\
            .filter(
                Employee.customer_id == customer_id,
                PatrolLog.checkpoint_date >= start_date,
                PatrolLog.checkpoint_date <= end_date
            )

        # Tambahkan filter employee_id jika ada
        if employee_id is not None:
            query = query.filter(PatrolLog.employee_id == employee_id)

        # Urutkan berdasarkan log_id secara ascending
        patrol_logs = query.order_by(PatrolLog.log_id.asc()).all()

        if not patrol_logs:
            return jsonify({"error": "Tidak ada data"}), 404

        return jsonify([log.to_dict() for log in patrol_logs]), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to filter patrol logs for customer", "details": str(e)}), 500
        
@patrol_logs_bp.route('/mobile', methods=['GET'])
def get_patrol_logs_by_employee_and_date():
    """
    Retrieve patrol logs and corresponding checkpoint data by employee_id and checkpoint_date.
    """
    try:
        employee_id = request.args.get('employee_id', type=int)
        checkpoint_date_str = request.args.get('checkpoint_date')

        if not employee_id or not checkpoint_date_str:
            return jsonify({"error": "employee_id and checkpoint_date are required"}), 400

        # Convert checkpoint_date_str to datetime object
        checkpoint_date = datetime.strptime(checkpoint_date_str, '%Y-%m-%d')

        # Query the database for patrol logs
        patrol_logs = PatrolLog.query.filter_by(employee_id=employee_id, checkpoint_date=checkpoint_date).all()

        if not patrol_logs:
            return jsonify({"error": "Tidak ada data"}), 404

        # Prepare the response data
        response_data = []
        for log in patrol_logs:
            checkpoint = Checkpoint.query.get(log.checkpoint_id)  # Get the corresponding checkpoint
            if checkpoint:
                response_data.append({
                    "log_id": log.log_id,  # Assuming log_id is the primary key in PatrolLog
                    "checkpoint": checkpoint.to_dict(),  # Convert checkpoint to dict
                    "checkpoint_date": log.checkpoint_date,
                    "other_log_data": log.to_dict()  # Include other log data as needed
                })

        return jsonify(response_data), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to retrieve patrol logs", "details": str(e)}), 500

# @patrol_logs_bp.route('/latest', methods=['GET'])
# def get_latest_patrol_logs():
#     try:
#         # Ambil parameter page dan per_page dari query string
#         page = request.args.get('page', 1, type=int)
#         per_page = request.args.get('per_page', 15, type=int)

#         # Aliasing tabel untuk lebih mudah dibaca
#         PL = aliased(PatrolLog)
#         Emp = aliased(Employee)
#         Cust = aliased(Customer)

#         # Subquery: Mendapatkan patrol log terbaru per employee
#         latest_subquery = (
#             db.session.query(
#                 PL.employee_id,
#                 func.max(PL.updated_at).label("latest_updated_at")
#             )
#             .group_by(PL.employee_id)
#             .subquery()
#         )

#         # Query utama: Mengambil log terbaru, serta join ke Employee dan Customer
#         patrol_logs_query = (
#             db.session.query(PL, Emp, Cust)
#             .join(latest_subquery, 
#                   (PL.employee_id == latest_subquery.c.employee_id) &
#                   (PL.updated_at == latest_subquery.c.latest_updated_at))
#             .join(Emp, PL.employee_id == Emp.id)
#             .join(Cust, Emp.customer_id == Cust.customer_id)
#             .order_by(PL.updated_at.desc())  # Urut berdasarkan employee_id
#         )

#         # Paginasi menggunakan offset & limit (opsional jika ingin lebih optimal)
#         paginated_logs = patrol_logs_query.offset((page - 1) * per_page).limit(per_page).all()

#         # Format hasil query menjadi JSON
#         data = []
#         for log, employee, customer in paginated_logs:
#             log_data = log.to_dict()
#             log_data['Employee'] = employee.to_dict()
#             log_data['Customer'] = customer.to_dict()
#             data.append(log_data)

#         # Hitung total data tanpa pagination
#         total_count = db.session.query(func.count()).select_from(latest_subquery).scalar()

#         return jsonify({
#             "total": total_count,
#             "page": page,
#             "per_page": per_page,
#             "data": data
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({"error": "Database error", "details": str(e)}), 500
#     except Exception as e:
#         return jsonify({"error": "Failed to fetch latest patrol logs", "details": str(e)}), 500
        
@patrol_logs_bp.route('/filter', methods=['GET'])  
def filter_patrol_logs():  
    """  
    Filter patrol logs by employee_id and date range.  
    """  
    try:  
        employee_id = request.args.get('employee_id', type=int)  
        tanggal_awal = request.args.get('tanggal_awal')  
        tanggal_akhir = request.args.get('tanggal_akhir')  
  
        if not employee_id or not tanggal_awal or not tanggal_akhir:  
            return jsonify({"error": "employee_id, tanggal_awal, and tanggal_akhir are required"}), 400  
  
        # Convert string dates to datetime objects  
        start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d')  
        end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d')  
  
        # Query the database for patrol logs within the specified date range  
        patrol_logs = PatrolLog.query.filter(  
            PatrolLog.employee_id == employee_id,  
            PatrolLog.checkpoint_date >= start_date,  
            PatrolLog.checkpoint_date <= end_date  
        ).order_by(PatrolLog.log_id.asc()).all()  
  
        return jsonify([log.to_dict() for log in patrol_logs]), 200  
    except ValueError as ve:  
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400  
    except Exception as e:  
        return jsonify({"error": "Failed to filter patrol logs", "details": str(e)}), 500  


@patrol_logs_bp.route('/employee/<int:employee_id>', methods=['GET'])
def get_patrol_logs_with_employee_and_position(employee_id):
    """
    Retrieve patrol logs along with employee name and position name by employee_id using a JOIN operation.
    """
    try:
        # Perform the JOIN operation between PatrolLog, Employee, and Position tables
        patrol_logs_with_details = db.session.query(
            PatrolLog,
            Employee.employees_name,
            Position.position_name
        ).join(
            Employee, PatrolLog.employee_id == Employee.id
        ).join(
            Position, Employee.position_id == Position.position_id
        ).filter(
            PatrolLog.employee_id == employee_id
        ).all()

        if not patrol_logs_with_details:
            return jsonify({"error": "Tidak ada data"}), 404

        # Format the result as a JSON response
        response_data = []
        for log, employees_name, position_name in patrol_logs_with_details:
            log_data = log.to_dict()
            log_data['employees_name'] = employees_name
            log_data['position_name'] = position_name
            response_data.append(log_data)

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve patrol logs with employee and position", "details": str(e)}), 500
        
@patrol_logs_bp.route('/employees/<int:employee_id>', methods=['GET'])
def get_patrol_logs_with_employee_and_position_with_image(employee_id):
    """
    Retrieve patrol logs along with employee name, position name, and base64 encoded image by employee_id using a JOIN operation.
    """
    try:
        # Perform the JOIN operation between PatrolLog, Employee, and Position tables
        patrol_logs_with_details = db.session.query(
            PatrolLog,
            Employee.employees_name,
            Position.position_name
        ).join(
            Employee, PatrolLog.employee_id == Employee.id
        ).join(
            Position, Employee.position_id == Position.position_id
        ).filter(
            PatrolLog.employee_id == employee_id
        ).order_by(
            desc(PatrolLog.updated_at)
        ).all()

        if not patrol_logs_with_details:
            return jsonify({"error": "Tidak ada data"}), 404

        # Format the result as a JSON response
        response_data = []
        for log, employees_name, position_name in patrol_logs_with_details:
            log_data = log.to_dict()
            log_data['employees_name'] = employees_name
            log_data['position_name'] = position_name

            # Encode the image to base64 and add it to the log_data
            if log.checkpoint_photo:
                image_path = os.path.join(os.getcwd(), log.checkpoint_photo)
                base64_image = encode_image_to_base64(image_path)
                if base64_image:
                    log_data['image_decoded'] = base64_image
                else:
                    log_data['image_decoded'] = None
            else:
                log_data['image_decoded'] = None

            response_data.append(log_data)

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": "Failed to retrieve patrol logs with employee and position", "details": str(e)}), 500


@patrol_logs_bp.route('/', methods=['GET'])
def get_patrol_logs():
    """
    Retrieve all patrol logs.
    """
    try:
        patrol_logs = PatrolLog.query.order_by(PatrolLog.log_id.desc()).all()
        return jsonify([log.to_dict() for log in patrol_logs]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch patrol logs", "details": str(e)}), 500

@patrol_logs_bp.route('/check', methods=['GET'])
def check_patrol_logs():
    """
    Check patrol logs by employee_id and checkpoint_date.
    """
    try:
        employee_id = request.args.get('employee_id')
        checkpoint_date = request.args.get('checkpoint_date')

        if not employee_id or not checkpoint_date:
            return jsonify({"error": "Both employee_id and checkpoint_date are required"}), 400

        patrol_logs = PatrolLog.query.filter(
            PatrolLog.employee_id == employee_id,
            PatrolLog.checkpoint_date == checkpoint_date
        ).order_by(PatrolLog.log_id.desc()).all()

        return jsonify([log.to_dict() for log in patrol_logs]), 200
    except Exception as e:
        return jsonify({"error": "Failed to check patrol logs", "details": str(e)}), 500
        

@patrol_logs_bp.route('/check/asc/', methods=['GET'])
def check_asc_patrol_logs():
    """
    Check patrol logs by employee_id and checkpoint_date.
    """
    try:
        employee_id = request.args.get('employee_id')
        checkpoint_date = request.args.get('checkpoint_date')

        if not employee_id or not checkpoint_date:
            return jsonify({"error": "Both employee_id and checkpoint_date are required"}), 400

        patrol_logs = PatrolLog.query.filter(
            PatrolLog.employee_id == employee_id,
            PatrolLog.checkpoint_date == checkpoint_date
        ).order_by(PatrolLog.log_id.asc()).all()

        return jsonify([log.to_dict() for log in patrol_logs]), 200
    except Exception as e:
        return jsonify({"error": "Failed to check patrol logs", "details": str(e)}), 500        
        
@patrol_logs_bp.route('/<int:log_id>', methods=['GET'])
def get_patrol_log_by_id(log_id):
    """
    Retrieve a specific patrol log by ID.
    """
    try:
        patrol_log = PatrolLog.query.get(log_id)
        if not patrol_log:
            return jsonify({"error": "Patrol log not found"}), 404

        return jsonify(patrol_log.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch patrol log", "details": str(e)}), 500

@patrol_logs_bp.route('/', methods=['POST'])
def create_patrol_log():
    """
    Create a new patrol log with limited fields and default 'process' session.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        patrol_log = PatrolLog(
            employee_id=data.get("employee_id"),
            checkpoint_id=data.get("checkpoint_id"),
            checkpoint_date=data.get("checkpoint_date"),
            checkpoint_in=data.get("checkpoint_in"),
            session='process'  # Static value
        )
        db.session.add(patrol_log)
        db.session.commit()
        return jsonify({"message": "Patrol log created successfully!", "patrol_log": patrol_log.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create patrol log", "details": str(e)}), 500

@patrol_logs_bp.route('/<int:log_id>', methods=['PUT'])
def update_patrol_log(log_id):
    """
    Update specific fields of an existing patrol log: checkpoint_out, checkpoint_result, checkpoint_photo, track, and schedule.
    """
    try:
        data = request.form
        photo = request.files.get('checkpoint_photo')

        patrol_log = PatrolLog.query.get(log_id)
        if not patrol_log:
            return jsonify({"error": "Patrol log not found"}), 404

        # Update allowed fields only
        patrol_log.checkpoint_out = data.get("checkpoint_out", patrol_log.checkpoint_out)
        patrol_log.checkpoint_result = data.get("checkpoint_result", patrol_log.checkpoint_result)
        patrol_log.track = data.get("track", patrol_log.track)  # Update track
        patrol_log.schedule = data.get("schedule", patrol_log.schedule)  # Update schedule
        patrol_log.session = 'end'

        # Update photo if exists
        if photo:
            old_photo_path = os.path.join(os.getcwd(), patrol_log.checkpoint_photo) if patrol_log.checkpoint_photo else None
            secure_name = secure_filename(photo.filename)
            new_photo_path = os.path.join(UPLOAD_FOLDER, secure_name)
            photo.save(new_photo_path)
            patrol_log.checkpoint_photo = f'uploads/{secure_name}'  # Save the new photo path
            delete_file(old_photo_path)  # Delete old photo if it exists

        db.session.commit()
        return jsonify({"message": "Patrol log updated successfully!", "patrol_log": patrol_log.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update patrol log", "details": str(e)}), 500

@patrol_logs_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_patrol_log(log_id):
    """
    Delete a patrol log by ID.
    """
    try:
        patrol_log = PatrolLog.query.get(log_id)
        if not patrol_log:
            return jsonify({"error": "Patrol log not found"}), 404

        # Delete photo if exists
        if patrol_log.checkpoint_photo:
            photo_path = os.path.join(os.getcwd(), patrol_log.checkpoint_photo)
            delete_file(photo_path)

        db.session.delete(patrol_log)
        db.session.commit()
        return jsonify({"message": "Patrol log deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete patrol log", "details": str(e)}), 500
