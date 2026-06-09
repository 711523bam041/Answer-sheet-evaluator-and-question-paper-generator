from flask import Flask, request, jsonify, Response, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import uuid
import logging

load_dotenv()

from models import db, User, Result, QuestionPaper
from reports import (
    generate_student_report,
    generate_faculty_report,
    generate_class_report,
    generate_similarity_report,
    generate_flagged_report
)
from evaluator import evaluate_and_check_plagiarism
from paper_generator import generate_paper, generate_paper_pdf
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

# Set up logging
log = setup_logging(app)

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


# Create uploads directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.before_request
def initialize_database():
    """Initialize database on startup."""
    if not hasattr(app, 'db_initialized'):
        try:
            with app.app_context():
                db.create_all()
                app.db_initialized = True
                log.info("Database initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize database: {str(e)}", exc_info=True)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        # Test database connection
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
    """Register a new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'message': 'Username and password required', 'error': 'missing_fields'}), 400

        if len(username) < 3 or len(username) > 150:
            return jsonify({'message': 'Username must be between 3 and 150 characters', 'error': 'invalid_username'}), 400

        if len(password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters', 'error': 'weak_password'}), 400

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            log.warning(f"Registration attempt with existing username: {username}")
            return jsonify({'message': 'Username already exists', 'error': 'username_taken'}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        log.info(f"New user registered: {username}")
        return jsonify({'message': 'Registration successful', 'username': username}), 201
    
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
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'message': 'Username and password required', 'error': 'missing_fields'}), 400

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=str(user.id))
            log.info(f"User logged in: {username}")
            return jsonify({
                'access_token': access_token,
                'username': username,
                'user_id': user.id
            }), 200
        else:
            log.warning(f"Failed login attempt for username: {username}")
            return jsonify({'message': 'Invalid credentials', 'error': 'invalid_credentials'}), 401
    
    except Exception as e:
        log.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'message': 'Login failed', 'error': 'server_error'}), 500

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload():
    """Upload and evaluate student answer sheets."""
    user_id = int(get_jwt_identity())
    batch_id = str(uuid.uuid4())
    
    try:
        log.info(f"Upload initiated by user {user_id}, batch_id: {batch_id}")
        
        # Check if evaluating against a generated paper ID or an uploaded answer key
        paper_id = request.form.get('paperId')
        paper_questions = None
        key_path = None
        answerkey = None
        
        if paper_id and paper_id != 'null' and paper_id != 'undefined':
            # Select paper from DB
            try:
                paper_id = int(paper_id)
                paper = QuestionPaper.query.filter_by(id=paper_id, user_id=user_id).first()
                if not paper:
                    return jsonify({'message': f'Selected question paper (ID: {paper_id}) not found', 'error': 'paper_not_found'}), 404
                paper_questions = paper.paper_content.get('questions', [])
                log.info(f"Using database question paper (ID: {paper_id}) for grading")
            except ValueError:
                return jsonify({'message': 'Invalid paper ID format', 'error': 'invalid_paper_id'}), 400
        else:
            # Check for uploaded answer key
            if 'answerkey' not in request.files:
                log.warning(f"Upload missing answer key for user {user_id}")
                return jsonify({
                    'message': 'Either select a Question Paper or upload an Answer Key file',
                    'error': 'missing_answerkey'
                }), 400
            answerkey = request.files['answerkey']
            if not answerkey or answerkey.filename == '':
                return jsonify({'message': 'Uploaded answer key is empty', 'error': 'empty_answerkey'}), 400
                
            # Validate answer key file
            is_valid, error = validate_file(answerkey)
            if not is_valid:
                return jsonify({'message': error, 'error': 'invalid_answerkey'}), 400

        # Validate student answers
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

        log.info(f"Validation passed for {len(student_files)} student files")

        # Save files temporarily
        batch_folder = os.path.join(UPLOAD_FOLDER, batch_id)
        os.makedirs(batch_folder, exist_ok=True)

        if answerkey:
            key_filename = f"answerkey_{uuid.uuid4()}_{answerkey.filename}"
            key_path = os.path.join(batch_folder, key_filename)
            answerkey.save(key_path)
            log.info(f"Answer key saved: {key_filename}")

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

        log.info(f"All student files saved to {answers_folder}")

        # Run Evaluation
        log.info("Starting evaluation process")
        evaluation_results = evaluate_and_check_plagiarism(
            answerkey_path=key_path,
            answers_folder=answers_folder,
            paper_questions=paper_questions
        )

        # Save results to DB
        for idx, result in enumerate(evaluation_results):
            if idx < len(saved_files):
                student_name = saved_files[idx]['name']
            else:
                student_name = f"Student_{idx + 1}"
                
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

        db.session.commit()
        log.info(f"Saved {len(evaluation_results)} results to database for batch {batch_id}")

        # Clean up files
        if not KEEP_UPLOADED_FILES:
            try:
                if key_path and os.path.exists(key_path):
                    os.remove(key_path)
                for f in os.listdir(answers_folder):
                    os.remove(os.path.join(answers_folder, f))
                os.rmdir(answers_folder)
                os.rmdir(batch_folder)
                log.info(f"Cleaned up temporary files for batch {batch_id}")
            except Exception as e:
                log.warning(f"Failed to clean up files: {str(e)}")

        return jsonify({
            'message': 'Evaluation complete',
            'batch_id': batch_id,
            'results_count': len(evaluation_results),
            'results': evaluation_results
        }), 200

    except Exception as e:
        log.error(f"Upload/evaluation error for user {user_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'message': f'Evaluation failed: {str(e)}',
            'error': 'evaluation_error'
        }), 500

@app.route('/api/results', methods=['GET'])
@jwt_required()
def get_results():
    """Get evaluation results for the current user."""
    try:
        user_id = int(get_jwt_identity())
        
        # Get batch_id filter if provided
        batch_id = request.args.get('batch_id')
        
        query = Result.query.filter_by(user_id=user_id)
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        
        results = query.order_by(Result.created_at.desc()).all()
        
        data = [r.to_dict() for r in results]
        log.info(f"Retrieved {len(data)} results for user {user_id}")
        return jsonify(data), 200
    
    except Exception as e:
        log.error(f"Error fetching results: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to fetch results', 'error': 'server_error'}), 500

@app.route('/api/results/<int:result_id>/review', methods=['POST'])
@jwt_required()
def review_result(result_id):
    """Update review status, comments, and optional score override for a flagged result."""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request data', 'error': 'invalid_data'}), 400
            
        status = data.get('status')
        comments = data.get('comments', '')
        override_marks = data.get('marks')
        
        if status not in ['Pending Review', 'Approved', 'Rejected']:
            return jsonify({'message': 'Invalid review status', 'error': 'invalid_status'}), 400
            
        result = Result.query.filter_by(id=result_id, user_id=user_id).first()
        if not result:
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404
            
        result.review_status = status
        result.reviewer_comments = comments
        
        if override_marks is not None:
            try:
                marks_val = float(override_marks)
                if 0 <= marks_val <= 100:
                    result.marks = marks_val
                    # Recalculate grade
                    from evaluator import _calculate_grade
                    result.grade = _calculate_grade(marks_val)
                else:
                    return jsonify({'message': 'Marks must be between 0 and 100', 'error': 'invalid_marks'}), 400
            except ValueError:
                return jsonify({'message': 'Invalid marks value', 'error': 'invalid_marks'}), 400
        
        # Also sync flag_details JSON structure if present
        if result.flag_details:
            new_flag_details = result.flag_details.copy()
            new_flag_details["review_status"] = status
            new_flag_details["reviewer_comments"] = comments
            if override_marks is not None:
                new_flag_details["overridden_score"] = result.marks
                new_flag_details["overridden_grade"] = result.grade
            result.flag_details = new_flag_details
            
        db.session.commit()
        log.info(f"Result {result_id} reviewed by user {user_id}. Status: {status}, Marks: {result.marks}")
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        log.error(f"Error reviewing result {result_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'message': 'Failed to submit review', 'error': 'server_error'}), 500

@app.route('/api/results/<int:result_id>/compare', methods=['GET'])
@jwt_required()
def compare_submission(result_id):
    """
    Get sentence-level comparison data between current student and a target
    (another student, the model answer, or self-comparison for duplicate questions).
    """
    try:
        import re
        user_id = int(get_jwt_identity())
        result = Result.query.filter_by(id=result_id, user_id=user_id).first()
        if not result:
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404
            
        compare_type = request.args.get('type', 'student') # student, model, self
        
        student_text = ""
        target_text = ""
        target_name = ""
        
        if compare_type == 'student':
            target_id = request.args.get('target_id')
            target_filename = request.args.get('target_filename')
            
            target_result = None
            if target_id:
                target_result = Result.query.filter_by(id=int(target_id), user_id=user_id).first()
            elif target_filename:
                target_result = Result.query.filter_by(student_filename=target_filename, user_id=user_id).first()
                if not target_result:
                    clean_name = target_filename.replace(" (Historical)", "").replace(" (Previous Batch)", "").strip()
                    target_result = Result.query.filter(
                        (Result.student_name == target_filename) |
                        (Result.student_name == clean_name)
                    ).filter_by(user_id=user_id).first()
                
            if not target_result:
                return jsonify({'message': 'Target student result not found', 'error': 'target_not_found'}), 404
                
            student_text = result.extracted_text or ""
            target_text = target_result.extracted_text or ""
            target_name = f"{target_result.student_name} (Roll: {target_result.roll_number or 'N/A'})"
            
        elif compare_type == 'model':
            student_text = result.extracted_text or ""
            # Reconstruct model answer from question_evaluations
            model_answers = []
            if result.question_evaluations:
                for qe in result.question_evaluations:
                    model_answers.append(qe.get('model_answer', ''))
            target_text = "\n\n".join(model_answers)
            target_name = "Reference Model Answer Key"
            
        elif compare_type == 'self':
            q1 = request.args.get('q1')
            q2 = request.args.get('q2')
            if not q1 or not q2:
                if result.flag_details and result.flag_details.get('pattern_details'):
                    self_dups = result.flag_details['pattern_details'].get('self_duplicates', [])
                    if self_dups:
                        q1 = self_dups[0].get('q1')
                        q2 = self_dups[0].get('q2')
                if not q1 or not q2:
                    return jsonify({'message': 'Questions not specified for self-comparison', 'error': 'missing_questions'}), 400
                    
            q1 = int(q1)
            q2 = int(q2)
            
            ans_q1 = ""
            ans_q2 = ""
            if result.question_evaluations:
                for qe in result.question_evaluations:
                    if qe.get('question_num') == q1:
                        ans_q1 = qe.get('student_answer', '')
                    elif qe.get('question_num') == q2:
                        ans_q2 = qe.get('student_answer', '')
                        
            student_text = ans_q1
            target_text = ans_q2
            target_name = f"Question {q2} Answer (compared with Question {q1})"
            
        # Split texts into sentences
        sentences_a = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', student_text) if s.strip()]
        sentences_b = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', target_text) if s.strip()]
        
        matches = []
        
        if sentences_a and sentences_b:
            from evaluator import get_model, simple_text_similarity
            model = get_model()
            
            if model is not None:
                try:
                    from sentence_transformers import util
                    # Map valid sentences (with > 2 words) to avoid short-phrase noise
                    valid_a = [(idx, s) for idx, s in enumerate(sentences_a) if len(s.split()) > 2]
                    valid_b = [(idx, s) for idx, s in enumerate(sentences_b) if len(s.split()) > 2]
                    
                    if valid_a and valid_b:
                        emb_a = model.encode([item[1] for item in valid_a], convert_to_tensor=True)
                        emb_b = model.encode([item[1] for item in valid_b], convert_to_tensor=True)
                        
                        if len(valid_a) == 1:
                            emb_a = emb_a.unsqueeze(0)
                        if len(valid_b) == 1:
                            emb_b = emb_b.unsqueeze(0)
                            
                        cos_sims = util.cos_sim(emb_a, emb_b)
                        
                        for i, (idx_a, s_a) in enumerate(valid_a):
                            best_j = -1
                            best_sim = 0.0
                            for j, (idx_b, s_b) in enumerate(valid_b):
                                sim = cos_sims[i][j].item()
                                if sim > best_sim:
                                    best_sim = sim
                                    best_j = idx_b
                            
                            if best_sim >= 0.70:
                                matches.append({
                                    "a_idx": idx_a,
                                    "b_idx": best_j,
                                    "similarity": round(best_sim * 100, 2)
                                })
                except Exception as e:
                    log.warning(f"Sentence SBERT comparison failed: {e}")
                    # Fallback to Jaccard
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
            else:
                # Fallback to Jaccard
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
        log.error(f"Error comparing submission: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to compare submissions', 'error': 'server_error'}), 500

@app.route('/api/download_csv', methods=['GET'])
@jwt_required()
def download_csv():
    """Download evaluation results as CSV."""
    try:
        user_id = int(get_jwt_identity())
        batch_id = request.args.get('batch_id')
        
        query = Result.query.filter_by(user_id=user_id)
        if batch_id:
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
                "Evaluated At": r.created_at.isoformat() if r.created_at else ""
            })

        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        log.info(f"Downloaded CSV with {len(results)} results for user {user_id}")
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=evaluation_results.csv'}
        )

    except Exception as e:
        log.error(f"CSV download error: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to download CSV', 'error': 'server_error'}), 500

@app.route('/api/download_pdf', methods=['GET'])
@jwt_required()
def download_pdf():
    """Download evaluation results as PDF."""
    try:
        from fpdf import FPDF
        user_id = int(get_jwt_identity())
        batch_id = request.args.get('batch_id')
        
        query = Result.query.filter_by(user_id=user_id)
        if batch_id:
            query = query.filter_by(batch_id=batch_id)
        
        results = query.order_by(Result.created_at.desc()).all()
        
        if not results:
            return jsonify({'message': 'No results to download', 'error': 'no_results'}), 404

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        # Header
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
            pdf.cell(200, 6, txt=f"Score: {r.marks}/100    Grade: {r.grade or 'N/A'}", ln=True)
            pdf.cell(200, 6, txt=f"Similarity: {r.similarity_score}%", ln=True)
            pdf.multi_cell(0, 5, txt=f"Feedback: {r.feedback}")

            if r.is_flagged:
                pdf.set_text_color(255, 0, 0)
                pdf.cell(200, 6, txt="⚠ WARNING: Plagiarism Detected!", ln=True)
                pdf.set_text_color(0, 0, 0)

            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        output = BytesIO()
        pdf.output(output)
        output.seek(0)

        log.info(f"Downloaded PDF with {len(results)} results for user {user_id}")
        return Response(
            output.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': 'attachment; filename=evaluation_results.pdf'}
        )

    except Exception as e:
        log.error(f"PDF download error: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to download PDF', 'error': 'server_error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    log.warning("File size exceeded maximum limit")
    return jsonify({
        'message': f'File size exceeds maximum of {MAX_FILE_SIZE / (1024*1024):.0f}MB',
        'error': 'file_too_large'
    }), 413


@app.route('/api/question_papers/generate', methods=['POST'])
@jwt_required()
def generate_question_paper():
    user_id = int(get_jwt_identity())
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
            
        # Generate question paper content
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
        
        log.info(f"Question paper generated successfully for user {user_id}: {subject_name}")
        return jsonify(new_paper.to_dict()), 201
        
    except Exception as e:
        log.error(f"Error generating question paper: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'message': f'Failed to generate question paper: {str(e)}', 'error': 'server_error'}), 500

@app.route('/api/question_papers', methods=['GET'])
@jwt_required()
def get_question_papers():
    try:
        user_id = int(get_jwt_identity())
        papers = QuestionPaper.query.filter_by(user_id=user_id).order_by(QuestionPaper.created_at.desc()).all()
        return jsonify([p.to_dict() for p in papers]), 200
    except Exception as e:
        log.error(f"Error fetching question papers: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to fetch question papers', 'error': 'server_error'}), 500

@app.route('/api/question_papers/<int:paper_id>', methods=['GET'])
@jwt_required()
def get_question_paper(paper_id):
    try:
        user_id = int(get_jwt_identity())
        paper = QuestionPaper.query.filter_by(id=paper_id, user_id=user_id).first()
        if not paper:
            return jsonify({'message': 'Question paper not found', 'error': 'not_found'}), 404
        return jsonify(paper.to_dict()), 200
    except Exception as e:
        log.error(f"Error fetching question paper {paper_id}: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to fetch question paper', 'error': 'server_error'}), 500

@app.route('/api/question_papers/<int:paper_id>', methods=['DELETE'])
@jwt_required()
def delete_question_paper(paper_id):
    try:
        user_id = int(get_jwt_identity())
        paper = QuestionPaper.query.filter_by(id=paper_id, user_id=user_id).first()
        if not paper:
            return jsonify({'message': 'Question paper not found', 'error': 'not_found'}), 404
        db.session.delete(paper)
        db.session.commit()
        log.info(f"Deleted question paper {paper_id} for user {user_id}")
        return jsonify({'message': 'Question paper deleted successfully'}), 200
    except Exception as e:
        log.error(f"Error deleting question paper {paper_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'message': 'Failed to delete question paper', 'error': 'server_error'}), 500

@app.route('/api/question_papers/<int:paper_id>/download_pdf', methods=['GET'])
@jwt_required()
def download_question_paper_pdf(paper_id):
    try:
        user_id = int(get_jwt_identity())
        paper = QuestionPaper.query.filter_by(id=paper_id, user_id=user_id).first()
        if not paper:
            return jsonify({'message': 'Question paper not found', 'error': 'not_found'}), 404
            
        include_answers = request.args.get('answers') == 'true'
        pdf_bytes = generate_paper_pdf(paper.to_dict(), include_answers=include_answers)
        
        prefix = "question_paper_answers" if include_answers else "question_paper"
        filename = f"{prefix}_{paper.subject_name.replace(' ', '_')}_{paper_id}.pdf"
        
        log.info(f"Downloaded PDF (answers={include_answers}) for question paper {paper_id} for user {user_id}")
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        log.error(f"Error generating question paper PDF: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to generate question paper PDF', 'error': 'server_error'}), 500


def _get_results_for_report(user_id):
    batch_id = request.args.get('batch_id')
    query = Result.query.filter_by(user_id=user_id)
    if batch_id and batch_id != 'all':
        query = query.filter_by(batch_id=batch_id)
    return query.order_by(Result.created_at.desc()).all(), batch_id


@app.route('/api/reports/batches', methods=['GET'])
@jwt_required()
def get_batches():
    try:
        user_id = int(get_jwt_identity())
        batches_query = db.session.query(
            Result.batch_id,
            db.func.min(Result.created_at).label('created_at'),
            db.func.count(Result.id).label('student_count'),
            db.func.avg(Result.marks).label('avg_score'),
            db.func.sum(db.case((Result.is_flagged == True, 1), else_=0)).label('flagged_count')
        ).filter(Result.user_id == user_id).group_by(Result.batch_id).order_by(db.desc('created_at')).all()

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
        log.error(f"Error fetching batches: {str(e)}", exc_info=True)
        return jsonify({'message': 'Failed to fetch batches', 'error': 'server_error'}), 500


@app.route('/api/reports/student/<int:result_id>', methods=['GET'])
@jwt_required()
def get_student_report(result_id):
    try:
        user_id = int(get_jwt_identity())
        result = Result.query.filter_by(id=result_id, user_id=user_id).first()
        if not result:
            return jsonify({'message': 'Result not found', 'error': 'not_found'}), 404
        
        format_type = request.args.get('format', 'pdf').lower()
        if format_type not in ['pdf', 'excel']:
            return jsonify({'message': 'Invalid format. Supported: pdf, excel', 'error': 'invalid_format'}), 400
            
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
        log.error(f"Error generating student report: {str(e)}", exc_info=True)
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
        if format_type not in ['pdf', 'excel']:
            return jsonify({'message': 'Invalid format. Supported: pdf, excel', 'error': 'invalid_format'}), 400
            
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
        log.error(f"Error generating faculty report: {str(e)}", exc_info=True)
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
        if format_type not in ['pdf', 'excel']:
            return jsonify({'message': 'Invalid format. Supported: pdf, excel', 'error': 'invalid_format'}), 400
            
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
        log.error(f"Error generating class report: {str(e)}", exc_info=True)
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
        if format_type not in ['pdf', 'excel']:
            return jsonify({'message': 'Invalid format. Supported: pdf, excel', 'error': 'invalid_format'}), 400
            
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
        log.error(f"Error generating similarity report: {str(e)}", exc_info=True)
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
        if format_type not in ['pdf', 'excel']:
            return jsonify({'message': 'Invalid format. Supported: pdf, excel', 'error': 'invalid_format'}), 400
            
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
        log.error(f"Error generating flagged report: {str(e)}", exc_info=True)
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
    """Handle 404 errors."""
    return jsonify({'message': 'Endpoint not found', 'error': 'not_found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    log.error(f"Internal server error: {str(error)}", exc_info=True)
    db.session.rollback()
    return jsonify({'message': 'Internal server error', 'error': 'server_error'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    log.info("Starting Flask application")
    app.run(debug=False, host='0.0.0.0', port=5000)