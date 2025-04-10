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
