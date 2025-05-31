# logger.py

import logging
import os
import glob
from datetime import datetime

def cleanup_old_logs():
    """Remove old log files if there are more than 5 log files in the logs folder."""
    log_files = glob.glob('logs/nutriai_*.log')
    if len(log_files) > 5:
        # Sort by modification time (oldest first)
        log_files.sort(key=os.path.getmtime)
        # Remove the oldest files, keeping only the 5 most recent
        files_to_remove = log_files[:-5]
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
            except OSError:
                pass  # Ignore errors if file can't be removed

def setup_logger(log_file=None):
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Clean up old log files
    cleanup_old_logs()

    # If no log file is specified, create one with a timestamp
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f'logs/nutriai_{timestamp}.log'

    # Create a logger
    logger = logging.getLogger('NutriAI')
    logger.setLevel(logging.DEBUG)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

# Create and configure logger
logger = setup_logger()