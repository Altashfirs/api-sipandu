import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.database import db
from app.models.item_discovery import ItemDiscovery
from app.models.employees import Employee
from datetime import datetime, timedelta, date
from sqlalchemy.sql import text

item_discovery_bp = Blueprint('item_discovery', __name__, url_prefix='/api/item_discovery')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@item_discovery_bp.route('/check', methods=['GET'])
def check_item_discovery_entries():
    customer_id = request.args.get("customer_id")
    start_date = request.args.get("tanggal_awal")

    if not start_date:
        return jsonify({"error": "tanggal_awal is required"}), 400

    try:
        parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "tanggal_awal harus dalam format YYYY-MM-DD"}), 400

    if not customer_id:
        return jsonify({"error": "customer_id is required"}), 400

    # Query menggunakan relasi SQLAlchemy
    results = (
        db.session.query(ItemDiscovery)
        .join(Employee, ItemDiscovery.id == Employee.id)  # Join dengan tabel employees
        .filter(Employee.customer_id == customer_id)  # Filter berdasarkan customer_id
        .filter(db.func.date(ItemDiscovery.item_discovery_date) == parsed_date)  # Filter berdasarkan tanggal
        .all()
    )

    if results:
        result_list = [result.to_dict() for result in results]  # Gunakan method to_dict
        return jsonify(result_list)
    else:
        return jsonify({"message": "Tidak Ada Data..."}), 404

@item_discovery_bp.route('/filter', methods=['GET'])
def filter_item_discovery_entries():
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

    if not customer_id:
        return jsonify({"error": "customer_id is required"}), 400

    # Query menggunakan relasi SQLAlchemy
    results = (
        db.session.query(ItemDiscovery)
        .join(Employee, ItemDiscovery.id == Employee.id)  # Join dengan tabel employees
        .filter(Employee.customer_id == customer_id)  # Filter berdasarkan customer_id
        .filter(ItemDiscovery.item_discovery_date >= parsed_start_date)  # Filter tanggal awal
        .filter(ItemDiscovery.item_discovery_date <= parsed_end_date)  # Filter tanggal akhir
        .all()
    )

    if results:
        result_list = [result.to_dict() for result in results]  # Gunakan method to_dict
        return jsonify(result_list)
    else:
        return jsonify({"message": "Tidak Ada Data..."}), 404
        
def serialize_result(result):
    return {column: getattr(result, column) for column in result.keys()}
    
@item_discovery_bp.route('/', methods=['GET'])
def get_item_discoveries():
    try:
        items = ItemDiscovery.query.all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch items: {str(e)}"}), 500

@item_discovery_bp.route('/<int:id_item_discovery>', methods=['GET'])
def get_item_by_id(id_item_discovery):
    try:
        item = ItemDiscovery.query.get(id_item_discovery)
        if not item:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(item.to_dict()), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch item: {str(e)}"}), 500

