from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from app.models.employees import Employee
from app.models.shift import Shift
from app.models.notifikasi import Notification
from app import db
import requests
import logging

FCM_SERVER_KEY = "BLeNHWJf0E85Z7rii8MFMtl0NP7IlwCiGWL35rCcTHJX3XSZhuflGMsTCDup949NivEm2kr-_8zIJpsDyeypTqo"  # Isi dengan FCM Server Key

# Konfigurasi logging untuk memantau scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_fcm_notification(fcm_token, title, body):
    """Fungsi untuk mengirimkan notifikasi FCM."""
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": fcm_token,
        "notification": {
            "title": title,
            "body": body,
        },
    }
    response = requests.post("https://fcm.googleapis.com/fcm/send", json=payload, headers=headers)
    return response.json()

def send_notification(employee_id, message, notification_type):
    """Fungsi untuk membuat dan mengirimkan notifikasi baru."""
    try:
        notification = Notification(
            employees_id=employee_id,
            message=message,
            type=notification_type,
        )
        db.session.add(notification)
        db.session.commit()
        
        # Ambil token FCM karyawan
        employee = Employee.query.get(employee_id)
        if employee and employee.fcm_token:
            send_fcm_notification(employee.fcm_token, "Scheduled Notification", message)
        return notification
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending notification: {str(e)}")
        return None

def schedule_notifications():
    """Fungsi untuk menjadwalkan pengiriman notifikasi dengan APScheduler."""
    try:
        employees = Employee.query.all()  # Ambil semua karyawan
        
        now = datetime.utcnow()

        for employee in employees:
            if employee.shift_id:
                shift = Shift.query.get(employee.shift_id)
                
                if shift:
                    # Ambil waktu `time_in` dan `time_out` dari shift
                    time_in = datetime.strptime(shift.time_in, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)
                    time_out = datetime.strptime(shift.time_out, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)

                    # 10 menit sebelum waktu masuk
                    ten_minutes_before_in = time_in - timedelta(minutes=10)
                    if ten_minutes_before_in > now:
                        scheduler.add_job(
                            send_notification, 
                            DateTrigger(run_date=ten_minutes_before_in),
                            args=[employee.id, f"Halo {employee.name}, waktu kehadiran Anda dalam 10 menit. Harap datang tepat waktu.", "info"],
                            id=f"{employee.id}_time_in_10min"
                        )

                    # Waktu masuk
                    if time_in > now:
                        scheduler.add_job(
                            send_notification, 
                            DateTrigger(run_date=time_in),
                            args=[employee.id, f"Halo {employee.name}, waktu kehadiran telah dimulai. Harap hadir sekarang.", "info"],
                            id=f"{employee.id}_time_in"
                        )

                    # 10 menit sebelum waktu pulang
                    ten_minutes_before_out = time_out - timedelta(minutes=10)
                    if ten_minutes_before_out > now:
                        scheduler.add_job(
                            send_notification, 
                            DateTrigger(run_date=ten_minutes_before_out),
                            args=[employee.id, f"Halo {employee.name}, waktu pulang Anda dalam 10 menit. Selesaikan pekerjaan Anda.", "info"],
                            id=f"{employee.id}_time_out_10min"
                        )

                    # Waktu pulang
                    if time_out > now:
                        scheduler.add_job(
                            send_notification, 
                            DateTrigger(run_date=time_out),
                            args=[employee.id, f"Halo {employee.name}, waktu pulang telah tiba. Harap segera melakukan presensi pulang.", "info"],
                            id=f"{employee.id}_time_out"
                        )

    except Exception as e:
        logger.error(f"Error scheduling notifications: {str(e)}")

# Fungsi untuk menjalankan scheduler dalam thread terpisah
def run_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()
    schedule_notifications()
