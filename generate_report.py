from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os

def generate_project_report():
    """Generate a concise PDF report for the College Placement Portal project"""
    
    # Create PDF document
    doc = SimpleDocTemplate("College_Placement_Portal_Report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    story.append(Paragraph("College Placement Portal - Development Report", title_style))
    story.append(Spacer(1, 20))
    
    # Project Overview
    story.append(Paragraph("Project Overview", styles['Heading2']))
    story.append(Paragraph("""
    A comprehensive Flask-based web application for managing college placement activities. 
    Features AI-powered chatbot, resume analysis, interview scheduling, and multi-user role management.
    """, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Key Features
    story.append(Paragraph("Key Features Implemented", styles['Heading2']))
    features_data = [
        ['Feature', 'Description', 'Status'],
        ['Multi-User Authentication', 'Students, Companies, CDC Officers', '✅ Complete'],
        ['AI Chatbot (Google Gemini)', 'Resume analysis, coding help, interview prep', '✅ Complete'],
        ['Resume Upload & Analysis', 'PDF upload with AI-powered feedback', '✅ Complete'],
        ['Job Posting Management', 'Company job creation and management', '✅ Complete'],
        ['Application Tracking', 'Student applications and status updates', '✅ Complete'],
        ['Mock Interview Scheduling', 'CDC-organized mock interviews', '✅ Complete'],
        ['Interview Question Generation', 'AI-generated questions based on JD', '✅ Complete'],
        ['Selection Prediction', 'AI-powered placement chances prediction', '✅ Complete']
    ]
    
    feature_table = Table(features_data, colWidths=[1.5*inch, 3*inch, 1*inch])
    feature_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(feature_table)
    story.append(Spacer(1, 20))
    
    # Technical Stack
    story.append(Paragraph("Technical Stack", styles['Heading2']))
    tech_data = [
        ['Component', 'Technology'],
        ['Backend Framework', 'Flask (Python)'],
        ['Database', 'SQLite with SQLAlchemy ORM'],
        ['Frontend', 'HTML5, CSS3, Bootstrap 5, JavaScript'],
        ['AI Integration', 'Google Gemini API'],
        ['Authentication', 'Flask-Login'],
        ['File Handling', 'PyMuPDF for PDF processing'],
        ['Forms', 'Flask-WTF with WTForms'],
        ['Email', 'Flask-Mail']
    ]
    
    tech_table = Table(tech_data, colWidths=[2*inch, 3.5*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 20))
    
    # Setup Instructions
    story.append(Paragraph("Quick Setup Instructions", styles['Heading2']))
    setup_steps = [
        "1. Clone the repository",
        "2. Create virtual environment: python -m venv venv",
        "3. Activate virtual environment: venv\\Scripts\\activate (Windows)",
        "4. Install dependencies: pip install -r requirements.txt",
        "5. Set up environment variables (GEMINI_API_KEY)",
        "6. Initialize database: flask db init && flask db migrate && flask db upgrade",
        "7. Run the application: venv\\Scripts\\python.exe app.py",
        "8. Access at: http://localhost:5000"
    ]
    
    for step in setup_steps:
        story.append(Paragraph(step, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Key Issues Resolved
    story.append(Paragraph("Key Issues Resolved During Development", styles['Heading2']))
    issues_data = [
        ['Issue', 'Solution'],
        ['App Initialization Error', 'Fixed create_app() function usage'],
        ['Form Validation Errors', 'Added missing user_id field handling'],
        ['Database Import Errors', 'Cleared and recreated database'],
        ['File Upload Errors', 'Created static/uploads directory'],
        ['Template URL Errors', 'Fixed url_for() with routes prefix'],
        ['Chatbot Visibility Issues', 'Updated CSS and removed conflicting themes'],
        ['Resume Analysis Errors', 'Added PyMuPDF text extraction'],
        ['Mock Interview Validation', 'Added server-side and client-side validation']
    ]
    
    issues_table = Table(issues_data, colWidths=[2.5*inch, 3*inch])
    issues_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(issues_table)
    story.append(Spacer(1, 20))
    
    # User Roles & Permissions
    story.append(Paragraph("User Roles & Permissions", styles['Heading2']))
    roles_data = [
        ['Role', 'Permissions'],
        ['Student', 'Profile management, job applications, resume upload, chatbot access'],
        ['Company', 'Job posting, application review, interview scheduling, feedback'],
        ['CDC Officer', 'Company management, student applications, mock interview scheduling']
    ]
    
    roles_table = Table(roles_data, colWidths=[1.5*inch, 4*inch])
    roles_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(roles_table)
    story.append(Spacer(1, 20))
    
    # AI Features Summary
    story.append(Paragraph("AI-Powered Features", styles['Heading2']))
    ai_features = [
        "• Resume Analysis: Extracts text and provides improvement suggestions",
        "• Interview Questions: Generates technical and behavioral questions",
        "• Coding Help: Debugs code and explains programming concepts",
        "• Selection Prediction: Analyzes resume-job fit and predicts chances",
        "• General Assistance: Academic guidance and career advice"
    ]
    
    for feature in ai_features:
        story.append(Paragraph(feature, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Project Status
    story.append(Paragraph("Current Project Status", styles['Heading2']))
    story.append(Paragraph("""
    ✅ Core functionality complete and tested
    ✅ AI integration working with Google Gemini
    ✅ Multi-user authentication and role management
    ✅ Database operations and file handling
    ✅ Responsive UI with Bootstrap
    ✅ Real-time chatbot with conversation context
    ⚠️ Minor template URL fixes needed (in progress)
    """, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1)))
    
    # Build PDF
    doc.build(story)
    print("✅ Report generated successfully: College_Placement_Portal_Report.pdf")

if __name__ == "__main__":
    generate_project_report() 