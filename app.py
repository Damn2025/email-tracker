from flask import Flask, Response, request
import logging
from datetime import datetime

from my_action import perform_action
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)

# A 1x1 transparent GIF image in binary format
# This is a standard way to represent a tracking pixel
pixel_data = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00'
    b'\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
)

@app.route('/track/<user_id>')
def track_email(user_id):
    """
    This function is called when a tracking pixel is loaded.
    It logs the event and returns the pixel image.
    """
    try:
        # Get user's IP address from the request
        ip_address = request.remote_addr
        
        # Log the email open event. You could save this to a database instead.
        log_message = f"Email opened! User ID: {user_id}, IP: {ip_address}, Time: {datetime.now()}"
        logging.info(log_message)
        
    except Exception as e:
        logging.error(f"Error logging event: {e}")

    # Return the transparent GIF as a response with the correct mimetype
    return Response(pixel_data, mimetype='image/gif')

@app.route('/action/<user_id>')
def handle_action(user_id):
    """This endpoint is for link clicks to trigger a custom action."""
    perform_action(user_id)
    # You can redirect the user to a specific page after the action
    return "Action logged. You can be redirected."

if __name__ == '__main__':
    # Run the server. In a production environment, you would use a more robust
    # server like Gunicorn or uWSGI.
    app.run(debug=True)