import os
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file(file, max_size=MAX_FILE_SIZE):
    """
    Validate uploaded file.
    
    Args:
        file: Werkzeug FileStorage object
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not file or file.filename == '':
        return False, 'No file selected'
    
    if not allowed_file(file.filename):
        return False, f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f'File size exceeds maximum of {max_mb:.1f}MB'
    
    if file_length == 0:
        return False, 'File is empty'
    
    return True, None


def validate_student_data(student_name, file):
    """
    Validate student data.
    
    Args:
        student_name: Student name string
        file: Werkzeug FileStorage object
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if not student_name or len(student_name.strip()) == 0:
        return False, 'Student name is required'
    
    if len(student_name.strip()) > 255:
        return False, 'Student name too long (max 255 characters)'
    
    is_valid, error = validate_file(file)
    return is_valid, error


def secure_filename_safe(filename, max_length=200):
    """
    Create a secure filename with length limits.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
    """
    safe_name = secure_filename(filename)
    if len(safe_name) > max_length:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        name = name[:max_length - len(ext) - 1]
        safe_name = f"{name}.{ext}" if ext else name
    return safe_name or 'file'
