from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import (
    User, StudentProfile, CompanyProfile, JobPosting, Application, 
    InterviewRound, InterviewFeedback, MockInterview,
    ROLE_STUDENT, ROLE_CDC, ROLE_COMPANY
)
from forms import (
    LoginForm, StudentRegistrationForm, CompanyRegistrationForm, 
    JobPostingForm, EditJobPostingForm, InterviewRoundForm, 
    InterviewFeedbackForm, MockInterviewForm, MockFeedbackForm,
    ApplicationStatusForm, StudentProfileForm, ChatbotForm
)
from utils import check_eligibility, format_branches
from chatbot import get_chatbot_response
from datetime import datetime
import logging

# Template context processor for utility functions
@app.context_processor
def utility_processor():
    def now():
        return datetime.utcnow()
    return dict(now=now)

# Home route
@app.route('/')
def index():
    return render_template('dashboard.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_STUDENT
        )
        user.set_password(form.password.data)
        
        student_profile = StudentProfile(
            full_name=form.full_name.data,
            roll_number=form.roll_number.data,
            branch=form.branch.data,
            cgpa=form.cgpa.data
        )
        
        user.student_profile = student_profile
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, user_type='student')

@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_COMPANY
        )
        user.set_password(form.password.data)
        
        company_profile = CompanyProfile(
            company_name=form.company_name.data,
            description=form.description.data,
            website=form.website.data,
            established_year=form.established_year.data
        )
        
        user.company_profile = company_profile
        
        db.session.add(user)
        db.session.commit()
        
        flash('Company registration successful! Please wait for CDC approval.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, user_type='company')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
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
        
        return render_template(
            'dashboard.html', 
            eligible_jobs_count=eligible_jobs_count,
            applied_jobs=applied_jobs,
            mock_interviews=mock_interviews
        )
    
    elif current_user.is_cdc():
        # For CDC dashboard
        companies_count = CompanyProfile.query.count()
        active_jobs_count = JobPosting.query.filter(
            JobPosting.application_deadline >= datetime.utcnow()
        ).count()
        applications_count = Application.query.count()
        students_count = StudentProfile.query.count()
        
        return render_template(
            'dashboard.html',
            companies_count=companies_count,
            active_jobs_count=active_jobs_count,
            applications_count=applications_count,
            students_count=students_count
        )
    
    elif current_user.is_company():
        # For company dashboard
        company_id = current_user.company_profile.id
        
        jobs = JobPosting.query.filter_by(company_id=company_id).all()
        jobs_count = len(jobs)
        
        applications_count = sum(len(job.applications) for job in jobs)
        
        active_jobs = [job for job in jobs if job.application_deadline >= datetime.utcnow()]
        active_jobs_count = len(active_jobs)
        
        return render_template(
            'dashboard.html',
            jobs_count=jobs_count,
            applications_count=applications_count,
            active_jobs_count=active_jobs_count
        )
    
    return render_template('dashboard.html')

# Student module routes
@app.route('/student/eligible-companies')
@login_required
def student_eligible_companies():
    if not current_user.is_student():
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    student = current_user.student_profile
    active_jobs = JobPosting.query.filter(
        JobPosting.application_deadline >= datetime.utcnow()
    ).all()
    
    eligible_jobs = []
    for job in active_jobs:
        if check_eligibility(student, job):
            # Check if already applied
            application = Application.query.filter_by(
                student_id=student.id,
                job_id=job.id
            ).first()
            
            eligible_jobs.append({
                'job': job,
                'applied': application is not None
            })
    
    return render_template('student/eligible_companies.html', eligible_jobs=eligible_jobs)

@app.route('/student/apply/<int:job_id>', methods=['POST'])
@login_required
def student_apply(job_id):
    if not current_user.is_student():
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    job = JobPosting.query.get_or_404(job_id)
    student = current_user.student_profile
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        student_id=student.id,
        job_id=job.id
    ).first()
    
    if existing_application:
        flash('You have already applied for this job.', 'info')
        return redirect(url_for('student_eligible_companies'))
    
    # Check eligibility
    if not check_eligibility(student, job):
        flash('You do not meet the eligibility criteria for this job.', 'danger')
        return redirect(url_for('student_eligible_companies'))
    
    # Create application
    application = Application(
        student_id=student.id,
        job_id=job.id
    )
    
    db.session.add(application)
    db.session.commit()
    
    flash(f'Successfully applied for {job.title} at {job.company.company_name}.', 'success')
    return redirect(url_for('student_applications'))

@app.route('/student/withdraw/<int:application_id>', methods=['POST'])
@login_required
def student_withdraw(application_id):
    if not current_user.is_student():
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(application_id)
    
    # Verify ownership
    if application.student_id != current_user.student_profile.id:
        flash('You do not have permission to withdraw this application.', 'danger')
        return redirect(url_for('student_applications'))
    
    # Check if can withdraw (only if applied status)
    if application.status != 'applied':
        flash('Cannot withdraw application that is already in process.', 'warning')
        return redirect(url_for('student_applications'))
    
    db.session.delete(application)
    db.session.commit()
    
    flash('Application withdrawn successfully.', 'success')
    return redirect(url_for('student_applications'))

