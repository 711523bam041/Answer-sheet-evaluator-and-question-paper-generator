import logging
import os
from logging.handlers import RotatingFileHandler
from config import LOG_LEVEL

def setup_logging(app):
    """Set up application logging."""
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Remove default handler
    app.logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    app.logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    app.logger.addHandler(console_handler)
    
    # Set app logger level
    app.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    app.logger.info(f"Logging initialized at level {LOG_LEVEL}")
    return app.logger