@item_discovery_bp.route('/', methods=['POST'])
def create_item_discovery():
    try:
        data = request.form
        files = request.files

        # Daftar field required beserta pesan yang ingin ditampilkan
        required_fields = {
            'item_discovery_date': 'Harap mengisi tanggal penemuan',
            'o_clock_item_discovery': 'Harap mengisi jam penemuan',
            'inventors_name': 'Harap mengisi nama penemu',
            'ttl': 'Harap mengisi tempat/tanggal lahir',
            'address': 'Harap mengisi alamat',
            'telephone_number': 'Harap mengisi nomor telepon',
            'id_card_number': 'Harap mengisi nomor KTP',
            'location_found': 'Harap mengisi lokasi penemuan',
            'name_goods': 'Harap mengisi nama barang',
            'amount': 'Harap mengisi jumlah barang',
            'information': 'Harap mengisi informasi',
            'id': 'Harap mengisi ID',
            'position_id': 'Harap mengisi ID posisi',
            'shift_id': 'Harap mengisi ID shift'
        }

        # Cek setiap field required
        missing_fields = []
        for field, message in required_fields.items():
            if not data.get(field):
                missing_fields.append(message)  # Tambahkan pesan khusus untuk field yang kosong

        # Jika ada field yang kosong, kembalikan pesan error
        if missing_fields:
            return jsonify({"error": missing_fields}), 400

        # Lanjutkan proses jika semua field terisi
        item_discovery_photo = files.get('item_discovery_photo')
        item_discovery_photo_end = files.get('item_discovery_photo_end')

        photo_path = save_file(item_discovery_photo) if item_discovery_photo else None
        photo_path_end = save_file(item_discovery_photo_end) if item_discovery_photo_end else None

        item = ItemDiscovery(
            item_discovery_date=data.get('item_discovery_date'),
            o_clock_item_discovery=data.get('o_clock_item_discovery'),
            inventors_name=data.get('inventors_name'),
            ttl=data.get('ttl'),
            address=data.get('address'),
            telephone_number=data.get('telephone_number'),
            id_card_number=data.get('id_card_number'),
            location_found=data.get('location_found'),
            name_goods=data.get('name_goods'),
            amount=data.get('amount'),
            information=data.get('information'),
            id=data.get('id'),
            position_id=data.get('position_id'),
            shift_id=data.get('shift_id'),
            status=data.get('status', '1'),
            item_discovery_date_end=data.get('item_discovery_date_end'),
            id_user_end=data.get('id_user_end'),
            information_end=data.get('information_end'),
            inventors_name_end=data.get('inventors_name_end'),
            item_discovery_photo=photo_path,
            item_discovery_photo_end=photo_path_end
        )

        db.session.add(item)
        db.session.commit()
        return jsonify({"message": "Item created successfully!", "item": item.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create item: {str(e)}"}), 500

@item_discovery_bp.route('/<int:id_item_discovery>', methods=['PUT'])
def update_item_discovery(id_item_discovery):
    item = ItemDiscovery.query.get(id_item_discovery)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        data = request.form
        files = request.files

        # Daftar field required beserta pesan yang ingin ditampilkan
        required_fields = {
            'item_discovery_date': 'Harap mengisi tanggal penemuan',
            'o_clock_item_discovery': 'Harap mengisi jam penemuan',
            'inventors_name': 'Harap mengisi nama penemu',
            'ttl': 'Harap mengisi tempat/tanggal lahir',
            'address': 'Harap mengisi alamat',
            'telephone_number': 'Harap mengisi nomor telepon',
            'id_card_number': 'Harap mengisi nomor KTP',
            'location_found': 'Harap mengisi lokasi penemuan',
            'name_goods': 'Harap mengisi nama barang',
            'amount': 'Harap mengisi jumlah barang',
            'information': 'Harap mengisi informasi',
            'id': 'Harap mengisi ID',
            'position_id': 'Harap mengisi ID posisi',
            'shift_id': 'Harap mengisi ID shift'
        }

        # Cek setiap field required
        missing_fields = []
        for field, message in required_fields.items():
            if not data.get(field):
                missing_fields.append(message)  # Tambahkan pesan khusus untuk field yang kosong

        # Jika ada field yang kosong, kembalikan pesan error
        if missing_fields:
            return jsonify({"error": missing_fields}), 400

        # Update data item (hanya field yang tidak berakhiran _end)
        item.item_discovery_date = data.get('item_discovery_date')
        item.o_clock_item_discovery = data.get('o_clock_item_discovery')
        item.inventors_name = data.get('inventors_name')
        item.ttl = data.get('ttl')
        item.address = data.get('address')
        item.telephone_number = data.get('telephone_number')
        item.id_card_number = data.get('id_card_number')
        item.location_found = data.get('location_found')
        item.name_goods = data.get('name_goods')
        item.amount = data.get('amount')
        item.information = data.get('information')
        item.id = data.get('id')
        item.position_id = data.get('position_id')
        item.shift_id = data.get('shift_id')
        item.status = data.get('status')

        # Update file jika ada (hanya item_discovery_photo, bukan item_discovery_photo_end)
        if 'item_discovery_photo' in files:
            item.item_discovery_photo = save_file(files['item_discovery_photo'], item.item_discovery_photo)

        db.session.commit()
        return jsonify({"message": "Item updated successfully!", "item": item.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update item: {str(e)}"}), 500
        
@item_discovery_bp.route('/end/<int:id_item_discovery>', methods=['PUT'])
def update_item_discovery_end(id_item_discovery):
    item = ItemDiscovery.query.get(id_item_discovery)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        data = request.form
        files = request.files

        # Update hanya kolom yang berakhiran _end
        if 'item_discovery_date_end' in data:
            item.item_discovery_date_end = data.get('item_discovery_date_end')
        if 'id_user_end' in data:
            item.id_user_end = data.get('id_user_end')
        if 'information_end' in data:
            item.information_end = data.get('information_end')
        if 'inventors_name_end' in data:
            item.inventors_name_end = data.get('inventors_name_end')
        if 'status' in data:
            item.status = data.get('status')

        # Update file item_discovery_photo_end jika ada
        if 'item_discovery_photo_end' in files:
            item.item_discovery_photo_end = save_file(files['item_discovery_photo_end'], item.item_discovery_photo_end)

        db.session.commit()
        return jsonify({"message": "Item _end fields updated successfully!", "item": item.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update item _end fields: {str(e)}"}), 500
        
@item_discovery_bp.route('/<int:id_item_discovery>', methods=['DELETE'])
def delete_item_discovery(id_item_discovery):
    item = ItemDiscovery.query.get(id_item_discovery)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        if item.item_discovery_photo and os.path.exists(os.path.join(os.getcwd(), item.item_discovery_photo)):
            os.remove(os.path.join(os.getcwd(), item.item_discovery_photo))
        if item.item_discovery_photo_end and os.path.exists(os.path.join(os.getcwd(), item.item_discovery_photo_end)):
            os.remove(os.path.join(os.getcwd(), item.item_discovery_photo_end))

        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Item deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete item: {str(e)}"}), 500

def save_file(file, old_file_path=None):
    if old_file_path and os.path.exists(os.path.join(os.getcwd(), old_file_path)):
        os.remove(os.path.join(os.getcwd(), old_file_path))

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return f'uploads/{filename}'

def format_date(date):
    return date.strftime("%Y-%m-%d") if date else None

