import os
from flask import Blueprint, jsonify, request, send_file
from app.database import db
from app.models.urgent import Urgent
from app.models.employees import Employee
from app.models.position import Position
from app.models.customers import Customer
from app.models.checkpoints import Checkpoint
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
from PIL import Image as PILImage
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
import pytz

urgent_bp = Blueprint('urgent', __name__, url_prefix='/api/urgent')

# Timezone untuk Asia/Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

@urgent_bp.route('/', methods=['GET'])
def get_urgents():
    """
    Retrieve all urgent records.
    """
    try:
        urgents = Urgent.query.order_by(Urgent.id_urgent.desc()).all()
        return jsonify([urgent.to_dict() for urgent in urgents]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch urgent records", "details": str(e)}), 500

@urgent_bp.route('/<int:id_urgent>', methods=['GET'])
def get_urgent_by_id(id_urgent):
    """
    Retrieve a specific urgent record by ID.
    """
    try:
        urgent = Urgent.query.get(id_urgent)
        if not urgent:
            return jsonify({"error": "Urgent record not found"}), 404
        return jsonify(urgent.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch urgent record", "details": str(e)}), 500

def get_sorted_data(building_id, tanggal_awal=None, tanggal_akhir=None, sort_order='asc'):
    """
    Helper function untuk query data dengan filter dan sorting.
    """
    query = Urgent.query

    if building_id:
        query = query.filter(Urgent.building_id == building_id)
    if tanggal_awal:
        query = query.filter(Urgent.urgent_date >= tanggal_awal)
    if tanggal_akhir:
        query = query.filter(Urgent.urgent_date <= tanggal_akhir)

    if sort_order == 'asc':
        query = query.order_by(Urgent.urgent_date.asc())
    elif sort_order == 'desc':
        query = query.order_by(Urgent.urgent_date.desc())
    else:
        raise ValueError("Invalid sort_order. Use 'asc' or 'desc'")

    return query.all()

@urgent_bp.route('/filter_customer', methods=['GET'])
def filter_customer_by_date_range():
    """
    Filter urgent data by building_id and date range (tanggal_awal to tanggal_akhir).
    """
    try:
        building_id = request.args.get('building_id')
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')

        # Validasi parameter
        if not building_id or not tanggal_awal or not tanggal_akhir:
            return jsonify({"error": "building_id, tanggal_awal, and tanggal_akhir are required"}), 400

        try:
            tanggal_awal = datetime.strptime(tanggal_awal, "%Y-%m-%d")
            tanggal_akhir = datetime.strptime(tanggal_akhir, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Query data
        data = get_sorted_data(building_id=int(building_id), tanggal_awal=tanggal_awal, tanggal_akhir=tanggal_akhir)
        return jsonify([record.to_dict() for record in data]), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to filter data", "details": str(e)}), 500

@urgent_bp.route('/<int:id_urgent>', methods=['DELETE'])
def delete_urgent(id_urgent):
    """
    Delete an urgent record by ID.
    """
    try:
        urgent = Urgent.query.get(id_urgent)
        if not urgent:
            return jsonify({"error": "Urgent record not found"}), 404
        db.session.delete(urgent)
        db.session.commit()
        return jsonify({"message": "Urgent record deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete urgent record", "details": str(e)}), 500

@urgent_bp.route('/export_pdf', methods=['GET'])
def export_pdf():
    """
    Export urgent logs as a PDF report, grouped by employee, with columns: No, Tanggal, Waktu, Nama, Checkpoint, Keterangan, Foto, Status.
    Filterable by building_id, tanggal_awal, and tanggal_akhir (optional).
    """
    try:
        # Ambil parameter filter
        building_id = request.args.get('building_id', type=int)
        tanggal_awal = request.args.get('tanggal_awal')
        tanggal_akhir = request.args.get('tanggal_akhir')

        # Gunakan tanggal default jika parameter kosong
        start_date = None
        end_date = None
        if tanggal_awal or tanggal_akhir:
            today = datetime.now(jakarta_tz).date()
            last_month = today - timedelta(days=30)
            try:
                start_date = datetime.strptime(tanggal_awal, '%Y-%m-%d').date() if tanggal_awal else last_month
                end_date = datetime.strptime(tanggal_akhir, '%Y-%m-%d').date() if tanggal_akhir else today
                if start_date > end_date:
                    return jsonify({"error": "tanggal_awal cannot be after tanggal_akhir"}), 400
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Format tanggal untuk nama file dan header
        start_date_str = start_date.strftime('%Y-%m-%d') if start_date else 'All'
        end_date_str = end_date.strftime('%Y-%m-%d') if end_date else 'All'

        # Query data dengan join ke tabel terkait (left join untuk menangani data yang mungkin hilang)
        query = db.session.query(
            Urgent, Employee, Position, Customer, Checkpoint
        ).join(
            Employee, Urgent.id == Employee.id, isouter=False
        ).join(
            Position, Employee.position_id == Position.position_id, isouter=True
        ).join(
            Customer, Urgent.building_id == Customer.customer_id, isouter=True
        ).join(
            Checkpoint, Urgent.checkpoint_id == Checkpoint.id, isouter=True
        )

        # Tambahkan filter jika ada
        if start_date:
            query = query.filter(Urgent.urgent_date >= start_date)
        if end_date:
            query = query.filter(Urgent.urgent_date <= end_date)
        if building_id:
            query = query.filter(Urgent.building_id == building_id)

        # Urutkan berdasarkan id (employee) dan id_urgent
        urgent_logs = query.order_by(Urgent.id, Urgent.id_urgent).all()

        if not urgent_logs:
            return jsonify({"error": "Tidak ada data..."}), 404

        # Kelompokkan data per karyawan
        employee_logs = defaultdict(list)
        for urgent, employee, position, customer, checkpoint in urgent_logs:
            employee_logs[employee.id].append((urgent, employee, position, customer, checkpoint))

        # Buat PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=20*mm, bottomMargin=20*mm)
        elements = []

        styles = getSampleStyleSheet()
        title_style = styles['Heading2']
        normal_style = styles['Normal']
        normal_style.fontSize = 10

        # Style khusus untuk keterangan dan checkpoint dengan word wrap
        keterangan_style = styles['Normal']
        keterangan_style.fontSize = 8
        keterangan_style.leading = 10
        keterangan_style.wordWrap = 'CJK'

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
            elements.append(Paragraph(f"Nama: {employee.employees_name if employee else '-'}", normal_style))
            elements.append(Paragraph(f"Jabatan: {position.position_name if position else '-'}", normal_style))
            elements.append(Paragraph(f"Perusahaan: {customer.name if customer else '-'}", normal_style))
            elements.append(Spacer(1, 10*mm))

            # Buat tabel data log
            table_data = [['No', 'Tanggal', 'Waktu', 'Nama', 'Checkpoint', 'Keterangan', 'Foto', 'Status']]

            for idx, (urgent, employee, _, _, checkpoint) in enumerate(logs, 1):
                keterangan = urgent.urgent_result_user or "-"
                keterangan_paragraph = Paragraph(keterangan, keterangan_style)

                checkpoint_name = checkpoint.checkpoints_name if checkpoint and checkpoint.checkpoints_name else "-"
                checkpoint_paragraph = Paragraph(checkpoint_name, checkpoint_style)

                # Map status to text
                status_text = {
                    'N': 'Dilaporkan',
                    '1': 'Diproses',
                    '2': 'Selesai'
                }.get(urgent.status, '-')

                row = [
                    str(idx),
                    urgent.urgent_date.strftime('%Y-%m-%d') if urgent.urgent_date else "-",
                    urgent.urgent_date.strftime('%H:%M') if urgent.urgent_date else "-",
                    employee.employees_name if employee else "-",
                    checkpoint_paragraph,
                    keterangan_paragraph,
                    None,  # Placeholder for Foto
                    status_text
                ]

                if urgent.urgent_photo:
                    image_path = os.path.join(os.getcwd(), 'uploads', urgent.urgent_photo)
                    if os.path.exists(image_path):
                        try:
                            with PILImage.open(image_path) as img:
                                img = img.convert('RGB')
                                img_buffer = BytesIO()
                                img.thumbnail((20*mm, 20*mm), PILImage.Resampling.LANCZOS)
                                img.save(img_buffer, format='JPEG')
                                img_buffer.seek(0)
                                row[6] = Image(img_buffer, width=20*mm, height=20*mm)
                        except Exception as e:
                            print(f"Error processing image: {e}")
                            row[6] = "-"
                    else:
                        row[6] = "-"
                else:
                    row[6] = "-"

                table_data.append(row)

            colWidths = [15*mm, 25*mm, 20*mm, 40*mm, 30*mm, 50*mm, 25*mm, 25*mm]
            table = Table(table_data, colWidths=colWidths, rowHeights=25*mm)
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
                ('BOX', (6, 1), (6, -1), 0.5, colors.black),
                ('LEFTPADDING', (5, 1), (5, -1), 5),
                ('RIGHTPADDING', (5, 1), (5, -1), 5),
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
            download_name=f"urgent_log_{start_date_str}_{end_date_str}.pdf",
            mimetype='application/pdf'
        )

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to generate PDF", "details": str(e)}), 500