from flask import Flask, Response, request, render_template
import logging
import os
import json
from datetime import datetime
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import threading
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- Google Sheets Configuration ---
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']

private_key_b64 = os.environ.get("GCP_PRIVATE_KEY_B64")
private_key = base64.b64decode(private_key_b64).decode("utf-8") if private_key_b64 else os.environ.get("GCP_PRIVATE_KEY", "").replace('\\n', '\n')

creds_json = {
    "type": "service_account",
    "project_id": os.environ.get("GCP_PROJECT_ID"),
    "private_key_id": os.environ.get("GCP_PRIVATE_KEY_ID"),
    "private_key": private_key,
    "client_email": os.environ.get("GCP_CLIENT_EMAIL"),
    "client_id": os.environ.get("GCP_CLIENT_ID"),
}

CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

# Initialize DB
def initialize_database():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    ip_address VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

app = Flask(__name__)

pixel_data = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00'
    b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
)

# ✅ Helper: Convert column index → letter
def get_column_letter(index):
    letter = ''
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter

def update_google_sheet(user_id, spreadsheet_name, worksheet_name):
    try:
        client = gspread.authorize(CREDS)
        sheet = client.open(spreadsheet_name).worksheet(worksheet_name)

        all_values = sheet.get_all_values()

        headers_expected = ['name', 'email', 'Send Status', 'Time', 'Status', 'Open Count', 'First Opened', 'Last Opened']

        if not all_values:
            sheet.insert_row(headers_expected, 1)
            logging.info("Headers inserted in empty sheet.")
            return

        headers = all_values[0]

        # ✅ Create case-insensitive header map
        header_map = {h.strip().lower(): i + 1 for i, h in enumerate(headers)}

        # Required columns
        status_col = header_map.get('status')
        count_col = header_map.get('open count')
        first_open_col = header_map.get('first opened')
        last_open_col = header_map.get('last opened')
        email_col = header_map.get('email')

        if not all([status_col, count_col, first_open_col, last_open_col, email_col]):
            logging.error("Missing required columns in sheet.")
            return

        # 🔍 Find user row
        row_num = None
        user_row_data = None

        for i, row in enumerate(all_values[1:], start=2):  # skip header
            if len(row) >= email_col and row[email_col - 1] == user_id:
                row_num = i
                user_row_data = row
                break

        if not row_num:
            logging.warning(f"User '{user_id}' not found in sheet.")
            return

        # 🕒 Time in IST
        ist_timezone = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')

        # 📊 Current count
        try:
            current_count = int(user_row_data[count_col - 1]) if len(user_row_data) >= count_col and user_row_data[count_col - 1] else 0
        except:
            current_count = 0

        # 🕒 First open logic
        first_open_time = (
            user_row_data[first_open_col - 1]
            if len(user_row_data) >= first_open_col and user_row_data[first_open_col - 1]
            else now_ist
        )

        # 🔤 Convert to letters
        status_letter = get_column_letter(status_col)
        count_letter = get_column_letter(count_col)
        first_letter = get_column_letter(first_open_col)
        last_letter = get_column_letter(last_open_col)

        # 🚀 Batch update
        sheet.batch_update([
            {'range': f'{status_letter}{row_num}', 'values': [['Opened']]},
            {'range': f'{count_letter}{row_num}', 'values': [[current_count + 1]]},
            {'range': f'{first_letter}{row_num}', 'values': [[first_open_time]]},
            {'range': f'{last_letter}{row_num}', 'values': [[now_ist]]}
        ])

        logging.info(f"Updated user '{user_id}' | Count: {current_count + 1}")

    except gspread.exceptions.GSpreadException as e:
        error_details = getattr(e.response, 'text', 'No details available')
        logging.error(f"GSpread API Error: {e} | {error_details}")
    except Exception as e:
        logging.error(f"General Error: {e}")

@app.route('/track/<spreadsheet_name>/<worksheet_name>/<user_id>')
def track_email(spreadsheet_name, worksheet_name, user_id):
    try:
        ip_address = request.remote_addr

        logging.info(f"Email open tracked for user: {user_id} in sheet: {spreadsheet_name}/{worksheet_name}")

        threading.Thread(
            target=update_google_sheet,
            args=(user_id, spreadsheet_name, worksheet_name)
        ).start()

    except Exception as e:
        logging.error(f"Tracking error: {e}")

    return Response(pixel_data, mimetype='image/gif')

@app.route('/dashboard/<spreadsheet_name>/<worksheet_name>')
def show_dashboard(spreadsheet_name, worksheet_name):
    try:
        client = gspread.authorize(CREDS)
        sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
        all_data = sheet.get_all_values()

        if not all_data:
            return render_template('dashboard.html', error="No data found.")

        headers = all_data[0]
        rows = all_data[1:]

        return render_template(
            'dashboard.html',
            headers=headers,
            rows=rows,
            sheet_name=f"{spreadsheet_name} / {worksheet_name}"
        )

    except Exception as e:
        return render_template('dashboard.html', error=f"Error: {e}")

if __name__ == '__main__':
    # initialize_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
