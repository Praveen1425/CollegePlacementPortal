from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, TextAreaField, IntegerField, DateTimeField, SelectMultipleField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Regexp
from wtforms.widgets import TextArea
from wtforms.fields import DateTimeLocalField
import re

# Custom validator for JNTU roll number
def validate_jntu_roll_number(form, field):
    # JNTU roll numbers typically follow a pattern like: 18H51A0501
    pattern = re.compile(r'^[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{4}$')
    if not pattern.match(field.data):
        raise ValidationError('Invalid JNTU roll number format. Expected format: 18H51A0501')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('company', 'Company'), ('cdc', 'CDC')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        from models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StudentProfileForm(FlaskForm):
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
    resume_file = FileField('Upload Resume (PDF only)')
    submit = SubmitField('Update Profile')

    def validate_roll_number(self, roll_number):
        from models import StudentProfile
        profile = StudentProfile.query.filter_by(roll_number=roll_number.data).first()
        if profile and profile.user_id != self.user_id:
             raise ValidationError('Roll number already registered.')

class CompanyProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    description = TextAreaField('Company Description')
    website = StringField('Website')
    established_year = IntegerField('Established Year')
    submit = SubmitField('Update Profile')

class CDCProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    official_id = StringField('Official ID', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])
    contact_number = StringField('Contact Number', validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class JobPostingForm(FlaskForm):
    company = SelectField('Company', coerce=int, validators=[DataRequired()])
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
    ], validators=[DataRequired()])
    application_deadline = DateTimeField('Application Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    num_rounds = IntegerField('Number of Interview Rounds', validators=[DataRequired(), NumberRange(min=1)])
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
    ], validators=[DataRequired()])
    application_deadline = DateTimeField('Application Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    num_rounds = IntegerField('Number of Interview Rounds', validators=[DataRequired(), NumberRange(min=1)])
    package_offered = StringField('Package Offered (LPA)', validators=[DataRequired()])
    submit = SubmitField('Update Job')

class ApplicationForm(FlaskForm):
    resume = TextAreaField('Why are you a good fit for this role? (Optional)')
    submit = SubmitField('Submit Application')
    
class MockInterviewForm(FlaskForm):
    student = SelectField('Student', coerce=int)
    interviewer = StringField('Interviewer', validators=[DataRequired()])
    scheduled_date = DateTimeField('Scheduled Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    topic = StringField('Topic', validators=[DataRequired()])
    submit = SubmitField('Schedule Interview')

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

class ChatbotForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class InterviewSlotForm(FlaskForm):
    slot_datetime = DateTimeLocalField('Interview Slot Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Assign Slot')

class CompanyCommentForm(FlaskForm):
    company_comment = TextAreaField('Company Comment/Review', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Save Comment')

class CDCCompanyProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    website = StringField('Website', validators=[Length(max=200)])
    established_year = IntegerField('Established Year', validators=[NumberRange(min=1800, max=2100)])
    submit = SubmitField('Save Company')
