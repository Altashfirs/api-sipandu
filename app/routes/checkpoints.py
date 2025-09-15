import os
from flask import Blueprint, jsonify, request, send_file
from app.database import db
from app.models.checkpoints import Checkpoint
from app.models.customers import Customer 
from datetime import datetime
from werkzeug.utils import secure_filename
from pytz import timezone
import requests
import qrcode
import logging
from PIL import Image, ImageDraw, ImageFont
import textwrap
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)

checkpoints_bp = Blueprint('checkpoints', __name__, url_prefix='/api/checkpoints')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def delete_file(file_path):
    """Helper function to delete a file if it exists."""
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

@checkpoints_bp.route('/regenerate-qr/<int:id>', methods=['PUT'])
def regenerate_qr_code(id):
    """
    Regenerate the QR code for a checkpoint by ID.
    This will replace the existing QR code with a new one, with text below the QR code
    showing the checkpoint name and the customer name, with a white background.
    The QR code size will be 300x300 pixels.
    """
    try:
        # Query the checkpoint by ID
        checkpoint = Checkpoint.query.get(id)
        if not checkpoint:
            return jsonify({"error": "Checkpoint not found"}), 404

        # Delete the existing QR code file if it exists
        if checkpoint.checkpoint_qrcode:
            old_qr_filepath = os.path.join(os.getcwd(), checkpoint.checkpoint_qrcode)
            if os.path.exists(old_qr_filepath):
                os.remove(old_qr_filepath)

        # Generate a new QR code
        qr_data = checkpoint.checkpoints_code
        checkpoint_name = checkpoint.checkpoints_name
        customer_id = checkpoint.customer_id

        # Query the customer by customer_id to get the customer name
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found for this checkpoint"}), 404
        customer_name = customer.name  # Get the customer name from the Customer model

        # Create QR code image with size 300x300 pixels
        logging.info("Membuat kode QR...")
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=13,  # Adjusted to make QR code approximately 300x300 pixels
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.convert("RGB")  # Convert to RGB to add text

        # Add text below the QR code
        img_width, img_height = img.size  # Should be around 300x300 pixels
        padding = 40  # Increased padding for better spacing around QR code and text
        text_height = 80  # Estimated height for two lines of text
        new_height = img_height + text_height + padding * 2  # Extra padding at top and bottom
        new_width = img_width + padding * 2  # Extra padding on left and right

        # Create a new image with a white background and additional space for text
        new_img = Image.new("RGB", (new_width, new_height), "white")
        # Center the QR code in the new image
        qr_x = (new_width - img_width) // 2  # Center horizontally
        qr_y = padding  # Add padding at the top
        new_img.paste(img, (qr_x, qr_y))  # Paste the QR code with padding

        # Add text
        draw = ImageDraw.Draw(new_img)

        # Use default font or download a custom font
        try:
            font_url = "https://fonts.googleapis.com/css2?family=Roboto:wght@500&display=swap"
            font_file_url = "https://fonts.gstatic.com/s/roboto/v27/KFOlCnqEu92Fr1MmWUlfBBc4.woff2"
            font_response = requests.get(font_file_url, timeout=10)
            font_response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".woff2") as temp_font_file:
                temp_font_file.write(font_response.content)
                temp_font_path = temp_font_file.name

            font = ImageFont.truetype(temp_font_path, 20)
        except Exception as e:
            logging.warning(f"Gagal mengunduh font: {str(e)}. Menggunakan font default.")
            font = ImageFont.load_default()

        # Add checkpoint name and customer name
        text_y = img_height + padding + 5  # Distance from QR code to text
        text_x = new_width // 2  # Center of the image

        # Wrap text if too long
        max_width = img_width - 10  # Maximum text width
        wrapped_checkpoint_name = textwrap.wrap(checkpoint_name, width=20)
        wrapped_customer_name = textwrap.wrap(customer_name, width=25)

        # Draw checkpoint name line by line
        for line in wrapped_checkpoint_name:
            text_width = draw.textlength(line, font=font)
            draw.text((text_x - text_width // 2, text_y), line, fill="black", font=font)
            text_y += 30  # Move down for the next line

        # Draw customer name line by line
        for line in wrapped_customer_name:
            text_width = draw.textlength(line, font=font)
            draw.text((text_x - text_width // 2, text_y), line, fill="black", font=font)
            text_y += 30  # Move down for the next line

        # Save the new QR code to a temporary file
        logging.info("Menyimpan gambar QR code sementara...")
        new_qr_filename = f"uploads/qr_code/{checkpoint.checkpoints_code.replace('/', '-').replace(' ', '').lower()}.png"
        new_qr_filepath = os.path.join(os.getcwd(), new_qr_filename)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(new_qr_filepath), exist_ok=True)

        new_img.save(new_qr_filepath, format="PNG")

        # Update the checkpoint's checkpoint_qrcode field
        checkpoint.checkpoint_qrcode = new_qr_filename
        db.session.commit()

        return jsonify({"message": "QR code regenerated successfully!", "checkpoint": checkpoint.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error dalam regenerate_qr_code: {str(e)}")
        return jsonify({"error": f"Failed to regenerate QR code: {str(e)}"}), 500

def generate_checkpoints_code():
    """Generate a random checkpoints code without using random or string modules."""
    year = datetime.now().year
    date_part = datetime.now().strftime('%Y-%m-%d')

    # Generate a random string manually
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    random_string = ''
    for _ in range(8):  # Generate 8 random characters
        index = int((len(characters) - 1) * (hash(str(datetime.now())) % 100) / 100)  # Simple hash-based random index
        random_string += characters[index % len(characters)]

    checkpoints_code = f"{year}/{random_string}/{date_part}"  # Format: tahun/string acak/tanggal
    return checkpoints_code





@checkpoints_bp.route('/', methods=['POST'])
def create_checkpoint():
    """
    Create a new checkpoint with a QR code.
    The QR code will be 300x300 pixels with text below it showing the checkpoint name and customer name,
    with a white background and padding.
    """
    try:
        data = request.form
        photo = request.files.get('photo')

        # Save photo if exists
        photo_filename = None
        if photo:
            secure_name = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, secure_name)
            photo.save(photo_path)
            photo_filename = f'uploads/{secure_name}'

        # Timezone Asia/Jakarta
        jakarta_timezone = timezone('Asia/Jakarta')
        current_time = datetime.now(jakarta_timezone)

        # Generate checkpoints_code using the new function
        checkpoints_code = generate_checkpoints_code()

        # Ambil customer_id dari data
        qr_customer_id = data.get("customer_id")
        if not qr_customer_id:
            return jsonify({"error": "customer_id is required"}), 400

        # Ambil name dari model Customer berdasarkan customer_id
        customer = Customer.query.filter_by(customer_id=qr_customer_id).first()
        if not customer:
            return jsonify({"error": f"Customer with customer_id {qr_customer_id} not found"}), 404
        customer_name = customer.name

        # Ambil checkpoints_name dari data
        checkpoints_name = data.get("checkpoints_name")
        if not checkpoints_name:
            return jsonify({"error": "checkpoints_name is required"}), 400

        # Log the text that will be added
        logging.info(f"Checkpoint Name: {checkpoints_name}")
        logging.info(f"Customer Name: {customer_name}")

        # Generate QR Code locally with size 300x300 pixels
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=13,  # Adjusted to make QR code approximately 300x300 pixels
            border=1,
        )
        qr_data = checkpoints_code
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.convert("RGB")  # Convert to RGB to add text
        img = img.resize((300, 300), Image.Resampling.LANCZOS)  # Ensure QR code is exactly 300x300 pixels

        # Tambahkan logo NES di tengah
        try:
            logo_path = os.path.join(os.getcwd(), "static", "nes_logo.png")  # Sesuaikan path ke file logo
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = min(img.size[0], img.size[1]) // 3  # Logo 1/3 dari ukuran QR
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            logo_position = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
            img.paste(logo, logo_position, logo)  # Gunakan logo sebagai mask untuk transparansi
        except Exception as e:
            logging.warning(f"Failed to load logo: {str(e)}. Proceeding without logo.")

        # Add text below the QR code
        img_width, img_height = img.size  # Should be 300x300 pixels
        padding = 40  # Increased padding for better spacing around QR code and text
        text_height = 80  # Estimated height for two lines of text
        new_height = img_height + text_height + padding * 2  # Extra padding at top and bottom
        new_width = img_width + padding * 2  # Extra padding on left and right

        # Create a new image with a white background and additional space for text
        new_img = Image.new("RGB", (new_width, new_height), "white")
        # Center the QR code in the new image
        qr_x = (new_width - img_width) // 2  # Center horizontally
        qr_y = padding  # Add padding at the top
        new_img.paste(img, (qr_x, qr_y))  # Paste the QR code with padding

        # Add text
        draw = ImageDraw.Draw(new_img)

        # Use default font or download a custom font
        try:
            font_url = "https://fonts.googleapis.com/css2?family=Roboto:wght@500&display=swap"
            font_file_url = "https://fonts.gstatic.com/s/roboto/v27/KFOlCnqEu92Fr1MmWUlfBBc4.woff2"
            font_response = requests.get(font_file_url, timeout=10)
            font_response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".woff2") as temp_font_file:
                temp_font_file.write(font_response.content)
                temp_font_path = temp_font_file.name

            font = ImageFont.truetype(temp_font_path, 20)
        except Exception as e:
            logging.warning(f"Gagal mengunduh font: {str(e)}. Menggunakan font default.")
            font = ImageFont.load_default()

        # Add checkpoint name and customer name
        text_y = img_height + padding + 5  # Distance from QR code to text
        text_x = new_width // 2  # Center of the image

        # Wrap text if too long
        max_width = img_width - 10  # Maximum text width
        wrapped_checkpoint_name = textwrap.wrap(checkpoints_name, width=20)
        wrapped_customer_name = textwrap.wrap(customer_name, width=25)

        # Draw checkpoint name line by line
        for line in wrapped_checkpoint_name:
            text_width = draw.textlength(line, font=font)
            draw.text((text_x - text_width // 2, text_y), line, fill="black", font=font)
            text_y += 30  # Move down for the next line

        # Draw customer name line by line
        for line in wrapped_customer_name:
            text_width = draw.textlength(line, font=font)
            draw.text((text_x - text_width // 2, text_y), line, fill="black", font=font)
            text_y += 30  # Move down for the next line

        # Simpan QR code ke file
        qr_filename = f"uploads/qr_code/{checkpoints_code.replace('/', '-').replace(' ', '').lower()}.png"
        qr_filepath = os.path.join(os.getcwd(), qr_filename)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(qr_filepath), exist_ok=True)

        new_img.save(qr_filepath, format="PNG")
        logging.info(f"Gambar QR code disimpan di: {qr_filepath}")

        # Set the checkpoint_qrcode path
        checkpoint_qrcode_path = qr_filename

        # Siapkan data untuk database
        checkpoint_data = {
            "checkpoints_code": checkpoints_code,
            "urutan": data.get("urutan"),
            "todo_list": data.get("todo_list"),
            "duration": data.get("duration"),
            "checkpoints_name": checkpoints_name,
            "id_area_patroli": data.get("id_area_patroli"),
            "shift_id": data.get("shift_id"),
            "customer_id": qr_customer_id,
            "photo": photo_filename,
            "created_login": current_time,
            "created_cookies": current_time,
            "building_name": customer_name,  # Simpan name dari Customer
            "checkpoint_qrcode": checkpoint_qrcode_path,
            "created_at": current_time,
            "updated_at": current_time,
        }

        checkpoint = Checkpoint(**checkpoint_data)
        db.session.add(checkpoint)
        db.session.commit()

        return jsonify({"message": "Checkpoint created successfully!", "checkpoint": checkpoint.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create checkpoint: {str(e)}"}), 500
        

@checkpoints_bp.route('/download-qr/<string:formatted_code>', methods=['GET'])
def download_qr_code(formatted_code):
    """
    Endpoint untuk mengunduh QR code berdasarkan checkpoints_code dalam format: '2025-6v0ztx3f-2025-01-03'.
    """
    try:
        # Lokasi file QR code
        qr_filename = f"{formatted_code}.png"
        qr_filepath = os.path.join(os.getcwd(), "uploads/qr_code/", qr_filename)

        # Periksa apakah file ada
        if not os.path.exists(qr_filepath):
            return jsonify({"error": "QR code file not found"}), 404

        # Kirim file sebagai respons
        return send_file(qr_filepath, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"Failed to download QR code: {str(e)}"}), 500
        
@checkpoints_bp.route('/code/<string:formatted_code>', methods=['GET'])
def get_checkpoint_by_code(formatted_code):
    """
    Retrieve checkpoint data by formatted checkpoints_code.
    Replace '---' with space and '--' with slash in checkpoints_code.
    """
    try:
        # Replace custom formatting back to original format
        checkpoints_code = formatted_code.replace('---', ' ').replace('--', '/')

        # Query the database
        checkpoint = Checkpoint.query.filter_by(checkpoints_code=checkpoints_code).first()
        if not checkpoint:
            return jsonify({"error": "Checkpoint not found"}), 404

        return jsonify(checkpoint.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve checkpoint", "details": str(e)}), 500



@checkpoints_bp.route('/', methods=['GET'])
def get_checkpoints():
    checkpoints = Checkpoint.query.all()
    return jsonify([checkpoint.to_dict() for checkpoint in checkpoints])

@checkpoints_bp.route('/<int:id>', methods=['GET'])
def get_checkpoint_by_id(id):
    try:
        checkpoint = Checkpoint.query.get(id)
        if checkpoint:
            return jsonify(checkpoint.to_dict()), 200

        checkpoints_by_customer = Checkpoint.query.filter_by(customer_id=id).all()
        if checkpoints_by_customer:
            return jsonify([checkpoint.to_dict() for checkpoint in checkpoints_by_customer]), 200

        checkpoints_by_shift = Checkpoint.query.filter_by(shift_id=id).all()
        if checkpoints_by_shift:
            return jsonify([checkpoint.to_dict() for checkpoint in checkpoints_by_shift]), 200

        return jsonify({"error": "Checkpoint not found"}), 404

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": f"Failed to retrieve checkpoint: {str(e)}"}), 500




def fetch_customer_data(customer_id):
    """
    Fetch customer data from the /customers endpoint.
    """
    try:
        customer_url = f"https://backend.nes-sipandu.com/api/customers/{customer_id}"
        response = requests.get(customer_url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.Timeout:
        logging.error("Timeout saat menghubungi API backend untuk customer data.")
        return None
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as err:
        logging.error(f"Error occurred: {err}")
        return None


@checkpoints_bp.route('/<int:id>', methods=['PUT'])
def update_checkpoint(id):
    checkpoint = Checkpoint.query.get(id)
    if not checkpoint:
        return jsonify({"error": "Checkpoint not found"}), 404

    data = request.form
    photo = request.files.get('photo')

    # Update photo if exists
    if photo:
        old_photo_path = os.path.join(os.getcwd(), checkpoint.photo) if checkpoint.photo else None
        secure_name = secure_filename(photo.filename)
        new_photo_path = os.path.join(UPLOAD_FOLDER, secure_name)
        photo.save(new_photo_path)
        delete_file(old_photo_path)
        checkpoint.photo = f'uploads/{secure_name}'

    for key in ['checkpoints_code', 'urutan', 'todo_list', 'duration', 'checkpoints_name', 'id_area_patroli', 'shift_id', 'customer_id', 'building_name']:
        if key in data:
            setattr(checkpoint, key, data.get(key))

    checkpoint.updated_at = datetime.now(timezone('Asia/Jakarta'))
    db.session.commit()
    return jsonify({"message": "Checkpoint updated successfully!", "checkpoint": checkpoint.to_dict()})

@checkpoints_bp.route('/<int:id>', methods=['DELETE'])
def delete_checkpoint(id):
    try:
        checkpoint = Checkpoint.query.get(id)
        if not checkpoint:
            return jsonify({"error": "Checkpoint not found"}), 404

        # Delete photo if exists
        if checkpoint.photo:
            photo_path = os.path.join(os.getcwd(), checkpoint.photo)
            delete_file(photo_path)

        # Delete QR Code if exists
        if checkpoint.checkpoints_code:
            qr_filename = f"uploads/{checkpoint.checkpoints_code.replace('/', '-').lower()}.png"
            qr_path = os.path.join(os.getcwd(), qr_filename)
            delete_file(qr_path)

        db.session.delete(checkpoint)
        db.session.commit()

        return jsonify({"message": "Checkpoint deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete checkpoint: {str(e)}"}), 500


    """
    Retrieve checkpoint data by employee_id and checkpoint_date.
    """
    try:
        employee_id = request.args.get('employee_id', type=int)
        checkpoint_date_str = request.args.get('checkpoint_date')
        
        if not employee_id or not checkpoint_date_str:
            return jsonify({"error": "employee_id and checkpoint_date are required"}), 400

        # Convert checkpoint_date_str to datetime object
        checkpoint_date = datetime.strptime(checkpoint_date_str, '%Y-%m-%d')

        # Query the database
        checkpoints = Checkpoint.query.filter_by(employee_id=employee_id, checkpoint_date=checkpoint_date).all()
        if not checkpoints:
            return jsonify({"error": "No checkpoints found for the given employee_id and checkpoint_date"}), 404

        return jsonify([checkpoint.to_dict() for checkpoint in checkpoints]), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to retrieve checkpoint", "details": str(e)}), 500