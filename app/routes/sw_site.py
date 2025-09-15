import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.database import db
from app.models.sw_site import SwSite
from datetime import datetime

sw_site_bp = Blueprint('sw_site', __name__, url_prefix='/api/sw-sites')

@sw_site_bp.route('/', methods=['GET'])
def get_sw_sites():
    try:
        sites = SwSite.query.all()
        return jsonify([site.to_dict() for site in sites])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch sites: {str(e)}"}), 500

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@sw_site_bp.route('/<int:site_id>', methods=['GET'])
def get_sw_site_by_id(site_id):
    try:
        # Query untuk mendapatkan data berdasarkan site_id
        site = SwSite.query.get(site_id)
        if not site:
            return jsonify({"error": "Site not found"}), 404

        # Return data dalam bentuk JSON
        return jsonify(site.to_dict()), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch site: {str(e)}"}), 500


@sw_site_bp.route('/', methods=['POST'])
def create_sw_site():
    try:
        site_url = request.form.get('site_url')
        site_name = request.form.get('site_name')
        site_company = request.form.get('site_company')
        site_manager = request.form.get('site_manager')
        site_director = request.form.get('site_director')
        site_phone = request.form.get('site_phone')
        site_address = request.form.get('site_address')
        site_description = request.form.get('site_description')
        site_email = request.form.get('site_email')
        site_email_domain = request.form.get('site_email_domain')
        gmail_host = request.form.get('gmail_host')
        gmail_username = request.form.get('gmail_username')
        gmail_password = request.form.get('gmail_password')
        gmail_port = request.form.get('gmail_port')
        site_logo = request.files.get('site_logo')

        if not site_url or not site_name or not site_company or not site_manager or not site_phone or not site_address or not site_description or not site_email or not site_email_domain or not gmail_host or not gmail_username or not gmail_password or not gmail_port:
            return jsonify({"error": "Missing required fields"}), 400

        # Simpan file logo jika ada
        logo_path = None
        if site_logo:
            filename = secure_filename(site_logo.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, filename)
            site_logo.save(logo_path)
            logo_path = f'uploads/{filename}'

        # Simpan data ke database
        site = SwSite(
            site_url=site_url,
            site_name=site_name,
            site_company=site_company,
            site_manager=site_manager,
            site_director=site_director,
            site_phone=site_phone,
            site_address=site_address,
            site_description=site_description,
            site_logo=logo_path,
            site_email=site_email,
            site_email_domain=site_email_domain,
            gmail_host=gmail_host,
            gmail_username=gmail_username,
            gmail_password=gmail_password,
            gmail_port=gmail_port,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(site)
        db.session.commit()

        return jsonify({"message": "Site created successfully!", "site": site.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create site: {str(e)}"}), 500

@sw_site_bp.route('/<int:site_id>', methods=['PUT'])
def update_sw_site(site_id):
    site = SwSite.query.get(site_id)
    if not site:
        return jsonify({"error": "Site not found"}), 404

    try:
        # Periksa apakah data dikirim sebagai JSON atau form-data
        if request.is_json:
            data = request.get_json()
            site.site_name = data.get('site_name', site.site_name)
            site.site_description = data.get('site_description', site.site_description)
            site.site_phone = data.get('site_phone', site.site_phone)
            site.site_address = data.get('site_address', site.site_address)
            site.site_email = data.get('site_email', site.site_email)
            site.site_email_domain = data.get('site_email_domain', site.site_email_domain)
            site.site_url = data.get('site_url', site.site_url)
            site.site_company = data.get('site_company', site.site_company)
            site.site_manager = data.get('site_manager', site.site_manager)
            site.site_director = data.get('site_director', site.site_director)
            site.gmail_host = data.get('gmail_host', site.gmail_host)
            site.gmail_username = data.get('gmail_username', site.gmail_username)
            site.gmail_password = data.get('gmail_password', site.gmail_password)
            site.gmail_port = data.get('gmail_port', site.gmail_port)

        elif 'site_logo' in request.files or request.form:
            # Jika data dikirim sebagai form-data
            site.site_name = request.form.get('site_name', site.site_name)
            site.site_description = request.form.get('site_description', site.site_description)
            site.site_phone = request.form.get('site_phone', site.site_phone)
            site.site_address = request.form.get('site_address', site.site_address)
            site.site_email = request.form.get('site_email', site.site_email)
            site.site_email_domain = request.form.get('site_email_domain', site.site_email_domain)
            site.site_url = request.form.get('site_url', site.site_url)
            site.site_company = request.form.get('site_company', site.site_company)
            site.site_manager = request.form.get('site_manager', site.site_manager)
            site.site_director = request.form.get('site_director', site.site_director)
            site.gmail_host = request.form.get('gmail_host', site.gmail_host)
            site.gmail_username = request.form.get('gmail_username', site.gmail_username)
            site.gmail_password = request.form.get('gmail_password', site.gmail_password)
            site.gmail_port = request.form.get('gmail_port', site.gmail_port)

            # Tangkap file logo baru jika ada
            if 'site_logo' in request.files:
                site_logo = request.files['site_logo']
                if site_logo:
                    # Hapus logo lama jika ada
                    if site.site_logo and os.path.exists(os.path.join(os.getcwd(), site.site_logo)):
                        os.remove(os.path.join(os.getcwd(), site.site_logo))
                    
                    # Simpan logo baru
                    filename = secure_filename(site_logo.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    site_logo.save(file_path)
                    site.site_logo = f'uploads/{filename}'  # Simpan path relatif

        # Update waktu terakhir diubah
        site.updated_at = datetime.utcnow()

        # Commit perubahan
        db.session.commit()

        return jsonify({"message": "Site updated successfully!", "site": site.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update site: {str(e)}"}), 500

@sw_site_bp.route('/<int:site_id>', methods=['DELETE'])
def delete_sw_site(site_id):
    site = SwSite.query.get(site_id)
    if not site:
        return jsonify({"error": "Site not found"}), 404

    try:
        # Hapus logo jika ada
        if site.site_logo and os.path.exists(os.path.join(os.getcwd(), site.site_logo)):
            os.remove(os.path.join(os.getcwd(), site.site_logo))

        db.session.delete(site)
        db.session.commit()
        return jsonify({"message": "Site deleted successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete site: {str(e)}"}), 500

