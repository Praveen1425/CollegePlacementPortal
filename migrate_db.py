#!/usr/bin/env python3
"""
Database Migration Script for College Placement Portal
Adds new AI integration tables and updates existing structure
"""

from app import app, db
from models import (
    User, StudentProfile, CompanyProfile, JobPosting, Application, 
    InterviewRound, InterviewFeedback, MockInterview, CDCProfile,
    ResumeAnalysis, ChatbotSession, SelectionPrediction, JDQuestions,
    ROLE_STUDENT, ROLE_CDC, ROLE_COMPANY
)
from datetime import datetime
import os

def migrate_database():
    """Migrate the database to include new AI integration tables"""
    
    with app.app_context():
        print("Starting database migration...")
        
        # Create all tables
        db.create_all()
        print("✓ All tables created successfully")
        
        # Check if CDCProfile table exists and has data
        try:
            cdc_count = CDCProfile.query.count()
            print(f"✓ CDCProfile table exists with {cdc_count} records")
        except Exception as e:
            print(f"⚠ CDCProfile table check: {e}")
        
        # Check if new AI tables exist
        try:
            resume_analysis_count = ResumeAnalysis.query.count()
            print(f"✓ ResumeAnalysis table exists with {resume_analysis_count} records")
        except Exception as e:
            print(f"⚠ ResumeAnalysis table check: {e}")
        
        try:
            chatbot_session_count = ChatbotSession.query.count()
            print(f"✓ ChatbotSession table exists with {chatbot_session_count} records")
        except Exception as e:
            print(f"⚠ ChatbotSession table check: {e}")
        
        try:
            selection_prediction_count = SelectionPrediction.query.count()
            print(f"✓ SelectionPrediction table exists with {selection_prediction_count} records")
        except Exception as e:
            print(f"⚠ SelectionPrediction table check: {e}")
        
        try:
            jd_questions_count = JDQuestions.query.count()
            print(f"✓ JDQuestions table exists with {jd_questions_count} records")
        except Exception as e:
            print(f"⚠ JDQuestions table check: {e}")
        
        # Create sample data for testing
        create_sample_data()
        
        print("\n🎉 Database migration completed successfully!")
        print("The following new features are now available:")
        print("- AI-powered resume analysis")
        print("- Selection prediction system")
        print("- Enhanced chatbot with session management")
        print("- JD-based question generation")
        print("- Mock interview support")

