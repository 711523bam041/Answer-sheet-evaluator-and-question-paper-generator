from flask import Flask, request, jsonify, Response, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import uuid
import logging

load_dotenv()

from models import db, User, Result, QuestionPaper, ActivityLog, LoginHistory, SimilarityFlag
from reports import (
    generate_student_report,
    generate_faculty_report,
    generate_class_report,
    generate_similarity_report,
    generate_flagged_report
)
from evaluator import evaluate_and_check_plagiarism, _calculate_grade
from paper_generator import generate_paper, generate_paper_pdf, parse_paper_template
from validators import validate_file, validate_student_data
from logger import setup_logging
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, KEEP_UPLOADED_FILES

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

log = setup_logging(app)

# Cache-Control header to prevent back-button access post logout
@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

# JWT Error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    log.warning("Token expired for user")
    return jsonify({'message': 'Token has expired', 'error': 'token_expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    log.warning(f"Invalid token error: {error}")
    return jsonify({'message': 'Invalid token', 'error': 'invalid_token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    log.warning(f"Missing token error: {error}")
    return jsonify({'message': 'Authorization token is missing', 'error': 'missing_token'}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    log.warning("Token revoked")
    return jsonify({'message': 'Token has been revoked', 'error': 'token_revoked'}), 401

# Helper function for audit activity logging
def log_activity(user_id, username, user_role, action, details=None):
    try:
        log_entry = ActivityLog(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        log.error(f"Failed to log activity {action}: {e}")
        db.session.rollback()

# Role-based Decorator for Admin-only routes
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            try:
                user_id = int(get_jwt_identity())
                user = User.query.get(user_id)
                if not user or user.role != 'admin' or not user.is_active:
                    return jsonify({'message': 'Admin privileges required', 'error': 'forbidden'}), 403
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({'message': 'Authorization failed', 'error': 'forbidden'}), 403
        return decorator
    return wrapper

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.before_request
def initialize_database():
    """Initialize database and seed default admin user on startup."""
    if not hasattr(app, 'db_initialized'):
        try:
            with app.app_context():
                db.create_all()
                # Seed default admin user if no admin exists
                admin_user = User.query.filter_by(role='admin').first()
                if not admin_user:
                    hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
                    default_admin = User(
                        username='admin',
                        email='admin@evaluator.edu',
                        password=hashed_pw,
                        role='admin',
                        is_active=True
                    )
                    db.session.add(default_admin)
                    db.session.commit()
                    log.info("Default admin user created: username='admin'")

                app.db_initialized = True
                log.info("Database initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize database: {str(e)}", exc_info=True)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'ok',
            'message': 'API is running',
            'database': 'connected'
        }), 200
    except Exception as e:
        log.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Database connection failed'
        }), 503

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new faculty or admin user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'faculty').strip().lower()

        if not username or not password:
            return jsonify({'message': 'Username and password are required', 'error': 'missing_fields'}), 400

        if len(username) < 3 or len(username) > 150:
            return jsonify({'message': 'Username must be between 3 and 150 characters', 'error': 'invalid_username'}), 400

        if len(password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters', 'error': 'weak_password'}), 400

        if role not in ['faculty', 'admin']:
            role = 'faculty'

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return jsonify({'message': 'Username already exists', 'error': 'username_taken'}), 409

        if email:
            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                return jsonify({'message': 'Email address already registered', 'error': 'email_taken'}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            email=email if email else None,
            password=hashed_password,
            role=role,
            is_active=True
        )
        db.session.add(new_user)
        db.session.commit()

        log.info(f"New user registered: {username} ({role})")
        return jsonify({'message': 'Registration successful', 'username': username, 'role': role}), 201
    
    except Exception as e:
        log.error(f"Registration error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': 'server_error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid username or password.', 'error': 'invalid_credentials'}), 401
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')

        if not username_or_email or not password:
            return jsonify({'message': 'Please enter both username/email and password.', 'error': 'missing_fields'}), 400

        # Support login by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        # Generic error response regardless of whether user exists or password is wrong
        if not user or not user.is_active or not bcrypt.check_password_hash(user.password, password):
            log.warning(f"Failed login attempt for: {username_or_email}")
            return jsonify({'message': 'Invalid username or password.', 'error': 'invalid_credentials'}), 401

        access_token = create_access_token(identity=str(user.id))
        
        # Record Login History & Activity Log
        ip_addr = request.remote_addr
        login_hist = LoginHistory(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            ip_address=ip_addr
        )
        db.session.add(login_hist)
        db.session.commit()

        log_activity(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            action='LOGIN',
            details={'ip_address': ip_addr}
        )

        log.info(f"User logged in: {user.username} ({user.role})")
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        log.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'message': 'Invalid username or password.', 'error': 'invalid_credentials'}), 401

@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    """Log out user and record logout in audit history."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if user:
            # Update latest login history logout_at
            hist = LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.login_at.desc()).first()
            if hist and not hist.logout_at:
                hist.logout_at = datetime.utcnow()
                db.session.commit()

            log_activity(
                user_id=user.id,
                username=user.username,
                user_role=user.role,
                action='LOGOUT',
                details={'timestamp': datetime.utcnow().isoformat()}
            )
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        log.error(f"Logout error: {str(e)}")
        return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get profile of logged-in user."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'message': 'User not found or inactive', 'error': 'unauthorized'}), 401
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch user profile', 'error': 'server_error'}), 500

# ================= Admin Endpoints =================

@app.route('/api/admin/users', methods=['GET'])
@admin_required()
def admin_get_users():
    """List all registered users for Admin."""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify([u.to_dict() for u in users]), 200
    except Exception as e:
        log.error(f"Error fetching users: {str(e)}")
        return jsonify({'message': 'Failed to fetch users', 'error': 'server_error'}), 500

@app.route('/api/admin/users/<int:target_user_id>/toggle-status', methods=['POST'])
@admin_required()
def admin_toggle_user_status(target_user_id):
    """Enable or disable a user account."""
    try:
        admin_id = int(get_jwt_identity())
        admin_user = User.query.get(admin_id)
        target = User.query.get(target_user_id)
        if not target:
            return jsonify({'message': 'User not found', 'error': 'not_found'}), 404

        if target.id == admin_id:
            return jsonify({'message': 'Cannot disable your own admin account', 'error': 'invalid_action'}), 400

        target.is_active = not target.is_active
        db.session.commit()

        status_str = "ENABLED" if target.is_active else "DISABLED"
        log_activity(
            user_id=admin_user.id,
            username=admin_user.username,
            user_role=admin_user.role,
            action='USER_STATUS_CHANGED',
            details={'target_user_id': target.id, 'target_username': target.username, 'new_status': status_str}
        )

        return jsonify({'message': f'Account {target.username} has been {status_str.lower()}', 'user': target.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to toggle status', 'error': 'server_error'}), 500

@app.route('/api/admin/activity-logs', methods=['GET'])
@admin_required()
def admin_get_activity_logs():
    """Fetch audit activity logs with optional filtering."""
    try:
        user_id_param = request.args.get('user_id')
        action_param = request.args.get('action')
        
        query = ActivityLog.query
        if user_id_param and user_id_param != 'all':
            query = query.filter_by(user_id=int(user_id_param))
        if action_param and action_param != 'all':
            query = query.filter_by(action=action_param)

        logs = query.order_by(ActivityLog.created_at.desc()).limit(200).all()
        return jsonify([l.to_dict() for l in logs]), 200
    except Exception as e:
        log.error(f"Error fetching activity logs: {str(e)}")
        return jsonify({'message': 'Failed to fetch logs', 'error': 'server_error'}), 500

@app.route('/api/admin/login-history', methods=['GET'])
@admin_required()
def admin_get_login_history():
    """Fetch user login history."""
    try:
        history = LoginHistory.query.order_by(LoginHistory.login_at.desc()).limit(200).all()
        return jsonify([h.to_dict() for h in history]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch login history', 'error': 'server_error'}), 500

@app.route('/api/admin/records', methods=['GET'])
@admin_required()
def admin_get_records():
    """System-wide overview records for Admin."""
    try:
        total_users = User.query.count()
        total_papers = QuestionPaper.query.count()
        total_evaluations = Result.query.count()
        total_flagged = Result.query.filter_by(is_flagged=True).count()
        total_similarity_flags = SimilarityFlag.query.count()

        recent_papers = [p.to_dict() for p in QuestionPaper.query.order_by(QuestionPaper.created_at.desc()).limit(10).all()]
        recent_evaluations = [r.to_dict() for r in Result.query.order_by(Result.created_at.desc()).limit(10).all()]

        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_papers': total_papers,
                'total_evaluations': total_evaluations,
                'total_flagged': total_flagged,
                'total_similarity_flags': total_similarity_flags
            },
            'recent_papers': recent_papers,
            'recent_evaluations': recent_evaluations
        }), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch system records', 'error': 'server_error'}), 500


# ================= Template & Question Paper Endpoints =================

@app.route('/api/parse-template', methods=['POST'])
@jwt_required()
def parse_template_route():
    """
    Parse uploaded template file or custom pattern text and return detected question paper structure.
    """
    try:
        template_text = request.form.get('pattern_text', '').strip()
        
        if 'template_file' in request.files:
            file = request.files['template_file']
            if file and file.filename != '':
                # Read text from file
                if file.filename.lower().endswith('.pdf'):
                    import PyPDF2
                    reader = PyPDF2.PdfReader(file)
                    file_text = ""
                    for page in reader.pages:
                        file_text += page.extract_text() or ""
                    template_text = file_text
                else:
                    template_text = file.read().decode('utf-8', errors='ignore')

        if not template_text:
            return jsonify({'message': 'Template text or file is required', 'error': 'missing_template'}), 400

        result = parse_paper_template(template_text)
        if not result['is_valid']:
            return jsonify({'message': result['error'], 'error': 'invalid_template'}), 400

        return jsonify(result), 200
    except Exception as e:
        log.error(f"Template parse error: {str(e)}")
        return jsonify({'message': f'Failed to parse template: {str(e)}', 'error': 'parse_error'}), 400


@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload():
    """Upload and evaluate student answer sheets."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    batch_id = str(uuid.uuid4())
    
    try:
        log.info(f"Upload initiated by user {user_id}, batch_id: {batch_id}")
        
        paper_id = request.form.get('paperId')
        paper_questions = None
        key_path = None
        answerkey = None
        
        if paper_id and paper_id != 'null' and paper_id != 'undefined':
            try:
                paper_id = int(paper_id)
                paper = QuestionPaper.query.filter_by(id=paper_id).first()
                if not paper:
                    return jsonify({'message': f'Selected question paper (ID: {paper_id}) not found', 'error': 'paper_not_found'}), 404
                paper_questions = paper.paper_content.get('questions', [])
            except ValueError:
                return jsonify({'message': 'Invalid paper ID format', 'error': 'invalid_paper_id'}), 400
        else:
            if 'answerkey' not in request.files:
                return jsonify({
                    'message': 'Either select a Question Paper or upload an Answer Key file',
                    'error': 'missing_answerkey'
                }), 400
            answerkey = request.files['answerkey']
            if not answerkey or answerkey.filename == '':
                return jsonify({'message': 'Uploaded answer key is empty', 'error': 'empty_answerkey'}), 400
                
            is_valid, error = validate_file(answerkey)
            if not is_valid:
                return jsonify({'message': error, 'error': 'invalid_answerkey'}), 400

        if 'answers' not in request.files:
            return jsonify({'message': 'Student answers files are required', 'error': 'missing_answers'}), 400
            
        answers = request.files.getlist('answers')
        if not answers or len(answers) == 0 or answers[0].filename == '':
            return jsonify({'message': 'No student answer files uploaded', 'error': 'empty_answers'}), 400

        student_files = []
        for idx, answer_file in enumerate(answers):
            is_valid, error = validate_file(answer_file)
            if not is_valid:
                return jsonify({
                    'message': f'Student file {idx + 1}: {error}',
                    'error': 'invalid_student_file'
                }), 400

            student_name = request.form.get(f'studentNames[{idx}]', f'Student_{idx + 1}').strip()
            if not student_name:
                student_name = f'Student_{idx + 1}'

            student_files.append({
                'file': answer_file,
                'name': student_name
            })

        batch_folder = os.path.join(UPLOAD_FOLDER, batch_id)
        os.makedirs(batch_folder, exist_ok=True)

        if answerkey:
            key_filename = f"answerkey_{uuid.uuid4()}_{answerkey.filename}"
            key_path = os.path.join(batch_folder, key_filename)
            answerkey.save(key_path)

        answers_folder = os.path.join(batch_folder, 'answers')
        os.makedirs(answers_folder, exist_ok=True)

        saved_files = []
        for student_data in student_files:
            filename = f"{student_data['name'].replace(' ', '_')}_{uuid.uuid4()}_{student_data['file'].filename}"
            file_path = os.path.join(answers_folder, filename)
            student_data['file'].save(file_path)
            saved_files.append({
                'path': file_path,
                'name': student_data['name'],
                'original': student_data['file'].filename
            })

        log_activity(
            user_id=user_id,
            username=user.username,
            user_role=user.role,
            action='ANSWER_SHEET_UPLOADED',
            details={'batch_id': batch_id, 'file_count': len(saved_files)}
        )

        evaluation_results = evaluate_and_check_plagiarism(
            answerkey_path=key_path,
            answers_folder=answers_folder,
            paper_questions=paper_questions
        )

        flagged_count = 0
        for idx, result in enumerate(evaluation_results):
            student_name = saved_files[idx]['name'] if idx < len(saved_files) else f"Student_{idx + 1}"
            student_roll = request.form.get(f'studentRollNumbers[{idx}]', f"R-{1000 + idx + 1}").strip()

            new_result = Result(
                user_id=user_id,
                batch_id=batch_id,
                student_name=student_name,
                student_filename=result["filename"],
                roll_number=student_roll,
                marks=result["marks"],
                similarity_score=result["similarity"],
                confidence_score=result.get("confidence", 0.75),
                feedback=result["remark"],
                is_flagged=result["is_flagged"],
                extracted_text=result.get("extracted_text"),
                question_evaluations=result.get("question_evaluations"),
                grade=result.get("grade"),
                plagiarism_details=result.get("plagiarism_details"),
                flag_details=result.get("flag_details"),
                review_status="Pending Review" if result["is_flagged"] else "Approved"
            )
            db.session.add(new_result)

            if result["is_flagged"]:
                flagged_count += 1
                # Save SimilarityFlag records for faculty review
                plag_matches = result.get("plagiarism_details", {}).get("matches", [])
                for match in plag_matches:
                    sim_flag = SimilarityFlag(
                        user_id=user_id,
                        batch_id=batch_id,
                        student1_name=student_name,
                        student2_name=match.get('matched_to', 'Other Student'),
                        question_num='Overall',
                        similarity_percentage=match.get('similarity', 0.0),
                        matching_snippet=match.get('reason', 'High similarity detected'),
                        flag_reason=match.get('reason', 'Similarity threshold exceeded'),
                        review_status='Pending Review'
                    )
                    db.session.add(sim_flag)

        db.session.commit()

        log_activity(
            user_id=user_id,
            username=user.username,
            user_role=user.role,
            action='EVALUATION_COMPLETED',
            details={'batch_id': batch_id, 'evaluated_count': len(evaluation_results), 'flagged_count': flagged_count}
        )

        log_activity(
            user_id=user_id,
            username=user.username,
            user_role=user.role,
            action='SIMILARITY_CHECK_COMPLETED',
            details={'batch_id': batch_id, 'flagged_pairs': flagged_count}
        )

        if flagged_count > 0:
            log_activity(
                user_id=user_id,
                username=user.username,
                user_role=user.role,
                action='ANSWER_FLAGGED',
                details={'batch_id': batch_id, 'flagged_count': flagged_count}
            )

        if not KEEP_UPLOADED_FILES:
            try:
                if key_path and os.path.exists(key_path):
                    os.remove(key_path)
                for f in os.listdir(answers_folder):
                    os.remove(os.path.join(answers_folder, f))
                os.rmdir(answers_folder)
                os.rmdir(batch_folder)
            except Exception as e:
                log.warning(f"Failed to clean up files: {str(e)}")

        return jsonify({
            'message': 'Evaluation complete',
            'batch_id': batch_id,
            'results_count': len(evaluation_results),
            'results': evaluation_results
        }), 200

    except Exception as e:
        log.error(f"Upload/evaluation error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'message': f'Evaluation failed: {str(e)}',
            'error': 'evaluation_error'
        }), 500

