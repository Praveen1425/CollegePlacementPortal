import os
import re
from werkzeug.utils import secure_filename
from flask_mail import Message
from extensions import mail
from flask import current_app

def check_eligibility(student, job):
    """
    Check if a student is eligible for a job based on CGPA and branch.
    
    Args:
        student: The StudentProfile object
        job: The JobPosting object
    
    Returns:
        bool: True if eligible, False otherwise
    """
    # Check CGPA requirement
    if student.cgpa < job.cgpa_criteria:
        return False
    
    # Check branch eligibility
    eligible_branches = job.eligible_branches.split(',')
    if student.branch not in eligible_branches:
        return False
    
    return True

def format_branches(branches_str):
    """
    Format the comma-separated branches string into a readable format.
    
    Args:
        branches_str: The comma-separated string of branches
    
    Returns:
        str: The formatted string
    """
    if not branches_str:
        return "All branches"
    
    branches = branches_str.split(',')
    return ", ".join(branches)

def format_status(status):
    """
    Format the application status for display.
    
    Args:
        status: The status string
    
    Returns:
        tuple: (formatted_string, badge_class)
    """
    status_map = {
        'applied': ('Applied', 'badge-primary'),
        'shortlisted': ('Shortlisted', 'badge-info'),
        'interview_scheduled': ('Interview Scheduled', 'badge-warning'),
        'selected': ('Selected', 'badge-success'),
        'rejected': ('Rejected', 'badge-danger')
    }
    
    if status in status_map:
        return status_map[status]
    
    return (status.replace('_', ' ').title(), 'badge-secondary')

def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: The filename to check
        allowed_extensions: List of allowed file extensions (default: ['pdf', 'docx', 'doc'])
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = {'pdf', 'docx', 'doc'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def parse_resume(file):
    """
    Parse resume file and extract text content.
    
    Args:
        file: File object to parse
    
    Returns:
        str: Extracted text content from the resume
    """
    try:
        filename = secure_filename(file.filename)
        
        if filename.endswith('.pdf'):
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file.read(), filetype="pdf")
            text = " ".join([page.get_text() for page in doc])
            return text
            
        elif filename.endswith('.docx'):
            from docx import Document
            doc = Document(file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
            
        elif filename.endswith('.doc'):
            # For .doc files, we'll return a placeholder
            # In a real implementation, you might use python-docx2txt or similar
            return "Document content (DOC format - conversion not implemented)"
            
        else:
            # For text files
            return file.read().decode("utf-8")
            
    except Exception as e:
        return f"Error parsing resume: {str(e)}"

def send_email(subject, recipients, body):
    msg = Message(subject, recipients=recipients, body=body)
    with current_app.app_context():
        mail.send(msg)
