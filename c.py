from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "path/to/your/service_account.json"  # Update with your credentials
SPREADSHEET_NAME = "User Registrations"

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
gc = gspread.authorize(credentials)
sheet = gc.open(SPREADSHEET_NAME).sheet1  # Access first sheet

# Twilio API Credentials (Update with your Twilio credentials)
TWILIO_SID = "your_twilio_sid"
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_PHONE = "your_twilio_phone_number"

twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Email Setup (Update with your Email credentials)
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

def send_sms(to_number, message):
    twilio_client.messages.create(to=to_number, from_=TWILIO_PHONE, body=message)

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400
    
    users = sheet.get_all_records()
    for user in users:
        if user["Email"] == email and user["Password"] == password:
            return jsonify({"message": "Login successful", "name": user["Name"]})
    
    return jsonify({"error": "Invalid email or password"}), 401

@app.route("/send_distress", methods=["POST"])
def send_distress():
    data = request.json
    name = data.get("name")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not name or not latitude or not longitude:
        return jsonify({"error": "Missing required fields"}), 400

    message = f"🚨 EMERGENCY ALERT 🚨\n{name} is in distress!\nLocation: {latitude}, {longitude}"
    
    users = sheet.get_all_records()
    for user in users:
        if user["Phone"]:
            send_sms(user["Phone"], message)
        if user["Email"]:
            send_email(user["Email"], "Distress Alert!", message)
    
    return jsonify({"message": "Distress signal sent successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
