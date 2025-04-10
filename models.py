from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# User roles
ROLE_STUDENT = 'student'
ROLE_CDC = 'cdc'
ROLE_COMPANY = 'company'

# Application status
STATUS_APPLIED = 'applied'
STATUS_SHORTLISTED = 'shortlisted'
STATUS_INTERVIEW_SCHEDULED = 'interview_scheduled'
STATUS_SELECTED = 'selected'
STATUS_REJECTED = 'rejected'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_student(self):
        return self.role == ROLE_STUDENT
    
    def is_cdc(self):
        return self.role == ROLE_CDC
    
    def is_company(self):
        return self.role == ROLE_COMPANY
    
    def __repr__(self):
        return f'<User {self.username}>'

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    resume = db.Column(db.Text, nullable=True)
    
    # Relationships
    applications = db.relationship('Application', backref='student', cascade='all, delete-orphan')
    mock_interviews = db.relationship('MockInterview', backref='student', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudentProfile {self.full_name}>'

class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(200), nullable=True)
    established_year = db.Column(db.Integer, nullable=True)
    
    # Relationships
    job_postings = db.relationship('JobPosting', backref='company', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CompanyProfile {self.company_name}>'

class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cgpa_criteria = db.Column(db.Float, nullable=False)
    eligible_branches = db.Column(db.String(200), nullable=False)
    application_deadline = db.Column(db.DateTime, nullable=False)
    num_rounds = db.Column(db.Integer, nullable=False)
    package_offered = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='job_posting', cascade='all, delete-orphan')
    interview_rounds = db.relationship('InterviewRound', backref='job_posting', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<JobPosting {self.title} by {self.company.company_name}>'

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    status = db.Column(db.String(30), default=STATUS_APPLIED, nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interview_feedbacks = db.relationship('InterviewFeedback', backref='application', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Application {self.student.user.username} for {self.job_posting.title}>'

class InterviewRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    round_name = db.Column(db.String(100), nullable=False)
    round_description = db.Column(db.Text, nullable=True)
    round_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    feedbacks = db.relationship('InterviewFeedback', backref='interview_round', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InterviewRound {self.round_name} for {self.job_posting.title}>'

class InterviewFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('interview_round.id'), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    interviewer_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InterviewFeedback for {self.application.student.user.username}>'

class MockInterview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    scheduled_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    interviewer = db.Column(db.String(100), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='scheduled', nullable=False)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with the CDC user who scheduled it
    cdc_user = db.relationship('User', foreign_keys=[scheduled_by])
    
    def __repr__(self):
        return f'<MockInterview for {self.student.user.username} on {self.topic}>'
