import os
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, flash, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()

class WhatsAppSender:
    def __init__(self):
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Use existing Chrome profile
        user_data_dir = os.path.expanduser('~') + "/AppData/Local/Google/Chrome/User Data"
        if os.path.exists(user_data_dir):
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options
        )
    
    def send_message(self, phone_number, message):
        """Send message to a single number"""
        try:
            self.driver.get(f"https://web.whatsapp.com/send?phone={phone_number}&text={message}")
            
            # Wait for page to load and send button to appear
            send_button = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    '//div[@role="button"][@aria-label="Send" or contains(@data-icon,"send")]'
                ))
            )
            send_button.click()
            return True
        except Exception as e:
            print(f"Failed to send to {phone_number}: {str(e)}")
            return False
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

def validate_phone_numbers(numbers):
    """Validate international phone number format"""
    import re
    pattern = r'^\+\d{10,15}$'
    return all(re.match(pattern, num.strip()) for num in numbers)

def background_task(numbers, message, send_time=None, repeat_interval=0, repeat_count=1):
    """Background task to handle message sending"""
    sender = WhatsAppSender()
    try:
        while repeat_count > 0:
            if send_time:
                # Wait until scheduled time
                while datetime.now().strftime("%H:%M") < send_time:
                    time.sleep(10)
            
            for number in numbers:
                if not sender.send_message(number, message):
                    continue
                time.sleep(5)  # Rate limiting
            
            if repeat_interval > 0:
                time.sleep(repeat_interval)
            repeat_count -= 1
    finally:
        sender.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            data = request.get_json() if request.is_json else request.form
            numbers = [num.strip() for num in data.get("numbers", "").split(",") if num.strip()]
            message = data.get("message", "").strip()
            
            if not numbers or not message:
                return jsonify({"error": "Phone numbers and message are required"}), 400
            
            if not validate_phone_numbers(numbers):
                return jsonify({"error": "Invalid phone number format. Use +[country code][number]"}), 400
            
            # Process scheduling options
            send_time = data.get("time")
            repeat = data.get("repeat", "false").lower() == "true"
            repeat_interval = max(60, int(data.get("interval", 3600))) if repeat else 0
            repeat_count = max(1, int(data.get("count", 1))) if repeat else 1
            
            # Start background task
            thread = threading.Thread(
                target=background_task,
                args=(numbers, message, send_time, repeat_interval, repeat_count),
                daemon=True
            )
            thread.start()
            
            return jsonify({"success": "Messages are being sent in the background"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return render_template("index.html")

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, threaded=True)