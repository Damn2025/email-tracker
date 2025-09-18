from flask import Flask, Response, request
import logging
import os
from datetime import datetime
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- Google Sheets Configuration ---
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

# Create the tracking table if it doesn't exist
def initialize_database():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS email_logs (id SERIAL PRIMARY KEY, user_id VARCHAR(255) NOT NULL, ip_address VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
            conn.commit()

app = Flask(__name__)
pixel_data = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00'
    b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
)

def update_google_sheet(user_id):
    """Updates the Google Sheet with the email open event."""
    try:
        client = gspread.authorize(CREDS)
        # Make sure to use the exact name of your sheet
        sheet = client.open("Copy of n8n Test").worksheet("Test") # Or your specific sheet/tab name
        all_values = sheet.get_all_values()

        # Check if headers exist, if not, add them
        headers = ['name', 'email', 'Send Status', 'Time', 'Status', 'Open Count', 'First Opened', 'Last Opened']
        if not all_values or all_values[0] != headers:
            sheet.insert_row(headers, 1)
            logging.info("Added headers to Google Sheet.")
            all_values.insert(0, headers)  # Update local copy

        # Find user_id in the sheet using the fetched data
        row_num = None
        user_row_data = None
        for i, row in enumerate(all_values):
            # Find the row where the 'email' column (index 1) matches the user_id
            if row and len(row) > 1 and row[1] == user_id: 
                row_num = i + 1
                user_row_data = row
                break

        if not row_num:
            logging.warning(f"Google Sheet: User '{user_id}' not found in the pre-populated list. No action taken.")
            return

        # Get current time in Indian Standard Time (IST)
        ist_timezone = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')
        
        # Safely get current count, default to 0 if the cell is empty or not a number
        try:
            current_count = int(user_row_data[5]) if len(user_row_data) > 5 and user_row_data[5] else 0
        except (ValueError, IndexError):
            current_count = 0

        # Determine the 'First Opened' time. If it's not set, use the current time.
        first_open_time = user_row_data[6] if len(user_row_data) > 6 and user_row_data[6] else now_ist

        # Prepare a batch update for Status, Open Count, First Opened, and Last Opened
        sheet.batch_update([
            {'range': f'E{row_num}', 'values': [['Opened']]},      # Update 'Status' in column E
            {'range': f'F{row_num}', 'values': [[current_count + 1]]}, # Update 'Open Count' in column F
            {'range': f'G{row_num}', 'values': [[first_open_time]]},   # Update 'First Opened' in column G
            {'range': f'H{row_num}', 'values': [[now_ist]]}            # Update 'Last Opened' in column H
        ])
        logging.info(f"Google Sheet: Updated status for user '{user_id}'. New open count: {current_count + 1}.")
    except gspread.exceptions.GSpreadException as e:
        # Catch gspread-specific exceptions to get more detailed error messages
        logging.error(f"GSpread API Error: {e}")
    except Exception as e:
        logging.error(f"Error updating Google Sheet: {e}")

@app.route('/track/<user_id>')
def track_email(user_id):
    try:
        ip_address = request.remote_addr
        # with get_db_connection() as conn:
        #     with conn.cursor() as cur:
        #         cur.execute("INSERT INTO email_logs (user_id, ip_address) VALUES (%s, %s)", (user_id, ip_address))
        #         conn.commit()
        logging.info(f"Email open tracked for user: {user_id}")

        # Update Google Sheet in a background thread to not block the response
        threading.Thread(target=update_google_sheet, args=(user_id,)).start()
    except Exception as e:
        logging.error(f"Error logging email open: {e}")
    return Response(pixel_data, mimetype='image/gif')

# New endpoint to show live data
@app.route('/logs')
def show_logs():
    try:
        # with get_db_connection() as conn:
        #     with conn.cursor() as cur:
        #         cur.execute("SELECT user_id, ip_address, created_at FROM email_logs ORDER BY created_at DESC;")
        #         logs = cur.fetchall()
        
        # Format logs for display
        output = "<h1>Database logging is currently disabled.</h1>"
        logs = [] # Ensure logs is an empty list
        for log in logs:
            output += f"<p>User ID: {log[0]}, IP: {log[1]}, Time: {log[2]}</p>"
        return output
    except Exception as e:
        return f"Error retrieving logs: {e}"

if __name__ == '__main__':
    # initialize_database()
    app.run(host='0.0.0.0', port=5000, debug=True)