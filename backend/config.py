import os
from datetime import timedelta

# File upload configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB default
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'doc', 'docx'}

# JWT configuration
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION', 24))  # hours
JWT_REFRESH_DELTA = timedelta(hours=JWT_EXPIRATION)

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Evaluation configuration
PLAGIARISM_THRESHOLD = float(os.environ.get('PLAGIARISM_THRESHOLD', 0.80))
MIN_SIMILARITY_PERCENTAGE = float(os.environ.get('MIN_SIMILARITY_PERCENTAGE', 0.0))

# File cleanup
KEEP_UPLOADED_FILES = os.environ.get('KEEP_UPLOADED_FILES', 'false').lower() == 'true'

# Rate limiting
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 10))  # per minute
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 60))  # seconds
