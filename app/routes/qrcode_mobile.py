from flask import Blueprint, jsonify, request, send_file
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap
import tempfile
import os

qr_bp_mobile = Blueprint('qr_mobile', __name__, url_prefix='/api/qr_mobile')

@qr_bp_mobile.route('/generate', methods=['GET'])
def generate_qr_employees_mobile():
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