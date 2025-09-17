import logging
from datetime import datetime

import pytz

def perform_action(user_id):
    """A placeholder function to log a custom action, like a link click."""
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time_ist = datetime.now(ist_timezone)
    log_message = f"Action triggered! User ID: {user_id}, Time: {current_time_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    logging.info(log_message)