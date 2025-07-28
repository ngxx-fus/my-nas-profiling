import requests
from datetime import datetime
import pyrebase
import logging
import time
import os

# Custom FileHandler để giới hạn log còn 100 dòng mới nhất
class TrimmedFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.trim_log_file()

    def trim_log_file(self):
        max_lines = 100
        try:
            with open(self.baseFilename, 'r') as f:
                lines = f.readlines()
            if len(lines) > max_lines:
                with open(self.baseFilename, 'w') as f:
                    f.writelines(lines[-max_lines:])
        except Exception as e:
            print(f"Failed to trim log file: {e}")

# Đường dẫn file log
log_path = '/home/fus/UserApplications/UpdateInfo/ip_update.log'

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        TrimmedFileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Firebase configuration
firebase_config = {
    "apiKey": "***********************************",
    "authDomain": "dummy.firebaseapp.com",
    "databaseURL": "https://my-nas-ip-default-rtdb.asia-southeast1.firebasedatabase.app/",
    "storageBucket": "dummy"
}

# Firebase credentials
firebase_email = "fus-3568@my-nas-ip.iam.gserviceaccount.com"
firebase_password = "Password2@"

# Public IP provider list (fallbacks included)
ip_providers = [
    "https://api.ipify.org",
    "https://ipinfo.io/ip",
    "https://ifconfig.me",
    "https://checkip.amazonaws.com"
]

def get_public_ip():
    logger.info("Entering get_public_ip function")
    for url in ip_providers:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info("Exiting get_public_ip function with IP: %s", response.text.strip())
                return response.text.strip()
        except Exception as e:
            logger.warning("Failed to get IP from %s: %s", url, str(e))
            continue
    logger.info("Exiting get_public_ip function with None")
    return None

def login_firebase():
    logger.info("Entering login_firebase function")
    firebase = pyrebase.initialize_app(firebase_config)
    auth = firebase.auth()
    user = auth.sign_in_with_email_and_password(firebase_email, firebase_password)
    db = firebase.database()
    logger.info("Exiting login_firebase function")
    return db, user

def update_rtdb(db, token, ip_str):
    logger.info("Entering update_rtdb function with IP: %s", ip_str)
    now = datetime.now().strftime("%H:%M:%S-%d/%m/%Y")
    data = {
        "GlobalIp": ip_str,
        "LastUpdate": now,
        "RefreshNow": False
    }
    db.update(data, token)
    logger.info("Exiting update_rtdb function")

def stream_handler(message):
    logger.info("Entering stream_handler with event: %s", message["event"])
    try:
        refresh_now = message["data"]
        if refresh_now is True:
            logger.info("RefreshNow is True, triggering IP update")
            current_ip = get_public_ip()
            if current_ip is None:
                logger.error("Failed to retrieve public IP in stream_handler")
                print("Failed to retrieve public IP.")
                return

            try:
                with open("/home/fus/UserApplications/UpdateInfo/old_global_ip.txt", "r") as f:
                    old_ip = f.read().strip()
            except FileNotFoundError:
                old_ip = None
                logger.warning("old_global_ip.txt not found, setting old_ip to None")

            db, user = login_firebase()
            token = user['idToken']
            update_rtdb(db, token, current_ip)
            with open("old_global_ip.txt", "w") as f:
                f.write(current_ip)
            logger.info("Updated global IP to: %s", current_ip)
            print(f"Updated global IP to: {current_ip}")
        else:
            logger.info("RefreshNow is False, no action taken")
    except Exception as e:
        logger.error("Error in stream_handler: %s", str(e))
        print(f"Error in stream_handler: {str(e)}")
    logger.info("Exiting stream_handler")

def main():
    logger.info("Entering main function")
    db, user = login_firebase()
    token = user['idToken']
    
    try:
        logger.info("Starting Firebase stream for RefreshNow")
        db.child("RefreshNow").stream(stream_handler, token)
    except Exception as e:
        logger.error("Failed to start stream: %s", str(e))
        print(f"Failed to start stream: {str(e)}")
        return

    last_token_refresh = time.time()
    while_deplay = 60
    while True:
        try:
            if time.time() - last_token_refresh > 3000:
                logger.info("Refreshing Firebase token")
                db, user = login_firebase()
                token = user['idToken']
                last_token_refresh = time.time()
                try:
                    db.child("RefreshNow").stream(stream_handler, token)
                except Exception as e:
                    logger.error("Failed to restart stream: %s", str(e))
                    print(f"Failed to restart stream: {str(e)}")
                    time.sleep(while_deplay)
                    continue

            try:
                with open("old_global_ip.txt", "r") as f:
                    old_ip = f.read().strip()
            except FileNotFoundError:
                old_ip = None
                logger.warning("old_global_ip.txt not found, setting old_ip to None")

            current_ip = get_public_ip()
            if current_ip is None:
                logger.error("Failed to retrieve public IP")
                print("Failed to retrieve public IP.")
                time.sleep(while_deplay)
                continue

            if current_ip != old_ip:
                update_rtdb(db, token, current_ip)
                with open("old_global_ip.txt", "w") as f:
                    f.write(current_ip)
                logger.info("Updated global IP to: %s", current_ip)
                print(f"Updated global IP to: {current_ip}")
            else:
                logger.info("Public IP unchanged: %s", current_ip)
                print("Public IP has not changed. No update required.")

        except Exception as e:
            logger.error("Error in main loop: %s", str(e))
            print(f"Error occurred: {str(e)}")

        logger.info("Sleeping for %s seconds", while_deplay)
        time.sleep(while_deplay)

if __name__ == "__main__":
    main()

