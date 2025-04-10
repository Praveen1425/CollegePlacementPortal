from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, TextAreaField, IntegerField, DateTimeField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Regexp
from wtforms.widgets import TextArea
from models import User, StudentProfile
import re

# Custom validator for JNTU roll number
def validate_jntu_roll_number(form, field):
    # JNTU roll numbers typically follow a pattern like: 18H51A0501
    pattern = re.compile(r'^[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{4}$')
    if not pattern.match(field.data):
        raise ValidationError('Invalid JNTU roll number format. Expected format: 18H51A0501')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StudentRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired()])
    roll_number = StringField('JNTU Roll Number', validators=[DataRequired(), validate_jntu_roll_number])
    branch = SelectField('Branch', choices=[
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics and Communications', 'Electronics and Communications'),
        ('Electrical and Electronics', 'Electrical and Electronics'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Civil Engineering', 'Civil Engineering')
    ])
    cgpa = FloatField('CGPA', validators=[DataRequired(), NumberRange(min=0, max=10)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_roll_number(self, roll_number):
        profile = StudentProfile.query.filter_by(roll_number=roll_number.data).first()
        if profile:
            raise ValidationError('Roll number already registered.')

class CompanyRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    company_name = StringField('Company Name', validators=[DataRequired()])
    description = TextAreaField('Company Description')
    website = StringField('Website')
    established_year = IntegerField('Established Year')
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class JobPostingForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    cgpa_criteria = FloatField('CGPA Criteria', validators=[DataRequired(), NumberRange(min=0, max=10)])
    eligible_branches = SelectMultipleField('Eligible Branches', choices=[
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics and Communications', 'Electronics and Communications'),
        ('Electrical and Electronics', 'Electrical and Electronics'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Civil Engineering', 'Civil Engineering')
    ])
    application_deadline = DateTimeField('Application Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    num_rounds = IntegerField('Number of Interview Rounds', validators=[DataRequired(), NumberRange(min=1, max=10)])
    package_offered = StringField('Package Offered (LPA)', validators=[DataRequired()])
    submit = SubmitField('Post Job')

class EditJobPostingForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    cgpa_criteria = FloatField('CGPA Criteria', validators=[DataRequired(), NumberRange(min=0, max=10)])
    eligible_branches = SelectMultipleField('Eligible Branches', choices=[
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics and Communications', 'Electronics and Communications'),
        ('Electrical and Electronics', 'Electrical and Electronics'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Civil Engineering', 'Civil Engineering')
    ])
    application_deadline = DateTimeField('Application Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    num_rounds = IntegerField('Number of Interview Rounds', validators=[DataRequired(), NumberRange(min=1, max=10)])
    package_offered = StringField('Package Offered (LPA)', validators=[DataRequired()])
    submit = SubmitField('Update Job')

class InterviewRoundForm(FlaskForm):
    round_name = StringField('Round Name', validators=[DataRequired()])
    round_description = TextAreaField('Round Description')
    round_date = DateTimeField('Round Date and Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Schedule Round')

class InterviewFeedbackForm(FlaskForm):
    feedback = TextAreaField('Feedback', validators=[DataRequired()])
    rating = IntegerField('Rating (1-10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    interviewer_name = StringField('Interviewer Name', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class MockInterviewForm(FlaskForm):
    student = SelectField('Student', coerce=int, validators=[DataRequired()])
    interviewer = StringField('Interviewer Name', validators=[DataRequired()])
    scheduled_date = DateTimeField('Schedule Date and Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    topic = StringField('Interview Topic', validators=[DataRequired()])
    submit = SubmitField('Schedule Mock Interview')

class MockFeedbackForm(FlaskForm):
    feedback = TextAreaField('Feedback', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class ApplicationStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class StudentProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    branch = SelectField('Branch', choices=[
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics and Communications', 'Electronics and Communications'),
        ('Electrical and Electronics', 'Electrical and Electronics'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Civil Engineering', 'Civil Engineering')
    ])
    cgpa = FloatField('CGPA', validators=[DataRequired(), NumberRange(min=0, max=10)])
    resume = TextAreaField('Resume')
    submit = SubmitField('Update Profile')

class ChatbotForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')
