import logging
from datetime import datetime

def perform_action(user_id):
    """A placeholder function to log a custom action, like a link click."""
    log_message = f"Action triggered! User ID: {user_id}, Time: {datetime.now()}"
    logging.info(log_message)