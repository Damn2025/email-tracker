from flask import Flask, Response, request
import logging
import os
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Database connection
def get_db_connection():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

# Create the tracking table if it doesn't exist
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS email_logs (id SERIAL PRIMARY KEY, user_id VARCHAR(255) NOT NULL, ip_address VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        conn.commit()

app = Flask(__name__)
pixel_data = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00'
    b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
)

@app.route('/track/<user_id>')
def track_email(user_id):
    try:
        ip_address = request.remote_addr
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO email_logs (user_id, ip_address) VALUES (%s, %s)", (user_id, ip_address))
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Email open logged for user: {user_id}")
    except Exception as e:
        logging.error(f"Error logging email open: {e}")
    return Response(pixel_data, mimetype='image/gif')

# New endpoint to show live data
@app.route('/logs')
def show_logs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, ip_address, created_at FROM email_logs ORDER BY created_at DESC;")
        logs = cur.fetchall()
        cur.close()
        conn.close()
        
        # Format logs for display
        output = "<h1>Live Email Open Logs</h1>"
        for log in logs:
            output += f"<p>User ID: {log[0]}, IP: {log[1]}, Time: {log[2]}</p>"
        return output
    except Exception as e:
        return f"Error retrieving logs: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)