@app.route('/student/applications')
@login_required
def student_applications():
    if not current_user.is_student():
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    student = current_user.student_profile
    applications = Application.query.filter_by(student_id=student.id).all()
    
    return render_template('student/applications.html', applications=applications)

@app.route('/student/feedback')
@login_required
def student_feedback():
    if not current_user.is_student():
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    student = current_user.student_profile
    
    # Get mock interview feedback
    mock_interviews = MockInterview.query.filter_by(student_id=student.id).all()
    
    # Get company interview feedback
    applications = Application.query.filter_by(student_id=student.id).all()
    interview_feedbacks = []
    
    for application in applications:
        for feedback in application.interview_feedbacks:
            interview_feedbacks.append({
                'company': application.job_posting.company.company_name,
                'position': application.job_posting.title,
                'round': feedback.interview_round.round_name,
                'feedback': feedback.feedback,
                'rating': feedback.rating,
                'interviewer': feedback.interviewer_name,
                'date': feedback.created_at
            })
    
    return render_template(
        'student/feedback.html',
        mock_interviews=mock_interviews,
        interview_feedbacks=interview_feedbacks
    )

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    if not current_user.is_student():
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    student = current_user.student_profile
    form = StudentProfileForm(obj=student)
    
    if form.validate_on_submit():
        student.full_name = form.full_name.data
        student.branch = form.branch.data
        student.cgpa = form.cgpa.data
        student.resume = form.resume.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))
    
    return render_template('student/profile.html', form=form, student=student)

