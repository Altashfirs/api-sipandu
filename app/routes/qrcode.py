from flask import Blueprint, jsonify, request, send_file
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap
import tempfile
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Blueprint for QR code generation
qr_bp = Blueprint('qr', __name__, url_prefix='/api/qr')

@qr_bp.route('/generate', methods=['GET'])
def generate_qr():
    """
    Menghasilkan kode QR dengan teks checkpoint_code dan building_name di bawahnya.
    Tidak menggunakan API backend, melainkan data dummy.
    """
    try:
        # Ambil parameter dari query string
        data = request.args.get('data', '')  # Checkpoint code
        checkpoint_name = request.args.get('checkpoint_name', '')
        customer_id = request.args.get('customer_id', '')
        size = int(request.args.get('size', 300))  # Ukuran QR code

        # Validasi parameter
        if not data:
            return jsonify({"error": "Parameter 'data' tidak boleh kosong"}), 400
        if not customer_id:
            return jsonify({"error": "Parameter 'customer_id' tidak boleh kosong"}), 400
        if not checkpoint_name:
            return jsonify({"error": "Parameter 'checkpoint_name' tidak boleh kosong"}), 400

        # Gunakan data dummy sebagai pengganti API backend
        logging.info(f"Menggunakan data dummy untuk customer ID: {customer_id}")
        building_name = f"Gedung Customer {customer_id}"  # Contoh data dummy

        # Buat kode QR
        logging.info("Membuat kode QR...")
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size // 30,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.convert("RGB")  # Konversi ke RGB untuk bisa menambah teks

        # Ukuran gambar QR
        img_width, img_height = img.size
        padding = 20  # Jarak antara QR dan teks
        text_height = 80  # Perkiraan tinggi untuk beberapa baris teks
        new_height = img_height + text_height + padding

        # Buat gambar baru dengan lebih tinggi untuk teks
        new_img = Image.new("RGB", (img_width, new_height), "white")
        new_img.paste(img, (0, 0))  # Tempel QR di atas

        # Tambahkan teks
        draw = ImageDraw.Draw(new_img)

        # URL font online (misalnya dari Google Fonts)
        font_url = "https://fonts.googleapis.com/css2?family=Roboto:wght@500&display=swap"
        font_file_url = "https://fonts.gstatic.com/s/roboto/v27/KFOlCnqEu92Fr1MmWUlfBBc4.woff2"

        # Download font file
        try:
            logging.info("Mengunduh font dari Google Fonts...")
            font_response = requests.get(font_file_url, timeout=10)
            font_response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".woff2") as temp_font_file:
                temp_font_file.write(font_response.content)
                temp_font_path = temp_font_file.name

            # Load font file
            font = ImageFont.truetype(temp_font_path, 20)
        except Exception as e:
            logging.warning(f"Gagal mengunduh font: {str(e)}. Menggunakan font default.")
            font = ImageFont.load_default()

        # Tambahkan teks ke gambar
        text_y = img_height + 5  # Jarak dari QR ke teks
        text_x = img_width // 2  # Tengah gambar

        # Wrap teks jika terlalu panjang
        max_width = img_width - 10  # Lebar maksimum teks agar tidak keluar
        wrapped_data = textwrap.wrap(checkpoint_name, width=20)  # Batasi panjang per baris
        wrapped_building = textwrap.wrap(building_name, width=25)  # Batasi panjang per baris

        # Gambar teks baris per baris
        for line in wrapped_data:
            text_width = draw.textlength(line, font=font)
            draw.text((text_x - text_width // 2, text_y), line, fill="black", font=font)
            text_y += 30  # Geser ke bawah untuk baris berikutnya

        text_y += 10  # Tambahkan jarak antar teks

        for line in wrapped_building:
            text_width = draw.textlength(line, font=font)
            draw.text((text_x - text_width // 2, text_y), line, fill="black", font=font)
            text_y += 30  # Geser ke bawah untuk baris berikutnya

        # Simpan gambar ke buffer
        logging.info("Menyimpan gambar QR code sementara...")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            new_img.save(temp_file, format="PNG")
            temp_file_path = temp_file.name  # Simpan path file

        try:
            # Kirim file sementara
            logging.info("Mengirim file QR code ke client...")
            return send_file(temp_file_path, mimetype='image/png')
        finally:
            # Bersihkan file sementara setelah dikirim
            logging.info("Membersihkan file sementara...")
            os.unlink(temp_file_path)

    except Exception as e:
        logging.error(f"Error dalam generate_qr: {str(e)}")
        return jsonify({"error": f"Failed to generate QR code: {str(e)}"}), 500

@qr_bp.route('/generate/employee', methods=['GET'])
def generate_qr_employees():
    """
    Menghasilkan kode QR berdasarkan data yang diberikan untuk mobile.
    """
    data = request.args.get('data', '')  # Data untuk QR code
    size = int(request.args.get('size', 300))  # Ukuran QR code

    if not data:
        return jsonify({"error": "Parameter 'data' tidak boleh kosong"}), 400

    # Buat kode QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size // 30,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Buat file sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        img.save(tmp.name, format='PNG')
        tmp_file_path = tmp.name

    try:
        # Kirim file sementara
        return send_file(tmp_file_path, mimetype='image/png')
    finally:
        # Bersihkan file sementara setelah dikirim
        os.unlink(tmp_file_path)

