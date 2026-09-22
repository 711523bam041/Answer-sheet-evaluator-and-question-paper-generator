from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='faculty', nullable=False)  # 'admin' or 'faculty'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    results = db.relationship('Result', backref='user', lazy=True, cascade='all, delete-orphan')
    question_papers = db.relationship('QuestionPaper', backref='user', lazy=True, cascade='all, delete-orphan')
    login_history = db.relationship('LoginHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    username = db.Column(db.String(150), nullable=False)
    user_role = db.Column(db.String(50), nullable=False)
    login_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    logout_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'user_role': self.user_role,
            'login_at': self.login_at.isoformat() if self.login_at else None,
            'logout_at': self.logout_at.isoformat() if self.logout_at else None,
            'ip_address': self.ip_address
        }

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    username = db.Column(db.String(150), nullable=False)
    user_role = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False, index=True)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'user_role': self.user_role,
            'action': self.action,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SimilarityFlag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    batch_id = db.Column(db.String(36), nullable=False, index=True)
    student1_name = db.Column(db.String(255), nullable=False)
    student2_name = db.Column(db.String(255), nullable=False)
    question_num = db.Column(db.String(50), nullable=False)
    similarity_percentage = db.Column(db.Float, nullable=False)
    matching_snippet = db.Column(db.Text, nullable=True)
    flag_reason = db.Column(db.String(500), nullable=False)
    review_status = db.Column(db.String(50), default='Pending Review')  # Pending Review, Reviewed, Cleared, Confirmed
    reviewer_comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'batch_id': self.batch_id,
            'student1_name': self.student1_name,
            'student2_name': self.student2_name,
            'question_num': self.question_num,
            'similarity_percentage': self.similarity_percentage,
            'matching_snippet': self.matching_snippet,
            'flag_reason': self.flag_reason,
            'review_status': self.review_status,
            'reviewer_comments': self.reviewer_comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    batch_id = db.Column(db.String(36), nullable=False, index=True)  # UUID for grouping evaluations
    student_name = db.Column(db.String(255), nullable=False)
    student_filename = db.Column(db.String(255), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float, default=0.75)
    feedback = db.Column(db.String(500), nullable=False)
    is_flagged = db.Column(db.Boolean, default=False)
    extracted_text = db.Column(db.Text, nullable=True)
    question_evaluations = db.Column(db.JSON, nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    plagiarism_details = db.Column(db.JSON, nullable=True)
    roll_number = db.Column(db.String(50), nullable=True)
    review_status = db.Column(db.String(50), default='Pending Review')
    reviewer_comments = db.Column(db.Text, nullable=True)
    flag_details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_name': self.student_name,
            'filename': self.student_filename,
            'marks': self.marks,
            'similarity': self.similarity_score,
            'confidence': self.confidence_score,
            'feedback': self.feedback,
            'flagged': self.is_flagged,
            'extracted_text': self.extracted_text,
            'question_evaluations': self.question_evaluations,
            'grade': self.grade,
            'plagiarism_details': self.plagiarism_details,
            'roll_number': self.roll_number,
            'review_status': self.review_status,
            'reviewer_comments': self.reviewer_comments,
            'flag_details': self.flag_details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class QuestionPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    subject_name = db.Column(db.String(255), nullable=False)
    topics = db.Column(db.String(500), nullable=False)
    syllabus = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    distribution = db.Column(db.JSON, nullable=False)
    paper_content = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_name': self.subject_name,
            'topics': self.topics,
            'syllabus': self.syllabus,
            'difficulty': self.difficulty,
            'duration': self.duration,
            'total_marks': self.total_marks,
            'distribution': self.distribution,
            'paper_content': self.paper_content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }