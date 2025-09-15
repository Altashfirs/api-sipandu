from flask import Blueprint

def register_routes(app):
    """
    Register all blueprints to the Flask app instance.

    Parameters:
        app (Flask): The Flask application instance.
    """
    # Import blueprints
    from .customers import customers_bp
    from .employees import employees_bp
    from .employees_mobile import employees_mobile_bp  
    from .position import position_bp
    from .shift import shift_bp
    from .area_patroli import area_patroli_bp
    from .user import users_bp
    from .business_card import business_card_bp
    from .matrix_routes import matrix_bp
    from .question import question_bp
    from .topic import topic_bp
    from .checkpoints import checkpoints_bp
    from .journal_book import journal_book_bp
    from .guest_book import guest_book_bp
    from .handover import handover_bp
    from .sw_site import sw_site_bp
    from .start_test import start_test_bp
    from .results_test import results_test_bp
    from .item_discovery import item_discovery_bp
    from .area import area_bp
    from .area_mobile import area_mobile_bp
    from .vehicle_book import vehicle_book_bp
    from .add_vehicle import add_vehicle_bp
    from .add_vehicle_mobile import add_vehicle_mobile_bp
    from .patrol_logs import patrol_logs_bp
    from .presence import presence_bp
    from .msp_table import msp_table_bp
    from .urgent_mobile import urgent_mobile_bp
    from .notifikasi import notifikasi_bp
    from .vehicle_book_mobile import vehicle_book_mobile_bp  # Import blueprint yang baru
    from .urgent import urgent_bp
    from .qrcode import qr_bp
    from .qrcode_mobile import qr_bp_mobile
    from .msp_log import msp_log_bp
    from .feedback import feedback_bp
    from .soal_surat import soal_surat_bp
    from .msp_log_baru import msp_log_bp_baru
    from .msp_log_answer import msp_log_answer_bp
    from .turn_over import turn_over_bp
    from .absence import absence_bp
    from .template_rekap import template_rekap_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(employees_bp, url_prefix='/api/employees')
    app.register_blueprint(employees_mobile_bp, url_prefix='/api/employees_mobile')  
    app.register_blueprint(position_bp, url_prefix='/api/positions')
    app.register_blueprint(shift_bp, url_prefix='/api/shifts')
    app.register_blueprint(area_patroli_bp, url_prefix='/api/area-patroli')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(business_card_bp, url_prefix='/api/thema-cards')
    app.register_blueprint(matrix_bp, url_prefix='/api/matrix')
    app.register_blueprint(question_bp, url_prefix='/api/questions')
    app.register_blueprint(topic_bp, url_prefix='/api/topic')
    app.register_blueprint(checkpoints_bp, url_prefix='/api/checkpoints')
    app.register_blueprint(journal_book_bp, url_prefix='/api/journal_book')
    app.register_blueprint(guest_book_bp, url_prefix='/api/guest_book')
    app.register_blueprint(handover_bp, url_prefix='/api/handover')
    app.register_blueprint(sw_site_bp, url_prefix='/api/sw_sites')
    app.register_blueprint(start_test_bp, url_prefix='/api/start_tests')
    app.register_blueprint(results_test_bp, url_prefix='/api/results_test')
    app.register_blueprint(item_discovery_bp, url_prefix='/api/item_discovery')
    app.register_blueprint(vehicle_book_bp, url_prefix='/api/vehicle_book')
    app.register_blueprint(area_bp, url_prefix='/api/areas')
    app.register_blueprint(add_vehicle_bp, url_prefix='/api/add_vehicle')
    app.register_blueprint(add_vehicle_mobile_bp, url_prefix='/api/add_vehicle_mobile')
    app.register_blueprint(patrol_logs_bp, url_prefix='/api/patrol_logs')
    app.register_blueprint(presence_bp, url_prefix='/api/presence')
    app.register_blueprint(msp_table_bp, url_prefix='/api/msp_table')
    app.register_blueprint(urgent_mobile_bp, url_prefix='/api/urgent_mobile')
    app.register_blueprint(notifikasi_bp, url_prefix='/api/notifikasi')
    app.register_blueprint(area_mobile_bp)  # Daftarkan blueprint
    app.register_blueprint(vehicle_book_mobile_bp)  # Daftarkan blueprint
    app.register_blueprint(urgent_bp, url_prefix='/api/urgent')
    app.register_blueprint(qr_bp, url_prefix='/api/qr')
    app.register_blueprint(qr_bp_mobile, url_prefix='/api/qr_mobile')
    app.register_blueprint(msp_log_bp, url_prefix='/api/msp_log')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(soal_surat_bp, url_prefix='/api/soal_surat')
    app.register_blueprint(msp_log_bp_baru, url_prefix='/api/msp_log_baru')
    app.register_blueprint(msp_log_answer_bp, url_prefix='/api/msp_log_answer')
    app.register_blueprint(turn_over_bp, url_prefix='/api/turn_over')
    app.register_blueprint(absence_bp, url_prefix='/api/absence')
    app.register_blueprint(template_rekap_bp, url_prefix='/api/template_rekap')
    
