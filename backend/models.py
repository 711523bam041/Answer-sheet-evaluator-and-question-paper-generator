from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    results = db.relationship('Result', backref='user', lazy=True, cascade='all, delete-orphan')
    question_papers = db.relationship('QuestionPaper', backref='user', lazy=True, cascade='all, delete-orphan')

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    batch_id = db.Column(db.String(36), nullable=False, index=True)  # UUID for grouping evaluations
    student_name = db.Column(db.String(255), nullable=False)  # Student name
    student_filename = db.Column(db.String(255), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float, default=0.75)  # NEW: Confidence in evaluation (0-1)
    feedback = db.Column(db.String(500), nullable=False)
    is_flagged = db.Column(db.Boolean, default=False)
    extracted_text = db.Column(db.Text, nullable=True)  # Extracted handwritten/printed text
    question_evaluations = db.Column(db.JSON, nullable=True)  # Question-by-question scoring details
    grade = db.Column(db.String(10), nullable=True)  # Student grade (e.g. A+, A, B, etc.)
    plagiarism_details = db.Column(db.JSON, nullable=True)  # Structured plagiarism matches and details
    roll_number = db.Column(db.String(50), nullable=True)  # Student Roll Number
    review_status = db.Column(db.String(50), default='Pending Review')  # Pending Review, Approved, Rejected
    reviewer_comments = db.Column(db.Text, nullable=True)  # Optional comments from review
    flag_details = db.Column(db.JSON, nullable=True)  # Structured automatic flagging details
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
    difficulty = db.Column(db.String(50), nullable=False)  # Easy, Medium, Hard
    duration = db.Column(db.String(50), nullable=False)  # e.g., "3 Hours"
    total_marks = db.Column(db.Integer, nullable=False)
    distribution = db.Column(db.JSON, nullable=False)  # e.g., {"1": 10, "2": 5, "5": 3, "13": 2}
    paper_content = db.Column(db.JSON, nullable=False)  # Structured list of questions
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