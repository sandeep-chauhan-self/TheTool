import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Setup application logger with rotation (idempotent)"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'app.log')
    
    # Create logger
    logger = logging.getLogger('trading_analyzer')
    logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
    
    # Prevent duplicate handlers if logger already configured
    if logger.hasHandlers():
        return logger
    
    # Create rotating file handler (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    
    # Create console handler (explicit stdout to avoid buffering issues)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