# CDC Module Routes
@app.route('/cdc/companies')
@login_required
def cdc_companies():
    if not current_user.is_cdc():
        flash('Access denied. CDC privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    companies = CompanyProfile.query.all()
    return render_template('cdc/companies.html', companies=companies)

@app.route('/cdc/add-company', methods=['GET', 'POST'])
@login_required
def cdc_add_company():
    if not current_user.is_cdc():
        flash('Access denied. CDC privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = JobPostingForm()
    
    # Get the list of companies for selection
    companies = CompanyProfile.query.all()
    company_choices = [(company.id, company.company_name) for company in companies]
    form.company = SelectField('Company', choices=company_choices, coerce=int)
    
    if form.validate_on_submit():
        # Convert the list of selected branches to a comma-separated string
        branches = ','.join(form.eligible_branches.data)
        
        job = JobPosting(
            company_id=form.company.data,
            title=form.title.data,
            description=form.description.data,
            cgpa_criteria=form.cgpa_criteria.data,
            eligible_branches=branches,
            application_deadline=form.application_deadline.data,
            num_rounds=form.num_rounds.data,
            package_offered=form.package_offered.data
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job posting added successfully!', 'success')
        return redirect(url_for('cdc_companies'))
    
    return render_template('cdc/add_company.html', form=form)

@app.route('/cdc/edit-company/<int:job_id>', methods=['GET', 'POST'])
@login_required
def cdc_edit_company(job_id):
    if not current_user.is_cdc():
        flash('Access denied. CDC privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    job = JobPosting.query.get_or_404(job_id)
    form = EditJobPostingForm(obj=job)
    
    # Pre-populate branches
    if request.method == 'GET':
        form.eligible_branches.data = job.eligible_branches.split(',')
    
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
        return redirect(url_for('cdc_companies'))
    
    return render_template('cdc/edit_company.html', form=form, job=job)

@app.route('/cdc/student-applications')
@login_required
def cdc_student_applications():
    if not current_user.is_cdc():
        flash('Access denied. CDC privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    applications = Application.query.all()
    return render_template('cdc/student_applications.html', applications=applications)

@app.route('/cdc/schedule-mock', methods=['GET', 'POST'])
@login_required
def cdc_schedule_mock():
    if not current_user.is_cdc():
        flash('Access denied. CDC privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = MockInterviewForm()
    
    # Get students for selection
    students = StudentProfile.query.all()
    form.student.choices = [(student.id, f"{student.full_name} ({student.roll_number})") for student in students]
    
    if form.validate_on_submit():
        mock = MockInterview(
            student_id=form.student.data,
            scheduled_by=current_user.id,
            interviewer=form.interviewer.data,
            scheduled_date=form.scheduled_date.data,
            topic=form.topic.data
        )
        
        db.session.add(mock)
        db.session.commit()
        
        flash('Mock interview scheduled successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('cdc/schedule_mock.html', form=form)

@app.route('/cdc/provide-mock-feedback/<int:mock_id>', methods=['GET', 'POST'])
@login_required
def cdc_provide_mock_feedback(mock_id):
    if not current_user.is_cdc():
        flash('Access denied. CDC privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    mock = MockInterview.query.get_or_404(mock_id)
    form = MockFeedbackForm()
    
    if form.validate_on_submit():
        mock.feedback = form.feedback.data
        mock.status = 'completed'
        
        db.session.commit()
        flash('Mock interview feedback provided successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template(
        'cdc/provide_mock_feedback.html',
        form=form, 
        mock=mock,
        student=mock.student
    )

# Company module routes
@app.route('/company/students')
@login_required
def company_students():
    if not current_user.is_company():
        flash('Access denied. Company privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    company_id = current_user.company_profile.id
    jobs = JobPosting.query.filter_by(company_id=company_id).all()
    
    applications_by_job = {}
    for job in jobs:
        applications_by_job[job.id] = Application.query.filter_by(job_id=job.id).all()
    
    return render_template('company/students.html', jobs=jobs, applications_by_job=applications_by_job)

@app.route('/company/schedule-interview/<int:job_id>', methods=['GET', 'POST'])
@login_required
def company_schedule_interview(job_id):
    if not current_user.is_company():
        flash('Access denied. Company privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    job = JobPosting.query.get_or_404(job_id)
    
    # Check if job belongs to this company
    if job.company_id != current_user.company_profile.id:
        flash('You do not have permission to schedule interviews for this job.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = InterviewRoundForm()
    
    if form.validate_on_submit():
        # Find the next round number
        max_round = db.session.query(db.func.max(InterviewRound.round_number)).filter_by(job_id=job.id).scalar() or 0
        next_round = max_round + 1
        
        round = InterviewRound(
            job_id=job.id,
            round_number=next_round,
            round_name=form.round_name.data,
            round_description=form.round_description.data,
            round_date=form.round_date.data
        )
        
        db.session.add(round)
        db.session.commit()
        
        flash(f'Interview round {next_round} scheduled successfully!', 'success')
        return redirect(url_for('company_students'))
    
    return render_template('company/schedule_interview.html', form=form, job=job)

@app.route('/company/update-status/<int:application_id>', methods=['GET', 'POST'])
@login_required
def company_update_status(application_id):
    if not current_user.is_company():
        flash('Access denied. Company privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(application_id)
    job = application.job_posting
    
    # Check if job belongs to this company
    if job.company_id != current_user.company_profile.id:
        flash('You do not have permission to update status for this application.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ApplicationStatusForm(obj=application)
    
    if form.validate_on_submit():
        application.status = form.status.data
        application.updated_date = datetime.utcnow()
        
        db.session.commit()
        flash('Application status updated successfully!', 'success')
        return redirect(url_for('company_students'))
    
    return render_template(
        'company/update_status.html',
        form=form,
        application=application,
        student=application.student,
        job=job
    )

@app.route('/company/provide-feedback/<int:application_id>/<int:round_id>', methods=['GET', 'POST'])
@login_required
def company_provide_feedback(application_id, round_id):
    if not current_user.is_company():
        flash('Access denied. Company privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    application = Application.query.get_or_404(application_id)
    round = InterviewRound.query.get_or_404(round_id)
    
    # Check if job belongs to this company
    if application.job_posting.company_id != current_user.company_profile.id:
        flash('You do not have permission to provide feedback for this application.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if round belongs to this job
    if round.job_id != application.job_id:
        flash('This interview round does not belong to the job the student applied for.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = InterviewFeedbackForm()
    
    if form.validate_on_submit():
        # Check if feedback already exists
        existing_feedback = InterviewFeedback.query.filter_by(
            application_id=application_id,
            round_id=round_id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            existing_feedback.feedback = form.feedback.data
            existing_feedback.rating = form.rating.data
            existing_feedback.interviewer_name = form.interviewer_name.data
        else:
            # Create new feedback
            feedback = InterviewFeedback(
                application_id=application_id,
                round_id=round_id,
                feedback=form.feedback.data,
                rating=form.rating.data,
                interviewer_name=form.interviewer_name.data
            )
            db.session.add(feedback)
        
        db.session.commit()
        flash('Interview feedback provided successfully!', 'success')
        return redirect(url_for('company_students'))
    
    return render_template(
        'company/feedback.html',
        form=form,
        application=application,
        student=application.student,
        round=round
    )

# Chatbot routes
@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    form = ChatbotForm()
    
    if form.validate_on_submit():
        user_message = form.message.data
        bot_response = get_chatbot_response(user_message)
        
        # Store conversation in session if not already there
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        # Add current exchange to history
        session['chat_history'].append({
            'user': user_message,
            'bot': bot_response
        })
        session.modified = True
        
        return redirect(url_for('chatbot'))
    
    # Get chat history from session
    chat_history = session.get('chat_history', [])
    
    return render_template('chatbot.html', form=form, chat_history=chat_history)

@app.route('/chatbot/api', methods=['POST'])
@login_required
def chatbot_api():
    data = request.get_json()
    user_message = data.get('message', '')
    
    bot_response = get_chatbot_response(user_message)
    
    return jsonify({
        'response': bot_response
    })

@app.route('/chatbot/clear', methods=['POST'])
@login_required
def chatbot_clear():
    if 'chat_history' in session:
        session.pop('chat_history')
    
    return redirect(url_for('chatbot'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
