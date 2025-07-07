from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import fitz  # PyMuPDF
from docx import Document

from extensions import db
from models import (
    User, StudentProfile, CompanyProfile, CDCProfile, JobPosting, Application,
    MockInterview, ResumeAnalysis, SelectionPrediction, JDQuestions, InterviewRound, InterviewFeedback, InterviewSlot,
    ROLE_STUDENT, ROLE_CDC, ROLE_COMPANY, STATUS_APPLIED, STATUS_REJECTED,
    STATUS_SELECTED, STATUS_SHORTLISTED, STATUS_INTERVIEW_SCHEDULED
)
from forms import (
    RegistrationForm, LoginForm, StudentProfileForm, CompanyProfileForm, CDCProfileForm,
    JobPostingForm, EditJobPostingForm, ApplicationForm, MockInterviewForm, InterviewRoundForm, InterviewFeedbackForm,
    MockFeedbackForm, ApplicationStatusForm, ChatbotForm, InterviewSlotForm, CompanyCommentForm, CDCCompanyProfileForm
)
from utils import allowed_file, parse_resume, send_email
from chatbot import get_chatbot_response, clear_chatbot_session, handle_resume_analysis_request, analyze_resume_for_job, predict_selection_chances

bp = Blueprint('routes', __name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_resume_text(student):
    """Extracts text from a student's uploaded resume file (PDF)."""
    if not student or not student.resume_file:
        return None
    
    resume_path = os.path.join(UPLOAD_FOLDER, student.resume_file)
    
    if not os.path.exists(resume_path):
        return None
        
    try:
        with open(resume_path, 'rb') as f:
            doc = fitz.open(stream=f.read(), filetype="pdf")
            return " ".join([page.get_text() for page in doc])
    except Exception as e:
        print(f"Error reading resume PDF for student {student.id}: {e}")
        return None

def extract_text(file):
    if file.filename.endswith('.pdf'):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return " ".join([page.get_text() for page in doc])
    elif file.filename.endswith('.docx'):
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return file.read().decode("utf-8")

def calculate_similarity(text1, text2):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    return cosine_similarity(vectorizer[0:1], vectorizer[1:2])[0][0]

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_student():
            return redirect(url_for('routes.student_dashboard'))
        elif current_user.is_cdc():
            return redirect(url_for('routes.cdc_dashboard'))
        elif current_user.is_company():
            return redirect(url_for('routes.company_dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_student():
        return redirect(url_for('routes.student_dashboard'))
    elif current_user.is_cdc():
        return redirect(url_for('routes.cdc_dashboard'))
    elif current_user.is_company():
        return redirect(url_for('routes.company_dashboard'))
    return redirect(url_for('routes.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    user_type = request.args.get('type', 'student')  # Default to student
    form = RegistrationForm()
    
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            role=form.role.data
        )
        db.session.add(user)
        db.session.commit()
        
        # Create profile based on role
        if user.role == ROLE_STUDENT:
            profile = StudentProfile(user_id=user.id, full_name="", roll_number="", branch="", cgpa=0.0)
            db.session.add(profile)
        elif user.role == ROLE_COMPANY:
            profile = CompanyProfile(user_id=user.id, company_name="")
            db.session.add(profile)
        elif user.role == ROLE_CDC:
            profile = CDCProfile(user_id=user.id, full_name="", official_id="", designation="", contact_number="")
            db.session.add(profile)
            
        db.session.commit()
        
        # Log the user in automatically
        login_user(user)
        
        flash('Your account has been created! Please complete your profile.', 'success')
        
        # Redirect to appropriate profile page
        if user.role == ROLE_STUDENT:
            return redirect(url_for('routes.student_profile'))
        elif user.role == ROLE_COMPANY:
            return redirect(url_for('routes.company_profile'))
        elif user.role == ROLE_CDC:
            return redirect(url_for('routes.cdc_profile'))
    
    return render_template('register.html', form=form, user_type=user_type)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('routes.dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.index'))

@bp.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_student():
        # For student dashboard
        eligible_jobs_count = JobPosting.query.filter(
            JobPosting.application_deadline >= datetime.utcnow()
        ).count()
        
        applied_jobs = Application.query.filter_by(
            student_id=current_user.student_profile.id
        ).count()
        
        mock_interviews = MockInterview.query.filter_by(
            student_id=current_user.student_profile.id
        ).count()
        
        # Get recent applications with predictions
        recent_applications = Application.query.filter_by(
            student_id=current_user.student_profile.id
        ).order_by(Application.applied_date.desc()).limit(5).all()
        
        return render_template(
            'student/dashboard.html', 
            eligible_jobs_count=eligible_jobs_count,
            applied_jobs=applied_jobs,
            mock_interviews=mock_interviews,
            recent_applications=recent_applications
        )
    
    return render_template('student/dashboard.html', user=current_user)

@bp.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = StudentProfileForm()
    form.user_id = current_user.id
    if form.validate_on_submit():
        student = current_user.student_profile
        student.full_name = form.full_name.data
        student.roll_number = form.roll_number.data
        student.branch = form.branch.data
        student.cgpa = form.cgpa.data
        # Handle PDF resume upload
        resume_file = form.resume_file.data
        if resume_file and resume_file.filename:
            filename = secure_filename(f"resume_{student.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf")
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            resume_file.save(upload_path)
            student.resume_file = filename
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('routes.student_profile'))
    
    elif request.method == 'GET':
        student = current_user.student_profile
        form.full_name.data = student.full_name
        form.roll_number.data = student.roll_number
        form.branch.data = student.branch
        form.cgpa.data = student.cgpa
    
    return render_template('student/profile.html', form=form)

@bp.route('/student/eligible_companies')
@login_required
def eligible_companies():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    # Get eligible job postings
    student = current_user.student_profile
    eligible_jobs = JobPosting.query.filter(
        JobPosting.application_deadline >= datetime.utcnow(),
        JobPosting.cgpa_criteria <= student.cgpa,
        JobPosting.eligible_branches.contains(student.branch)
    ).all()
    
    # Check which jobs the student has already applied to
    applied_job_ids = [app.job_id for app in Application.query.filter_by(student_id=student.id).all()]
    
    return render_template('student/eligible_companies.html', 
                         eligible_jobs=eligible_jobs, 
                         applied_jobs=applied_job_ids)

@bp.route('/student/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_for_job(job_id):
    from utils import check_eligibility, allowed_file
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    job = JobPosting.query.get_or_404(job_id)
    student = current_user.student_profile
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        student_id=student.id, job_id=job_id
    ).first()
    
    if existing_application:
        flash('You have already applied for this position.', 'warning')
        return redirect(url_for('routes.eligible_companies'))
    
    # Check eligibility
    if not check_eligibility(student, job):
        flash('You are not eligible for this position.', 'danger')
        return redirect(url_for('routes.eligible_companies'))
    
    # Handle resume upload
    resume_file = request.files.get('resume')
    resume_text = ""
    resume_filename = None
    
    if resume_file and resume_file.filename:
        # Save file
        filename = f"resume_{student.id}_{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        resume_file.save(os.path.join(UPLOAD_FOLDER, filename))
        resume_filename = filename
        
        # Extract text for analysis
        resume_text = extract_text(resume_file)
        
        # Update student skills if not already set
        if not student.skills:
            skills_prompt = f"Extract technical skills from this resume: {resume_text[:1000]}"
            skills_response = model.generate_content(skills_prompt)
            student.skills = skills_response.text
            db.session.commit()
    
    # Create application
    application = Application(
        student_id=student.id,
        job_id=job_id,
        resume_file=resume_filename
    )
    db.session.add(application)
    db.session.commit()
    
    # Perform AI analysis if resume was uploaded
    if resume_text:
        analyze_resume_for_job(resume_text, job.description or "", student.id, job_id)
    
    # Generate selection prediction
    predict_selection_chances(application.id)
    
    flash('Your application has been submitted!', 'success')
    return redirect(url_for('routes.student_applications'))

@bp.route('/student/applications')
@login_required
def student_applications():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    applications = Application.query.filter_by(
        student_id=current_user.student_profile.id
    ).order_by(Application.applied_date.desc()).all()
    
    return render_template('student/applications.html', applications=applications)

@bp.route('/student/mock_interview', methods=['GET', 'POST'])
@login_required
def schedule_mock_interview():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = MockInterviewForm()
    
    # Populate student choices
    students = StudentProfile.query.all()
    form.student.choices = [(s.id, f"{s.full_name} ({s.roll_number})") for s in students]
    
    if form.validate_on_submit():
        # Validate interview scheduling constraints
        scheduled_date = form.scheduled_date.data
        
        # Check if date is in the past
        if scheduled_date < datetime.utcnow():
            flash('Cannot schedule interviews in the past.', 'danger')
            return render_template('student/mock_interview.html', 
                                 form=form, 
                                 mock_interviews=get_mock_interviews(),
                                 now=datetime.utcnow())
        
        # Check if it's Sunday (weekday 6)
        if scheduled_date.weekday() == 6:  # Sunday
            flash('Interviews cannot be scheduled on Sundays.', 'danger')
            return render_template('student/mock_interview.html', 
                                 form=form, 
                                 mock_interviews=get_mock_interviews(),
                                 now=datetime.utcnow())
        
        # Check if time is between 9 AM and 10 PM
        hour = scheduled_date.hour
        if hour < 9 or hour >= 22:  # Before 9 AM or after 10 PM
            flash('Interviews can only be scheduled between 9:00 AM and 10:00 PM.', 'danger')
            return render_template('student/mock_interview.html', 
                                 form=form, 
                                 mock_interviews=get_mock_interviews(),
                                 now=datetime.utcnow())
        
        # Check if date is within next month
        from datetime import timedelta
        one_month_from_now = datetime.utcnow() + timedelta(days=30)
        if scheduled_date > one_month_from_now:
            flash('Interviews can only be scheduled within the next month.', 'danger')
            return render_template('student/mock_interview.html', 
                                 form=form, 
                                 mock_interviews=get_mock_interviews(),
                                 now=datetime.utcnow())
        
        mock_interview = MockInterview(
            student_id=form.student.data,
            scheduled_by=current_user.id,
            interviewer=form.interviewer.data,
            scheduled_date=scheduled_date,
            topic=form.topic.data
        )
        
        db.session.add(mock_interview)
        db.session.commit()
        
        flash('Mock interview scheduled successfully!', 'success')
        return redirect(url_for('routes.student_dashboard'))
    
    return render_template('student/mock_interview.html', 
                         form=form, 
                         mock_interviews=get_mock_interviews(),
                         now=datetime.utcnow())

def get_mock_interviews():
    """Helper function to get mock interviews for current student"""
    return MockInterview.query.filter_by(
        student_id=current_user.student_profile.id
    ).order_by(MockInterview.scheduled_date.desc()).all()

@bp.route('/student/feedback')
@login_required
def student_feedback():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    # Get mock interview feedback
    mock_interviews = MockInterview.query.filter_by(
        student_id=current_user.student_profile.id
    ).order_by(MockInterview.scheduled_date.desc()).all()
    
    # Get real interview feedback
    applications = Application.query.filter_by(
        student_id=current_user.student_profile.id
    ).all()
    
    interview_feedbacks = []
    for app in applications:
        feedbacks = InterviewFeedback.query.filter_by(application_id=app.id).all()
        interview_feedbacks.extend(feedbacks)
    
    return render_template('student/feedback.html', 
                         mock_interviews=mock_interviews,
                         interview_feedbacks=interview_feedbacks)

@bp.route('/cdc/dashboard')
@login_required
def cdc_dashboard():
    if current_user.is_cdc():
        # For CDC dashboard
        companies_count = CompanyProfile.query.count()
        active_jobs_count = JobPosting.query.filter(
            JobPosting.application_deadline >= datetime.utcnow()
        ).count()
        applications_count = Application.query.count()
        students_count = StudentProfile.query.count()
        
        # Get recent companies and applications
        recent_companies = CompanyProfile.query.order_by(CompanyProfile.id.desc()).limit(5).all()
        recent_applications = Application.query.order_by(Application.applied_date.desc()).limit(5).all()
        
        return render_template(
            'cdc/dashboard.html',
            companies_count=companies_count,
            active_jobs_count=active_jobs_count,
            applications_count=applications_count,
            students_count=students_count,
            recent_companies=recent_companies,
            recent_applications=recent_applications
        )
    
    return render_template('cdc/dashboard.html')

@bp.route('/company/dashboard')
@login_required
def company_dashboard():
    if current_user.is_company():
        # For company dashboard
        company_id = current_user.company_profile.id
        
        jobs = JobPosting.query.filter_by(company_id=company_id).all()
        jobs_count = len(jobs)
        applications_count = Application.query.join(JobPosting).filter(
            JobPosting.company_id == company_id
        ).count()
        
        # Get eligible students for this company's jobs (CGPA > 6.0)
        eligible_students = StudentProfile.query.filter(StudentProfile.cgpa >= 6.0).all()
        students_count = len(eligible_students)
        
        # Get recent applications for this company
        recent_applications = Application.query.join(JobPosting).filter(
            JobPosting.company_id == company_id
        ).order_by(Application.applied_date.desc()).limit(5).all()
        
        # Get eligible students for each job
        job_eligible_students = {}
        for job in jobs:
            eligible_for_job = []
            for student in eligible_students:
                # Check if student meets job criteria
                if (student.cgpa >= job.cgpa_criteria and 
                    student.branch in job.eligible_branches.split(',')):
                    eligible_for_job.append(student)
            job_eligible_students[job.id] = eligible_for_job
        
        return render_template(
            'company/dashboard.html',
            jobs_count=jobs_count,
            applications_count=applications_count,
            students_count=students_count,
            recent_applications=recent_applications,
            jobs=jobs,
            eligible_students=eligible_students,
            job_eligible_students=job_eligible_students
        )
    
    return render_template('company/dashboard.html')

@bp.route('/student/eligible-companies')
@login_required
def student_eligible_companies():
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    # Get eligible job postings
    student = current_user.student_profile
    eligible_jobs = JobPosting.query.filter(
        JobPosting.application_deadline >= datetime.utcnow(),
        JobPosting.cgpa_criteria <= student.cgpa,
        JobPosting.eligible_branches.contains(student.branch)
    ).all()
    
    # Check which jobs the student has already applied to
    applied_job_ids = [app.job_id for app in Application.query.filter_by(student_id=student.id).all()]
    
    return render_template('student/eligible_companies.html', 
                         jobs=eligible_jobs, 
                         applied_job_ids=applied_job_ids)

@bp.route('/student/withdraw/<int:application_id>', methods=['POST'])
@login_required
def student_withdraw(application_id):
    if not current_user.is_student():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.student_applications'))
    
    application = Application.query.get_or_404(application_id)
    
    # Check if the application belongs to the current student
    if application.student_id != current_user.student_profile.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.student_applications'))
    
    db.session.delete(application)
    db.session.commit()
    
    flash('Application withdrawn successfully.', 'success')
    return redirect(url_for('routes.student_applications'))

@bp.route('/cdc/companies')
@login_required
def cdc_companies():
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    companies = CompanyProfile.query.all()
    return render_template('cdc/companies.html', companies=companies)

@bp.route('/cdc/add-company', methods=['GET', 'POST'])
@login_required
def cdc_add_company():
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = JobPostingForm()
    
    # Populate company choices
    companies = CompanyProfile.query.all()
    if not companies:
        flash('No companies available. Please add a company profile first.', 'warning')
        return redirect(url_for('routes.cdc_add_company_profile'))
    
    form.company.choices = [(c.id, c.company_name) for c in companies]
    
    if form.validate_on_submit():
        company = CompanyProfile.query.get(form.company.data)
        if not company:
            flash('Selected company not found.', 'danger')
            return redirect(url_for('routes.cdc_add_company'))
        
        job = JobPosting(
            company_id=company.id,
            title=form.title.data,
            description=form.description.data,
            cgpa_criteria=form.cgpa_criteria.data,
            eligible_branches=','.join(form.eligible_branches.data),
            application_deadline=form.application_deadline.data,
            num_rounds=form.num_rounds.data,
            package_offered=form.package_offered.data
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Generate JD-based questions
        generate_jd_questions(job.id, "technical", 5)
        generate_jd_questions(job.id, "behavioral", 3)
        
        flash('Job posting added successfully!', 'success')
        return redirect(url_for('routes.cdc_companies'))
    
    return render_template('cdc/add_company.html', form=form)

@bp.route('/cdc/edit-company/<int:job_id>', methods=['GET', 'POST'])
@login_required
def cdc_edit_company(job_id):
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    job = JobPosting.query.get_or_404(job_id)
    form = EditJobPostingForm()
    
    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.cgpa_criteria = form.cgpa_criteria.data
        job.eligible_branches = ','.join(form.eligible_branches.data)
        job.application_deadline = form.application_deadline.data
        job.num_rounds = form.num_rounds.data
        job.package_offered = form.package_offered.data
        
        db.session.commit()
        flash('Job posting updated successfully!', 'success')
        return redirect(url_for('routes.cdc_companies'))
    
    elif request.method == 'GET':
        form.title.data = job.title
        form.description.data = job.description
        form.cgpa_criteria.data = job.cgpa_criteria
        form.eligible_branches.data = job.eligible_branches.split(',')
        form.application_deadline.data = job.application_deadline
        form.num_rounds.data = job.num_rounds
        form.package_offered.data = job.package_offered
    
    return render_template('cdc/edit_company.html', form=form, job=job)

@bp.route('/cdc/student-applications')
@login_required
def cdc_student_applications():
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    applications = Application.query.order_by(Application.applied_date.desc()).all()
    return render_template('cdc/student_applications.html', applications=applications)

@bp.route('/cdc/schedule-mock', methods=['GET', 'POST'])
@login_required
def cdc_schedule_mock():
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = MockInterviewForm()
    
    # Populate student choices
    students = StudentProfile.query.all()
    form.student.choices = [(s.id, f"{s.full_name} ({s.roll_number})") for s in students]
    
    if form.validate_on_submit():
        mock_interview = MockInterview(
            student_id=form.student.data,
            scheduled_by=current_user.id,
            interviewer=form.interviewer.data,
            scheduled_date=form.scheduled_date.data,
            topic=form.topic.data
        )
        
        db.session.add(mock_interview)
        db.session.commit()
        
        flash('Mock interview scheduled successfully!', 'success')
        return redirect(url_for('routes.cdc_schedule_mock'))
    
    # Get existing mock interviews for display
    mock_interviews = MockInterview.query.all()
    
    return render_template('cdc/schedule_mock.html', form=form, mock_interviews=mock_interviews)

@bp.route('/cdc/provide-mock-feedback/<int:mock_id>', methods=['GET', 'POST'])
@login_required
def cdc_provide_mock_feedback(mock_id):
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    mock_interview = MockInterview.query.get_or_404(mock_id)
    form = MockFeedbackForm()
    
    if form.validate_on_submit():
        mock_interview.feedback = form.feedback.data
        mock_interview.status = 'completed'
        
        db.session.commit()
        flash('Feedback provided successfully!', 'success')
        return redirect(url_for('routes.cdc_schedule_mock'))
    
    return render_template('cdc/provide_mock_feedback.html', form=form, mock_interview=mock_interview)

@bp.route('/company/students')
@login_required
def company_students():
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    # Get students who applied to this company's jobs
    company_id = current_user.company_profile.id
    applications = Application.query.join(JobPosting).filter(
        JobPosting.company_id == company_id
    ).all()
    
    return render_template('company/students.html', applications=applications)

@bp.route('/company/schedule-interview/<int:job_id>', methods=['GET', 'POST'])
@login_required
def company_schedule_interview(job_id):
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    job = JobPosting.query.get_or_404(job_id)
    form = InterviewRoundForm()
    
    if form.validate_on_submit():
        # Find the next round number
        existing_rounds = InterviewRound.query.filter_by(job_id=job_id).all()
        next_round = len(existing_rounds) + 1
        
        interview_round = InterviewRound(
            job_id=job_id,
            round_number=next_round,
            round_name=form.round_name.data,
            round_description=form.round_description.data,
            round_date=form.round_date.data
        )
        
        db.session.add(interview_round)
        db.session.commit()
        
        flash('Interview round scheduled successfully!', 'success')
        return redirect(url_for('routes.company_students'))
    
    return render_template('company/schedule_interview.html', form=form, job=job)

@bp.route('/company/update-status/<int:application_id>', methods=['GET', 'POST'])
@login_required
def company_update_status(application_id):
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    application = Application.query.get_or_404(application_id)
    form = ApplicationStatusForm()
    
    if form.validate_on_submit():
        application.status = form.status.data
        application.updated_date = datetime.utcnow()
        
        db.session.commit()
        flash('Application status updated successfully!', 'success')
        return redirect(url_for('routes.company_students'))
    
    form.status.data = application.status
    return render_template('company/update_status.html', form=form, application=application)

@bp.route('/company/provide-feedback/<int:application_id>/<int:round_id>', methods=['GET', 'POST'])
@login_required
def company_provide_feedback(application_id, round_id):
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    application = Application.query.get_or_404(application_id)
    interview_round = InterviewRound.query.get_or_404(round_id)
    form = InterviewFeedbackForm()
    
    if form.validate_on_submit():
        feedback = InterviewFeedback(
            application_id=application_id,
            round_id=round_id,
            feedback=form.feedback.data,
            rating=form.rating.data,
            interviewer_name=form.interviewer_name.data
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Feedback provided successfully!', 'success')
        return redirect(url_for('routes.company_students'))
    
    return render_template('company/provide_feedback.html', 
                         form=form, application=application, interview_round=interview_round)

@bp.route("/chatbot", methods=["GET"])
@login_required
def chatbot():
    session_id = session.get("chatbot_session_id")
    return render_template("chatbot.html", session_id=session_id)

@bp.route('/chatbot/api', methods=['POST'])
@login_required
def chatbot_api():
    data = request.json
    user_input = data.get("message")
    session_id = session.get("chatbot_session_id")
    
    response, new_session_id = get_chatbot_response(user_input, current_user.student_profile.id, session_id)
    session["chatbot_session_id"] = new_session_id
    
    return jsonify({"response": response})

@bp.route('/chatbot/clear', methods=['POST'])
@login_required
def chatbot_clear():
    session_id = request.json.get('session_id')
    if session_id:
        clear_chatbot_session(session_id)
    return jsonify({'success': True})

@bp.route('/resume/review', methods=['GET', 'POST'])
@login_required
def resume_review():
    if not current_user.is_student():
        flash('Access denied. Only students can review resumes.', 'danger')
        return redirect(url_for('routes.dashboard'))

    student = current_user.student_profile
    if request.method == 'GET':
        if not student.resume_file:
            flash('Please upload your resume in your profile first.', 'warning')
            return redirect(url_for('routes.student_profile'))

        review_result = session.pop('review_result', None)
        review_type = request.args.get('type', 'comprehensive')
        resume_text = ""

        resume_path = os.path.join(UPLOAD_FOLDER, student.resume_file)
        try:
            with open(resume_path, 'rb') as f:
                doc = fitz.open(stream=f.read(), filetype="pdf")
                resume_text = " ".join([page.get_text() for page in doc])
        except Exception as e:
            flash(f'Error reading resume PDF: {e}', 'danger')

        return render_template('resume_review.html',
                             review_result=review_result,
                             student=student,
                             review_type=review_type,
                             resume_text=resume_text)

    if request.method == 'POST':
        review_type = request.form.get('type', 'comprehensive')
        
        from chatbot import model

        resume_text = get_resume_text(student)
        if not resume_text:
            flash('Could not read your resume file. Please upload a valid PDF.', 'danger')
            return redirect(url_for('routes.resume_review'))

        try:
            # Create a more detailed prompt based on review type
            if review_type == 'comprehensive':
                prompt = f"""Please provide a comprehensive analysis of this resume. Write in clear, simple language that a 5th grader can understand. Use clear section headers and avoid any HTML formatting.

Structure your response with these sections:

1. OVERALL ASSESSMENT
- What are the main strengths of this resume?
- What areas need improvement?

2. CONTENT ANALYSIS  
- What are the key achievements mentioned?
- What skills and experience are highlighted?

3. STRUCTURE AND FORMATTING
- How well is the resume organized?
- Is the layout clear and professional?

4. LANGUAGE AND GRAMMAR
- How clear and professional is the writing?
- Are there any grammar or spelling issues?

5. SKILLS ASSESSMENT
- What technical skills are mentioned?
- What soft skills are highlighted?

6. RECOMMENDATIONS
- What specific improvements would you suggest?
- What should be added or changed?

Resume Content:
{resume_text[:3000]}"""
            elif review_type == 'grammar':
                prompt = f"""Please analyze the grammar, language, and writing quality of this resume. Write in simple, clear language. Use clear section headers.

Structure your response with these sections:

1. GRAMMAR AND SPELLING
- Are there any spelling mistakes?
- Are there any grammar errors?

2. LANGUAGE QUALITY
- Is the writing clear and easy to understand?
- Is the tone professional?

3. WRITING STYLE
- How effective is the writing style?
- Is the language appropriate for a resume?

4. SPECIFIC CORRECTIONS
- List any specific errors you found
- Provide corrected versions

5. LANGUAGE TIPS
- What general writing improvements would you suggest?

Resume Content:
{resume_text[:3000]}"""
            elif review_type == 'skills':
                prompt = f"""Please analyze the skills presented in this resume. Write in simple, clear language. Use clear section headers.

Structure your response with these sections:

1. TECHNICAL SKILLS
- What programming languages are mentioned?
- What tools and technologies are listed?

2. SOFT SKILLS
- What communication skills are mentioned?
- What leadership or teamwork skills are shown?

3. SKILL RELEVANCE
- How well do the skills match typical job requirements?
- Are the skills relevant to the field?

4. SKILL PRESENTATION
- How effectively are the skills presented?
- Are they clearly organized?

5. MISSING SKILLS
- What important skills might be missing?
- What skills could be added?

6. SKILL RECOMMENDATIONS
- What skills should be developed further?
- What learning suggestions do you have?

Resume Content:
{resume_text[:3000]}"""
            elif review_type == 'formatting':
                prompt = f"""Please analyze the formatting and structure of this resume. Write in simple, clear language. Use clear section headers.

Structure your response with these sections:

1. LAYOUT ASSESSMENT
- How well is the resume structured?
- Is the overall layout professional?

2. SECTION ANALYSIS
- How effective is each section?
- Are all important sections included?

3. VISUAL PRESENTATION
- How readable is the resume?
- Does it look professional?

4. CONTENT ORGANIZATION
- How well is the information organized?
- Is there a logical flow?

5. FORMATTING ISSUES
- Are there any structural problems?
- What formatting issues do you see?

6. IMPROVEMENT SUGGESTIONS
- What specific formatting changes would you suggest?
- How could the structure be improved?

Resume Content:
{resume_text[:3000]}"""
            else:
                prompt = f"Please provide a general analysis of this resume in simple, clear language. Use clear section headers and avoid any HTML formatting. Resume Content: {resume_text[:2000]}"

            print(f"Generating AI analysis for review type: {review_type}")
            response = model.generate_content(prompt)
            review_result = response.text
            print(f"AI response received. Length: {len(review_result) if review_result else 0}")

            if not review_result:
                review_result = "Sorry, I couldn't generate an analysis at this time. Please try again."

            session['review_result'] = review_result

        except Exception as e:
            print(f"Error in resume analysis: {e}")
            flash(f"Error generating analysis: {str(e)}", 'danger')

        return redirect(url_for('routes.resume_review', type=review_type))

@bp.route('/company/profile', methods=['GET', 'POST'])
@login_required
def company_profile():
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = CompanyProfileForm()
    if form.validate_on_submit():
        company = current_user.company_profile
        company.company_name = form.company_name.data
        company.description = form.description.data
        company.website = form.website.data
        company.established_year = form.established_year.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('routes.company_profile'))
    
    elif request.method == 'GET':
        company = current_user.company_profile
        form.company_name.data = company.company_name
        form.description.data = company.description
        form.website.data = company.website
        form.established_year.data = company.established_year
    
    return render_template('company/profile.html', form=form)

@bp.route('/cdc/profile', methods=['GET', 'POST'])
@login_required
def cdc_profile():
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    form = CDCProfileForm()
    if form.validate_on_submit():
        cdc = current_user.cdc_profile
        cdc.full_name = form.full_name.data
        cdc.official_id = form.official_id.data
        cdc.designation = form.designation.data
        cdc.contact_number = form.contact_number.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('routes.cdc_profile'))
    
    elif request.method == 'GET':
        cdc = current_user.cdc_profile
        form.full_name.data = cdc.full_name
        form.official_id.data = cdc.official_id
        form.designation.data = cdc.designation
        form.contact_number.data = cdc.contact_number
    
    return render_template('cdc/profile.html', form=form)

@bp.route('/company/assign-slot/<int:application_id>/<int:round_id>', methods=['GET', 'POST'])
@login_required
def company_assign_slot(application_id, round_id):
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    application = Application.query.get_or_404(application_id)
    interview_round = InterviewRound.query.get_or_404(round_id)
    form = InterviewSlotForm()
    if form.validate_on_submit():
        slot = InterviewSlot(
            application_id=application_id,
            round_id=round_id,
            slot_datetime=form.slot_datetime.data
        )
        db.session.add(slot)
        db.session.commit()
        # Email notification
        send_email(
            subject='Interview Slot Assigned',
            recipients=[application.student.user.email],
            body=f'Your interview slot for {interview_round.round_name} ({application.job_posting.title}) is scheduled at {form.slot_datetime.data}.'
        )
        flash('Interview slot assigned and student notified!', 'success')
        return redirect(url_for('routes.company_students'))
    return render_template('company/assign_slot.html', form=form, application=application, interview_round=interview_round)

@bp.route('/company/comment/<int:application_id>', methods=['GET', 'POST'])
@login_required
def company_comment(application_id):
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    application = Application.query.get_or_404(application_id)
    form = CompanyCommentForm(obj=application)
    if form.validate_on_submit():
        application.company_comment = form.company_comment.data
        db.session.commit()
        # Email notification
        send_email(
            subject='Company Comment Added',
            recipients=[application.student.user.email],
            body=f'A new comment has been added to your application for {application.job_posting.title}:\n\n{form.company_comment.data}'
        )
        flash('Comment saved and student notified!', 'success')
        return redirect(url_for('routes.company_students'))
    return render_template('company/comment.html', form=form, application=application)

@bp.route('/cdc/add-company-profile', methods=['GET', 'POST'])
@login_required
def cdc_add_company_profile():
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    form = CDCCompanyProfileForm()
    if form.validate_on_submit():
        company = CompanyProfile(
            company_name=form.company_name.data,
            description=form.description.data,
            website=form.website.data,
            established_year=form.established_year.data
        )
        db.session.add(company)
        db.session.commit()
        flash('Company profile added!', 'success')
        return redirect(url_for('routes.cdc_companies'))
    return render_template('cdc/add_company_profile.html', form=form)

@bp.route('/cdc/edit-company-profile/<int:company_id>', methods=['GET', 'POST'])
@login_required
def cdc_edit_company_profile(company_id):
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    company = CompanyProfile.query.get_or_404(company_id)
    form = CDCCompanyProfileForm(obj=company)
    if form.validate_on_submit():
        company.company_name = form.company_name.data
        company.description = form.description.data
        company.website = form.website.data
        company.established_year = form.established_year.data
        db.session.commit()
        flash('Company profile updated!', 'success')
        return redirect(url_for('routes.cdc_companies'))
    return render_template('cdc/edit_company_profile.html', form=form, company=company)

@bp.route('/test-resume-review')
def test_resume_review():
    """Test route to verify resume review styling"""
    test_review_result = """
1. OVERALL ASSESSMENT
- This is a test resume analysis
- The content should be clearly visible
- Background should have good contrast

2. CONTENT ANALYSIS
- Test content for visibility
- Should be easy to read
- No HTML formatting issues

3. RECOMMENDATIONS
- Test recommendations
- Clear and simple language
- Easy to understand
"""
    return render_template('resume_review.html', 
                         review_result=test_review_result,
                         student=None,
                         review_type='test',
                         resume_text="This is test resume content to verify visibility.")

@bp.route('/test-ai')
def test_ai():
    try:
        from chatbot import model
        response = model.generate_content("Say 'Hello, AI is working!'")
        return jsonify({"status": "success", "response": response.text})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@bp.route('/cdc/students')
@login_required
def cdc_students():
    """CDC view of all students with search and filter functionality"""
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    # Get search parameters
    search = request.args.get('search', '')
    branch_filter = request.args.get('branch', '')
    cgpa_min = request.args.get('cgpa_min', '')
    cgpa_max = request.args.get('cgpa_max', '')
    
    # Build query
    query = StudentProfile.query
    
    if search:
        query = query.filter(
            db.or_(
                StudentProfile.full_name.ilike(f'%{search}%'),
                StudentProfile.roll_number.ilike(f'%{search}%'),
                StudentProfile.skills.ilike(f'%{search}%')
            )
        )
    
    if branch_filter:
        query = query.filter(StudentProfile.branch == branch_filter)
    
    if cgpa_min:
        try:
            query = query.filter(StudentProfile.cgpa >= float(cgpa_min))
        except ValueError:
            pass
    
    if cgpa_max:
        try:
            query = query.filter(StudentProfile.cgpa <= float(cgpa_max))
        except ValueError:
            pass
    
    students = query.order_by(StudentProfile.full_name).all()
    
    # Get branch options for filter
    branches = db.session.query(StudentProfile.branch).distinct().all()
    branch_options = [branch[0] for branch in branches if branch[0]]
    
    return render_template('cdc/students.html', 
                         students=students, 
                         search=search,
                         branch_filter=branch_filter,
                         cgpa_min=cgpa_min,
                         cgpa_max=cgpa_max,
                         branch_options=branch_options)

@bp.route('/cdc/student/<int:student_id>')
@login_required
def cdc_student_details(student_id):
    """CDC view of detailed student information"""
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    student = StudentProfile.query.get_or_404(student_id)
    
    # Get student's applications
    applications = Application.query.filter_by(student_id=student_id).order_by(Application.applied_date.desc()).all()
    
    # Get student's mock interviews
    mock_interviews = MockInterview.query.filter_by(student_id=student_id).order_by(MockInterview.scheduled_date.desc()).all()
    
    # Get resume analysis data
    resume_analyses = ResumeAnalysis.query.filter_by(student_id=student_id).all()
    
    # Get selection predictions
    selection_predictions = SelectionPrediction.query.join(Application).filter(Application.student_id == student_id).all()
    
    # Calculate statistics
    total_applications = len(applications)
    selected_count = len([app for app in applications if app.status == 'selected'])
    shortlisted_count = len([app for app in applications if app.status == 'shortlisted'])
    rejected_count = len([app for app in applications if app.status == 'rejected'])
    
    return render_template('cdc/student_details.html',
                         student=student,
                         applications=applications,
                         mock_interviews=mock_interviews,
                         resume_analyses=resume_analyses,
                         selection_predictions=selection_predictions,
                         total_applications=total_applications,
                         selected_count=selected_count,
                         shortlisted_count=shortlisted_count,
                         rejected_count=rejected_count)

@bp.route('/cdc/student-analytics')
@login_required
def cdc_student_analytics():
    """CDC view of student analytics and statistics"""
    if not current_user.is_cdc():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    # Get all students
    students = StudentProfile.query.all()
    
    # Calculate statistics
    total_students = len(students)
    branch_stats = {}
    cgpa_ranges = {
        '9.0-10.0': 0,
        '8.0-8.99': 0,
        '7.0-7.99': 0,
        '6.0-6.99': 0,
        'Below 6.0': 0
    }
    
    for student in students:
        # Branch statistics
        branch = student.branch
        if branch not in branch_stats:
            branch_stats[branch] = 0
        branch_stats[branch] += 1
        
        # CGPA range statistics
        cgpa = student.cgpa
        if cgpa >= 9.0:
            cgpa_ranges['9.0-10.0'] += 1
        elif cgpa >= 8.0:
            cgpa_ranges['8.0-8.99'] += 1
        elif cgpa >= 7.0:
            cgpa_ranges['7.0-7.99'] += 1
        elif cgpa >= 6.0:
            cgpa_ranges['6.0-6.99'] += 1
        else:
            cgpa_ranges['Below 6.0'] += 1
    
    # Application statistics
    applications = Application.query.all()
    application_stats = {
        'total': len(applications),
        'applied': len([app for app in applications if app.status == 'applied']),
        'shortlisted': len([app for app in applications if app.status == 'shortlisted']),
        'selected': len([app for app in applications if app.status == 'selected']),
        'rejected': len([app for app in applications if app.status == 'rejected'])
    }
    
    # Top performing students (by selection rate)
    student_performance = []
    for student in students:
        student_apps = [app for app in applications if app.student_id == student.id]
        if student_apps:
            selection_rate = len([app for app in student_apps if app.status == 'selected']) / len(student_apps) * 100
            student_performance.append({
                'student': student,
                'total_applications': len(student_apps),
                'selected_count': len([app for app in student_apps if app.status == 'selected']),
                'selection_rate': selection_rate
            })
    
    # Sort by selection rate (descending)
    student_performance.sort(key=lambda x: x['selection_rate'], reverse=True)
    top_performers = student_performance[:10]
    
    return render_template('cdc/student_analytics.html',
                         total_students=total_students,
                         branch_stats=branch_stats,
                         cgpa_ranges=cgpa_ranges,
                         application_stats=application_stats,
                         top_performers=top_performers)

@bp.route('/company/eligible-students')
@login_required
def company_eligible_students():
    """Company view of eligible students for their job postings"""
    if not current_user.is_company():
        flash('Access denied.', 'danger')
        return redirect(url_for('routes.dashboard'))
    
    company_id = current_user.company_profile.id
    
    # Get all jobs for this company
    jobs = JobPosting.query.filter_by(company_id=company_id).all()
    
    # Get search parameters
    job_filter = request.args.get('job_id', '')
    branch_filter = request.args.get('branch', '')
    cgpa_min = request.args.get('cgpa_min', '6.0')  # Default minimum CGPA
    cgpa_max = request.args.get('cgpa_max', '10.0')
    
    # Get eligible students (CGPA >= 6.0)
    query = StudentProfile.query.filter(StudentProfile.cgpa >= 6.0)
    
    if branch_filter:
        query = query.filter(StudentProfile.branch == branch_filter)
    
    if cgpa_min:
        try:
            query = query.filter(StudentProfile.cgpa >= float(cgpa_min))
        except ValueError:
            pass
    
    if cgpa_max:
        try:
            query = query.filter(StudentProfile.cgpa <= float(cgpa_max))
        except ValueError:
            pass
    
    eligible_students = query.order_by(StudentProfile.cgpa.desc()).all()
    
    # Filter by job if specified
    if job_filter:
        job = JobPosting.query.get(job_filter)
        if job and job.company_id == company_id:
            filtered_students = []
            for student in eligible_students:
                if (student.cgpa >= job.cgpa_criteria and 
                    student.branch in job.eligible_branches.split(',')):
                    filtered_students.append(student)
            eligible_students = filtered_students
    
    # Get branch options for filter
    branches = db.session.query(StudentProfile.branch).distinct().all()
    branch_options = [branch[0] for branch in branches if branch[0]]
    
    return render_template('company/eligible_students.html',
                         jobs=jobs,
                         eligible_students=eligible_students,
                         job_filter=job_filter,
                         branch_filter=branch_filter,
                         cgpa_min=cgpa_min,
                         cgpa_max=cgpa_max,
                         branch_options=branch_options)