@app.route('/api/results', methods=['GET'])
@jwt_required()
def get_results():
    """Get evaluation results."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        batch_id = request.args.get('batch_id')
        
        query = Result.query
        if user.role != 'admin':
            query = query.filter_by(user_id=user_id)

        if batch_id and batch_id != 'all':
            query = query.filter_by(batch_id=batch_id)
        
        results = query.order_by(Result.created_at.desc()).all()
        return jsonify([r.to_dict() for r in results]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch results', 'error': 'server_error'}), 500

@app.route('/api/results/<int:result_id>/override-marks', methods=['POST'])
@jwt_required()
def override_result_marks(result_id):
    """Allow faculty to edit marks per question or total mark and update grade."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400

        result = Result.query.get(result_id)
        if not result or (user.role != 'admin' and result.user_id != user_id):
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404

        new_question_evals = data.get('question_evaluations')
        new_total_marks = data.get('marks')
        comments = data.get('reviewer_comments', '')

        if new_question_evals is not None:
            result.question_evaluations = new_question_evals
            # Calculate new total marks from questions
            calc_marks = sum(float(q.get('marks_obtained', 0)) for q in new_question_evals)
            result.marks = round(calc_marks, 2)
        elif new_total_marks is not None:
            result.marks = round(float(new_total_marks), 2)

        result.grade = _calculate_grade(result.marks)
        result.review_status = 'Approved'
        if comments:
            result.reviewer_comments = comments

        db.session.commit()

        log_activity(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            action='EVALUATION_COMPLETED',
            details={'result_id': result.id, 'student_name': result.student_name, 'new_marks': result.marks}
        )

        return jsonify(result.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to override marks: {str(e)}', 'error': 'server_error'}), 500

@app.route('/api/similarity-flags', methods=['GET'])
@jwt_required()
def get_similarity_flags():
    """Fetch student-to-student similarity flags for review."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        status_filter = request.args.get('status')
        
        query = SimilarityFlag.query
        if user.role != 'admin':
            query = query.filter_by(user_id=user_id)

        if status_filter and status_filter != 'all':
            query = query.filter_by(review_status=status_filter)

        flags = query.order_by(SimilarityFlag.created_at.desc()).all()
        return jsonify([f.to_dict() for f in flags]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch similarity flags', 'error': 'server_error'}), 500

@app.route('/api/similarity-flags/<int:flag_id>/review', methods=['POST'])
@jwt_required()
def review_similarity_flag(flag_id):
    """Faculty review endpoint for similarity flags (Pending Review, Reviewed, Cleared, Confirmed)."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid data', 'error': 'invalid_data'}), 400

        flag = SimilarityFlag.query.get(flag_id)
        if not flag or (user.role != 'admin' and flag.user_id != user_id):
            return jsonify({'message': 'Flag not found', 'error': 'not_found'}), 404

        new_status = data.get('status', 'Reviewed')
        if new_status not in ['Pending Review', 'Reviewed', 'Cleared', 'Confirmed']:
            return jsonify({'message': 'Invalid status choice', 'error': 'invalid_status'}), 400

        flag.review_status = new_status
        flag.reviewer_comments = data.get('comments', '')
        db.session.commit()

        log_activity(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            action='FLAG_REVIEWED',
            details={'flag_id': flag.id, 'student1': flag.student1_name, 'student2': flag.student2_name, 'new_status': new_status}
        )

        return jsonify(flag.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to review flag', 'error': 'server_error'}), 500


@app.route('/api/results/<int:result_id>/review', methods=['POST'])
@jwt_required()
def review_result(result_id):
    """Update review status, comments, and optional score override for a result."""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400
            
        status = data.get('status')
        comments = data.get('comments', '')
        override_marks = data.get('marks')
        
        if status not in ['Pending Review', 'Approved', 'Rejected', 'Cleared', 'Confirmed']:
            return jsonify({'message': 'Invalid review status', 'error': 'invalid_status'}), 400
            
        result = Result.query.get(result_id)
        if not result or (user.role != 'admin' and result.user_id != user_id):
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404
            
        result.review_status = status
        result.reviewer_comments = comments
        
        if override_marks is not None:
            try:
                marks_val = float(override_marks)
                if 0 <= marks_val <= 100:
                    result.marks = marks_val
                    result.grade = _calculate_grade(marks_val)
            except ValueError:
                return jsonify({'message': 'Invalid marks value', 'error': 'invalid_marks'}), 400

        db.session.commit()

        log_activity(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            action='FLAG_REVIEWED',
            details={'result_id': result.id, 'status': status}
        )

        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to submit review', 'error': 'server_error'}), 500


@app.route('/api/results/<int:result_id>/compare', methods=['GET'])
@jwt_required()
def compare_submission(result_id):
    try:
        import re
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        result = Result.query.get(result_id)
        if not result or (user.role != 'admin' and result.user_id != user_id):
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404
            
        compare_type = request.args.get('type', 'student')
        student_text = result.extracted_text or ""
        target_text = ""
        target_name = ""
        
        if compare_type == 'student':
            target_id = request.args.get('target_id')
            target_filename = request.args.get('target_filename')
            
            target_result = None
            if target_id:
                target_result = Result.query.get(int(target_id))
            elif target_filename:
                target_result = Result.query.filter_by(student_filename=target_filename).first()
                if not target_result:
                    clean_name = target_filename.replace(" (Historical)", "").replace(" (Previous Batch)", "").strip()
                    target_result = Result.query.filter(
                        (Result.student_name == target_filename) | (Result.student_name == clean_name)
                    ).first()
                
            if not target_result:
                return jsonify({'message': 'Target student result not found', 'error': 'target_not_found'}), 404
                
            target_text = target_result.extracted_text or ""
            target_name = f"{target_result.student_name} (Roll: {target_result.roll_number or 'N/A'})"
            
        elif compare_type == 'model':
            model_answers = []
            if result.question_evaluations:
                for qe in result.question_evaluations:
                    model_answers.append(qe.get('model_answer', ''))
            target_text = "\n\n".join(model_answers)
            target_name = "Reference Model Answer Key"
            
        sentences_a = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', student_text) if s.strip()]
        sentences_b = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', target_text) if s.strip()]
        
        matches = []
        if sentences_a and sentences_b:
            from evaluator import simple_text_similarity
            for idx_a, s_a in enumerate(sentences_a):
                best_j = -1
                best_sim = 0.0
                for idx_b, s_b in enumerate(sentences_b):
                    sim = simple_text_similarity(s_a, s_b)
                    if sim > best_sim:
                        best_sim = sim
                        best_j = idx_b
                if best_sim >= 0.50:
                    matches.append({
                        "a_idx": idx_a,
                        "b_idx": best_j,
                        "similarity": round(best_sim * 100, 2)
                    })
                        
        return jsonify({
            'student_name': result.student_name,
            'target_name': target_name,
            'sentences_a': sentences_a,
            'sentences_b': sentences_b,
            'matches': matches
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Failed to compare submissions', 'error': 'server_error'}), 500

@app.route('/api/download_csv', methods=['GET'])
@jwt_required()
def download_csv():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        batch_id = request.args.get('batch_id')
        
        query = Result.query
        if user.role != 'admin':
            query = query.filter_by(user_id=user_id)
        if batch_id and batch_id != 'all':
            query = query.filter_by(batch_id=batch_id)
        
        results = query.order_by(Result.created_at.desc()).all()
        if not results:
            return jsonify({'message': 'No results to download', 'error': 'no_results'}), 404

        data = []
        for r in results:
            data.append({
                "Student Name": r.student_name,
                "File Name": r.student_filename,
                "Score": r.marks,
                "Grade": r.grade or "",
                "Similarity (%)": r.similarity_score,
                "Feedback": r.feedback,
                "Flagged for Plagiarism": "Yes" if r.is_flagged else "No",
                "Review Status": r.review_status,
                "Evaluated At": r.created_at.isoformat() if r.created_at else ""
            })

        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=evaluation_results.csv'}
        )
    except Exception as e:
        return jsonify({'message': 'Failed to download CSV', 'error': 'server_error'}), 500

@app.route('/api/download_pdf', methods=['GET'])
@jwt_required()
def download_pdf():
    try:
        from fpdf import FPDF
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        batch_id = request.args.get('batch_id')
        
        query = Result.query
        if user.role != 'admin':
            query = query.filter_by(user_id=user_id)
        if batch_id and batch_id != 'all':
            query = query.filter_by(batch_id=batch_id)
        
        results = query.order_by(Result.created_at.desc()).all()
        if not results:
            return jsonify({'message': 'No results to download', 'error': 'no_results'}), 404

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Evaluation Results Report", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(200, 10, txt=f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(5)

        for r in results:
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(200, 8, txt=f"Student: {r.student_name}", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(200, 6, txt=f"File: {r.student_filename}", ln=True)
            pdf.cell(200, 6, txt=f"Score: {r.marks}/100    Grade: {r.grade or 'N/A'}    Status: {r.review_status}", ln=True)
            pdf.cell(200, 6, txt=f"Similarity: {r.similarity_score}%", ln=True)
            pdf.multi_cell(0, 5, txt=f"Feedback: {r.feedback}")
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        output = BytesIO()
        pdf.output(output)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': 'attachment; filename=evaluation_results.pdf'}
        )
    except Exception as e:
        return jsonify({'message': 'Failed to download PDF', 'error': 'server_error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'message': f'File size exceeds maximum of {MAX_FILE_SIZE / (1024*1024):.0f}MB',
        'error': 'file_too_large'
    }), 413

@app.route('/api/question_papers/generate', methods=['POST'])
@jwt_required()
def generate_question_paper():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400
            
        subject_name = data.get('subject_name', '').strip()
        topics = data.get('topics', '').strip()
        syllabus = data.get('syllabus', '').strip()
        difficulty = data.get('difficulty', 'Medium').strip()
        duration = data.get('duration', '3 Hours').strip()
        total_marks = data.get('total_marks')
        distribution = data.get('distribution', {})
        
        if not subject_name or not topics or not total_marks:
            return jsonify({'message': 'Subject name, topics, and total marks are required', 'error': 'missing_fields'}), 400
            
        try:
            total_marks = int(total_marks)
            dist_sum = 0
            for mark_val, count in distribution.items():
                dist_sum += int(mark_val) * int(count)
            if dist_sum != total_marks:
                return jsonify({
                    'message': f'Total marks of distribution ({dist_sum}) does not match the target total marks ({total_marks})',
                    'error': 'distribution_mismatch'
                }), 400
        except ValueError:
            return jsonify({'message': 'Invalid total marks or distribution values', 'error': 'invalid_values'}), 400
            
        paper_content = generate_paper(subject_name, topics, syllabus, difficulty, duration, total_marks, distribution)
        
        new_paper = QuestionPaper(
            user_id=user_id,
            subject_name=subject_name,
            topics=topics,
            syllabus=syllabus,
            difficulty=difficulty,
            duration=duration,
            total_marks=total_marks,
            distribution=distribution,
            paper_content=paper_content
        )
        db.session.add(new_paper)
        db.session.commit()

        log_activity(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            action='QUESTION_PAPER_GENERATED',
            details={'paper_id': new_paper.id, 'subject_name': subject_name, 'total_marks': total_marks}
        )
        log_activity(
            user_id=user.id,
            username=user.username,
            user_role=user.role,
            action='ANSWER_KEY_GENERATED',
            details={'paper_id': new_paper.id, 'subject_name': subject_name}
        )
        
        return jsonify(new_paper.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to generate question paper: {str(e)}', 'error': 'server_error'}), 500

@app.route('/api/question_papers', methods=['GET'])
@jwt_required()
def get_question_papers():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        query = QuestionPaper.query
        if user.role != 'admin':
            query = query.filter_by(user_id=user_id)
        papers = query.order_by(QuestionPaper.created_at.desc()).all()
        return jsonify([p.to_dict() for p in papers]), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch question papers', 'error': 'server_error'}), 500

@app.route('/api/question_papers/<int:paper_id>', methods=['GET'])
@jwt_required()
def get_question_paper(paper_id):
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        paper = QuestionPaper.query.get(paper_id)
        if not paper or (user.role != 'admin' and paper.user_id != user_id):
            return jsonify({'message': 'Question paper not found', 'error': 'not_found'}), 404
        return jsonify(paper.to_dict()), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch question paper', 'error': 'server_error'}), 500

@app.route('/api/question_papers/<int:paper_id>', methods=['DELETE'])
@jwt_required()
def delete_question_paper(paper_id):
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        paper = QuestionPaper.query.get(paper_id)
        if not paper or (user.role != 'admin' and paper.user_id != user_id):
            return jsonify({'message': 'Question paper not found', 'error': 'not_found'}), 404
        db.session.delete(paper)
        db.session.commit()
        return jsonify({'message': 'Question paper deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete question paper', 'error': 'server_error'}), 500

@app.route('/api/question_papers/<int:paper_id>/download_pdf', methods=['GET'])
@jwt_required()
def download_question_paper_pdf(paper_id):
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        paper = QuestionPaper.query.get(paper_id)
        if not paper or (user.role != 'admin' and paper.user_id != user_id):
            return jsonify({'message': 'Question paper not found', 'error': 'not_found'}), 404
            
        include_answers = request.args.get('answers') == 'true'
        pdf_bytes = generate_paper_pdf(paper.to_dict(), include_answers=include_answers)
        prefix = "question_paper_answers" if include_answers else "question_paper"
        filename = f"{prefix}_{paper.subject_name.replace(' ', '_')}_{paper_id}.pdf"
        
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'message': 'Failed to generate question paper PDF', 'error': 'server_error'}), 500

def _get_results_for_report(user_id):
    batch_id = request.args.get('batch_id')
    user = User.query.get(user_id)
    query = Result.query
    if user.role != 'admin':
        query = query.filter_by(user_id=user_id)
    if batch_id and batch_id != 'all':
        query = query.filter_by(batch_id=batch_id)
    return query.order_by(Result.created_at.desc()).all(), batch_id

@app.route('/api/reports/batches', methods=['GET'])
@jwt_required()
def get_batches():
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        query = db.session.query(
            Result.batch_id,
            db.func.min(Result.created_at).label('created_at'),
            db.func.count(Result.id).label('student_count'),
            db.func.avg(Result.marks).label('avg_score'),
            db.func.sum(db.case((Result.is_flagged == True, 1), else_=0)).label('flagged_count')
        )
        if user.role != 'admin':
            query = query.filter(Result.user_id == user_id)
        batches_query = query.group_by(Result.batch_id).order_by(db.desc('created_at')).all()

        batches = []
        for b in batches_query:
            batches.append({
                'batch_id': b.batch_id,
                'created_at': b.created_at.isoformat() if b.created_at else None,
                'student_count': b.student_count,
                'avg_score': round(b.avg_score, 2) if b.avg_score is not None else 0.0,
                'flagged_count': int(b.flagged_count) if b.flagged_count is not None else 0
            })

        return jsonify(batches), 200
    except Exception as e:
        return jsonify({'message': 'Failed to fetch batches', 'error': 'server_error'}), 500

@app.route('/api/reports/student/<int:result_id>', methods=['GET'])
@jwt_required()
def get_student_report(result_id):
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        result = Result.query.get(result_id)
        if not result or (user.role != 'admin' and result.user_id != user_id):
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404
        
        format_type = request.args.get('format', 'pdf').lower()
        report_data = generate_student_report(result, format_type)
        
        if format_type == 'excel':
            return Response(
                report_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename=student_report_{result.roll_number or result_id}.xlsx'}
            )
        else:
            return Response(
                report_data,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename=student_report_{result.roll_number or result_id}.pdf'}
            )
    except Exception as e:
        return jsonify({'message': 'Failed to generate report', 'error': 'server_error'}), 500

@app.route('/api/reports/faculty', methods=['GET'])
@jwt_required()
def get_faculty_report_route():
    try:
        user_id = int(get_jwt_identity())
        results, batch_id = _get_results_for_report(user_id)
        if not results:
            return jsonify({'message': 'No results found', 'error': 'no_results'}), 404
            
        format_type = request.args.get('format', 'pdf').lower()
        report_data = generate_faculty_report(results, format_type, batch_id)
        filename = f"faculty_report_{batch_id[:8]}" if batch_id and batch_id != 'all' else "faculty_report_all"
        if format_type == 'excel':
            return Response(
                report_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
            )
        else:
            return Response(
                report_data,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename={filename}.pdf'}
            )
    except Exception as e:
        return jsonify({'message': 'Failed to generate report', 'error': 'server_error'}), 500

@app.route('/api/reports/class', methods=['GET'])
@jwt_required()
def get_class_report_route():
    try:
        user_id = int(get_jwt_identity())
        results, batch_id = _get_results_for_report(user_id)
        if not results:
            return jsonify({'message': 'No results found', 'error': 'no_results'}), 404
            
        format_type = request.args.get('format', 'pdf').lower()
        report_data = generate_class_report(results, format_type, batch_id)
        filename = f"class_report_{batch_id[:8]}" if batch_id and batch_id != 'all' else "class_report_all"
        if format_type == 'excel':
            return Response(
                report_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
            )
        else:
            return Response(
                report_data,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename={filename}.pdf'}
            )
    except Exception as e:
        return jsonify({'message': 'Failed to generate report', 'error': 'server_error'}), 500

@app.route('/api/reports/similarity', methods=['GET'])
@jwt_required()
def get_similarity_report_route():
    try:
        user_id = int(get_jwt_identity())
        results, batch_id = _get_results_for_report(user_id)
        if not results:
            return jsonify({'message': 'No results found', 'error': 'no_results'}), 404
            
        format_type = request.args.get('format', 'pdf').lower()
        report_data = generate_similarity_report(results, format_type, batch_id)
        filename = f"similarity_report_{batch_id[:8]}" if batch_id and batch_id != 'all' else "similarity_report_all"
        if format_type == 'excel':
            return Response(
                report_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
            )
        else:
            return Response(
                report_data,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename={filename}.pdf'}
            )
    except Exception as e:
        return jsonify({'message': 'Failed to generate report', 'error': 'server_error'}), 500

@app.route('/api/reports/flagged', methods=['GET'])
@jwt_required()
def get_flagged_report_route():
    try:
        user_id = int(get_jwt_identity())
        results, batch_id = _get_results_for_report(user_id)
        if not results:
            return jsonify({'message': 'No results found', 'error': 'no_results'}), 404
            
        format_type = request.args.get('format', 'pdf').lower()
        report_data = generate_flagged_report(results, format_type, batch_id)
        filename = f"flagged_report_{batch_id[:8]}" if batch_id and batch_id != 'all' else "flagged_report_all"
        if format_type == 'excel':
            return Response(
                report_data,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
            )
        else:
            return Response(
                report_data,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename={filename}.pdf'}
            )
    except Exception as e:
        return jsonify({'message': 'Failed to generate report', 'error': 'server_error'}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path.startswith('api/'):
        return jsonify({'message': 'Endpoint not found', 'error': 'not_found'}), 404
        
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
        
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Endpoint not found', 'error': 'not_found'}), 404

@app.errorhandler(500)
def internal_error(error):
    log.error(f"Internal server error: {str(error)}", exc_info=True)
    db.session.rollback()
    return jsonify({'message': 'Internal server error', 'error': 'server_error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    log.info("Starting Flask application")
    app.run(debug=False, host='0.0.0.0', port=5000)