def create_sample_data():
    """Create sample data for testing the new features"""
    
    print("\nCreating sample data...")
    
    # Check if we already have sample data
    if JobPosting.query.count() > 0:
        print("✓ Sample data already exists, skipping...")
        return
    
    # Create a sample company
    company_user = User(
        username='sample_company',
        email='hr@abccorp.com',
        role=ROLE_COMPANY
    )
    company_user.set_password('password123')
    
    company_profile = CompanyProfile(
        company_name='ABC Corporation',
        description='A leading technology company specializing in software development',
        website='https://abccorp.com',
        established_year=2010
    )
    company_user.company_profile = company_profile
    
    db.session.add(company_user)
    db.session.commit()
    print("✓ Created sample company: ABC Corporation")
    
    # Create a sample job posting
    job_posting = JobPosting(
        company_id=company_profile.id,
        title='Software Engineer',
        description='We are looking for a talented software engineer with experience in Python, JavaScript, and web development. The ideal candidate should have strong problem-solving skills and be able to work in a team environment.',
        cgpa_criteria=7.0,
        eligible_branches='Computer Science,Information Technology',
        application_deadline=datetime(2025, 4, 15, 23, 59),
        num_rounds=3,
        package_offered='8-12 LPA'
    )
    
    db.session.add(job_posting)
    db.session.commit()
    print("✓ Created sample job posting: Software Engineer")
    
    # Create a sample student
    student_user = User(
        username='sample_student',
        email='student@university.edu',
        role=ROLE_STUDENT
    )
    student_user.set_password('password123')
    
    student_profile = StudentProfile(
        full_name='John Doe',
        roll_number='20CS1A0501',
        branch='Computer Science',
        cgpa=8.5,
        skills='Python, JavaScript, React, Node.js, SQL'
    )
    student_user.student_profile = student_profile
    
    db.session.add(student_user)
    db.session.commit()
    print("✓ Created sample student: John Doe")
    
    # Create a sample CDC user
    cdc_user = User(
        username='cdc_officer',
        email='cdc@university.edu',
        role=ROLE_CDC
    )
    cdc_user.set_password('password123')
    
    cdc_profile = CDCProfile(
        full_name='Dr. Jane Smith',
        official_id='CDC001',
        designation='Placement Officer',
        contact_number='9876543210'
    )
    cdc_user.cdc_profile = cdc_profile
    
    db.session.add(cdc_user)
    db.session.commit()
    print("✓ Created sample CDC officer: Dr. Jane Smith")
    
    # Create a sample application
    application = Application(
        student_id=student_profile.id,
        job_id=job_posting.id,
        status='applied',
        resume_file='sample_resume.pdf'
    )
    
    db.session.add(application)
    db.session.commit()
    print("✓ Created sample application")
    
    # Create sample JD questions
    sample_questions = [
        ('technical', 'Explain the difference between REST and GraphQL APIs'),
        ('technical', 'How would you optimize a slow database query?'),
        ('technical', 'Describe the MVC architecture pattern'),
        ('behavioral', 'Tell me about a time you had to work with a difficult team member'),
        ('behavioral', 'How do you handle tight deadlines and pressure?'),
        ('aptitude', 'If a train travels at 60 km/h and another at 40 km/h in opposite directions, how long until they meet if they start 200 km apart?')
    ]
    
    for question_type, question_text in sample_questions:
        jd_question = JDQuestions(
            job_id=job_posting.id,
            question_type=question_type,
            question_text=question_text,
            difficulty_level='medium'
        )
        db.session.add(jd_question)
    
    db.session.commit()
    print("✓ Created sample JD questions")
    
    # Create sample resume analysis
    resume_analysis = ResumeAnalysis(
        student_id=student_profile.id,
        job_id=job_posting.id,
        similarity_score=0.85,
        extracted_skills='Python, JavaScript, React, Node.js, SQL, Git, Docker',
        ai_feedback='Strong technical skills match the job requirements. Consider adding more details about project experience and leadership roles.'
    )
    
    db.session.add(resume_analysis)
    db.session.commit()
    print("✓ Created sample resume analysis")
    
    # Create sample selection prediction
    selection_prediction = SelectionPrediction(
        application_id=application.id,
        prediction_score=75.5,
        confidence_level=0.8,
        reasoning='Strong CGPA (8.5) exceeds requirement (7.0). Technical skills align well with job description. Branch matches eligibility criteria.'
    )
    
    db.session.add(selection_prediction)
    db.session.commit()
    print("✓ Created sample selection prediction")
    
    # Create sample chatbot session
    chatbot_session = ChatbotSession(
        student_id=student_profile.id,
        session_id='sample_session_123',
        conversation_history='[]',
        last_activity=datetime.utcnow()
    )
    
    db.session.add(chatbot_session)
    db.session.commit()
    print("✓ Created sample chatbot session")
    
    print("\n📊 Sample Data Summary:")
    print(f"- Companies: {CompanyProfile.query.count()}")
    print(f"- Job Postings: {JobPosting.query.count()}")
    print(f"- Students: {StudentProfile.query.count()}")
    print(f"- CDC Officers: {CDCProfile.query.count()}")
    print(f"- Applications: {Application.query.count()}")
    print(f"- JD Questions: {JDQuestions.query.count()}")
    print(f"- Resume Analyses: {ResumeAnalysis.query.count()}")
    print(f"- Selection Predictions: {SelectionPrediction.query.count()}")
    print(f"- Chatbot Sessions: {ChatbotSession.query.count()}")

if __name__ == '__main__':
    migrate_database() 