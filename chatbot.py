import google.generativeai as genai
import os
import re
import json
import uuid
from datetime import datetime
from models import ChatbotSession, ResumeAnalysis, SelectionPrediction, JDQuestions, Application, StudentProfile, JobPosting
from extensions import db
from config import Config

# Configure Gemini - You can replace this with your API key
GOOGLE_API_KEY = Config.GOOGLE_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)

# Model setup with enhanced system instruction
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "You are a comprehensive AI assistant for college students and young professionals. "
        "Your expertise includes:\n\n"
        "1. **Coding & Programming Help:** Debug code errors, explain programming concepts, help with algorithms, data structures, and software development\n"
        "2. **Engineering Support:** Help with math problems, physics, electronics, mechanical design, and engineering concepts\n"
        "3. **Resume & Career Guidance:** Analyze resumes, suggest improvements, career advice, interview preparation\n"
        "4. **Academic Support:** Help with homework, projects, research, and academic writing\n"
        "5. **General Problem Solving:** Logic, reasoning, and analytical thinking\n\n"
        "IMPORTANT GUIDELINES:\n"
        "- **Write for all ages:** Use simple, clear language that a 5th grader can understand\n"
        "- **Always format responses** using simple HTML for readability\n"
        "- **Maintain conversation context:** Remember previous questions and build on them\n"
        "- **Provide step-by-step explanations** for complex topics\n"
        "- **Use examples and analogies** to make concepts clear\n"
        "- **Be encouraging and supportive** in your responses\n\n"
        "HTML FORMATTING RULES:\n"
        "- Use <b> for important terms and headings\n"
        "- Use <ul> and <li> for lists and steps\n"
        "- Use <i> for emphasis and examples\n"
        "- Use <p> to separate paragraphs\n"
        "- Use <code> for code snippets\n"
        "- Use <br> for line breaks\n\n"
        "EXAMPLE FORMAT:\n"
        "<p><b>Here's how to fix your code:</b></p>\n"
        "<ul>\n"
        "<li><b>Step 1:</b> Check your variable names</li>\n"
        "<li><b>Step 2:</b> Look for syntax errors</li>\n"
        "</ul>\n"
        "<p><i>Remember:</i> Always test your code step by step!</p>"
    )
)

def get_chatbot_response(user_input, student_id=None, session_id=None):
    try:
        # Get or create session
        session = get_or_create_session(student_id, session_id)
        
        # Update conversation history
        update_conversation_history(session, "user", user_input)
        
        # Get conversation context for better continuity
        conversation_context = get_conversation_context(session)
        
        # Check for specific commands and types of questions
        if user_input.lower().startswith("review resume") or "resume" in user_input.lower() and ("analyze" in user_input.lower() or "review" in user_input.lower()):
            response_text = handle_resume_review_request(user_input, student_id, conversation_context)
        elif user_input.lower().startswith("analyze resume"):
            response_text = handle_resume_analysis_request(user_input, student_id, conversation_context)
        elif "interview" in user_input.lower() and "question" in user_input.lower():
            response_text = handle_interview_questions_request(user_input, student_id, conversation_context)
        elif "selection" in user_input.lower() and "chance" in user_input.lower():
            response_text = handle_selection_prediction_request(user_input, student_id, conversation_context)
        elif any(keyword in user_input.lower() for keyword in ["error", "bug", "code", "programming", "debug", "syntax", "algorithm", "function", "variable", "loop", "array", "string", "python", "java", "javascript", "c++", "html", "css", "sql"]):
            response_text = handle_coding_request(user_input, student_id, conversation_context)
        elif any(keyword in user_input.lower() for keyword in ["math", "physics", "engineering", "circuit", "mechanical", "electrical", "design", "calculation", "formula", "equation"]):
            response_text = handle_engineering_request(user_input, student_id, conversation_context)
        else:
            # Generate contextual response for general questions
            context = get_context_for_student(student_id)
            enhanced_prompt = f"{context}\n\n{conversation_context}\n\nStudent Question: {user_input}"
        
        response = model.generate_content(enhanced_prompt)
        response_text = response.text
        
        # Update conversation history
        update_conversation_history(session, "assistant", response_text)
        
        return response_text, session.session_id

    except Exception as e:
        error_msg = f"<p><i>Oops! Something went wrong: {str(e)}</i></p>"
        return error_msg, session_id

def get_or_create_session(student_id, session_id=None):
    """Get existing session or create new one"""
    if session_id:
        session = ChatbotSession.query.filter_by(session_id=session_id).first()
        if session:
            session.last_activity = datetime.utcnow()
            db.session.commit()
            return session
    
    if student_id:
        # Create new session for student
        session_id = str(uuid.uuid4())
        session = ChatbotSession(
            student_id=student_id,
            session_id=session_id,
            conversation_history="[]"
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    return None

def update_conversation_history(session, role, message):
    """Update conversation history in session"""
    if session:
        try:
            history = json.loads(session.conversation_history) if session.conversation_history else []
            history.append({
                "role": role,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            # Keep only last 20 messages
            if len(history) > 20:
                history = history[-20:]
            session.conversation_history = json.dumps(history)
            session.last_activity = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            print(f"Error updating conversation history: {e}")

def get_conversation_context(session):
    """Get recent conversation context for better continuity"""
    if not session or not session.conversation_history:
        return ""
    
    try:
        history = json.loads(session.conversation_history) if session.conversation_history else []
        if len(history) < 2:
            return ""
        
        # Get last 2 exchanges for context
        recent_context = []
        for i in range(max(0, len(history) - 4), len(history)):
            recent_context.append(f"{history[i]['role'].title()}: {history[i]['message']}")
        
        return "Recent conversation:\n" + "\n".join(recent_context[-4:]) + "\n"
    except Exception as e:
        print(f"Error getting conversation context: {e}")
        return ""

def get_context_for_student(student_id):
    """Get student context for enhanced responses"""
    if not student_id:
        return ""
    
    try:
        student = StudentProfile.query.get(student_id)
        if not student:
            return ""
        
        # Get recent applications and their status
        recent_applications = Application.query.filter_by(student_id=student_id).order_by(Application.applied_date.desc()).limit(3).all()
        
        context_parts = [
            f"Student Profile: {student.full_name} ({student.roll_number})",
            f"Branch: {student.branch}, CGPA: {student.cgpa}",
            f"Skills: {student.skills or 'Not specified'}"
        ]
        
        if recent_applications:
            context_parts.append("Recent Applications:")
            for app in recent_applications:
                context_parts.append(f"- {app.job_posting.title} at {app.job_posting.company.company_name} (Status: {app.status})")
        
        return "\n".join(context_parts)
    
    except Exception as e:
        print(f"Error getting student context: {e}")
        return ""

def analyze_resume_for_job(resume_text, job_description, student_id, job_id):
    """Analyze resume against job description and store results"""
    try:
        # Calculate similarity using TF-IDF
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        # Extract skills using AI
        skills_prompt = f"Extract technical skills from this resume: {resume_text[:1000]}"
        skills_response = model.generate_content(skills_prompt)
        extracted_skills = skills_response.text
        
        # Generate AI feedback
        feedback_prompt = f"""
        Resume: {resume_text[:1000]}
        Job Description: {job_description[:1000]}
        Similarity Score: {similarity_score:.2f}
        
        Provide specific feedback on how to improve the resume for this job.
        """
        feedback_response = model.generate_content(feedback_prompt)
        ai_feedback = feedback_response.text
        
        # Store analysis
        analysis = ResumeAnalysis(
            student_id=student_id,
            job_id=job_id,
            similarity_score=similarity_score,
            extracted_skills=extracted_skills,
            ai_feedback=ai_feedback
        )
        db.session.add(analysis)
        db.session.commit()
        
        return similarity_score, extracted_skills, ai_feedback
        
    except Exception as e:
        print(f"Error in resume analysis: {e}")
        return 0.0, "", f"Error analyzing resume: {str(e)}"

def predict_selection_chances(application_id):
    """Predict selection chances for an application"""
    try:
        application = Application.query.get(application_id)
        if not application:
            return 0.0, 0.0, "Application not found"
        
        student = application.student
        job = application.job_posting
        
        # Get resume analysis if available
        analysis = ResumeAnalysis.query.filter_by(
            student_id=student.id, 
            job_id=job.id
        ).first()
        
        # Calculate prediction factors
        cgpa_match = 1.0 if student.cgpa >= job.cgpa_criteria else student.cgpa / job.cgpa_criteria
        branch_match = 1.0 if student.branch in job.eligible_branches else 0.0
        resume_match = analysis.similarity_score if analysis else 0.5
        
        # Weighted prediction
        prediction_score = (cgpa_match * 0.3 + branch_match * 0.3 + resume_match * 0.4) * 100
        
        # Generate reasoning
        reasoning_prompt = f"""
        Student: {student.full_name} (CGPA: {student.cgpa}, Branch: {student.branch})
        Job: {job.title} at {job.company.company_name}
        Requirements: CGPA ≥ {job.cgpa_criteria}, Branches: {job.eligible_branches}
        Resume Match: {resume_match:.2f}
        
        Provide reasoning for the selection prediction of {prediction_score:.1f}%.
        """
        reasoning_response = model.generate_content(reasoning_prompt)
        reasoning = reasoning_response.text
        
        # Store prediction
        prediction = SelectionPrediction(
            application_id=application_id,
            prediction_score=prediction_score,
            confidence_level=0.8,  # Could be calculated based on data quality
            reasoning=reasoning
        )
        db.session.add(prediction)
        db.session.commit()
        
        return prediction_score, 0.8, reasoning
        
    except Exception as e:
        print(f"Error in selection prediction: {e}")
        return 0.0, 0.0, f"Error predicting selection: {str(e)}"

def generate_jd_questions(job_id, question_type="technical", num_questions=5):
    """Generate questions based on job description"""
    try:
        job = JobPosting.query.get(job_id)
        if not job:
            return []
        
        prompt = f"""
        Generate {num_questions} {question_type} interview questions for this job:
        
        Job Title: {job.title}
        Company: {job.company.company_name}
        Description: {job.description}
        Requirements: CGPA ≥ {job.cgpa_criteria}, Branches: {job.eligible_branches}
        
        Generate {question_type} questions that would be relevant for this position.
        """
        
        response = model.generate_content(prompt)
        questions_text = response.text
        
        # Parse questions (assuming they're numbered or bulleted)
        questions = []
        lines = questions_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up the question
                question_text = re.sub(r'^\d+\.\s*|^[-•]\s*', '', line)
                if question_text:
                    questions.append(question_text)
        
        # Store questions in database
        stored_questions = []
        for question in questions[:num_questions]:
            jd_question = JDQuestions(
                job_id=job_id,
                question_type=question_type,
                question_text=question,
                difficulty_level="medium"  # Could be determined by AI
            )
            db.session.add(jd_question)
            stored_questions.append(jd_question)
        
        db.session.commit()
        return stored_questions
        
    except Exception as e:
        print(f"Error generating JD questions: {e}")
        return []

def get_mock_interview_questions(student_id, topic="general"):
    """Get questions for mock interview"""
    try:
        student = StudentProfile.query.get(student_id)
        if not student:
            return []
        
        # Get recent applications for context
        recent_app = Application.query.filter_by(student_id=student_id).order_by(Application.applied_date.desc()).first()
        
        if recent_app and recent_app.job_posting:
            # Use job-specific questions
            questions = JDQuestions.query.filter_by(job_id=recent_app.job_posting.id).limit(10).all()
            if questions:
                return [q.question_text for q in questions]
        
        # Generate general questions
        prompt = f"""
        Generate 5 interview questions for a {student.branch} student with CGPA {student.cgpa}.
        Topic: {topic}
        Include a mix of technical and behavioral questions.
        """
        
        response = model.generate_content(prompt)
        questions_text = response.text
        
        # Parse questions
        questions = []
        lines = questions_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                question_text = re.sub(r'^\d+\.\s*|^[-•]\s*', '', line)
                if question_text:
                    questions.append(question_text)
        
        return questions[:5]
        
    except Exception as e:
        print(f"Error getting mock interview questions: {e}")
        return []

def format_response(text):
    """Formats the bot's response text into simple HTML."""
    # This function is now less critical as we ask the AI for HTML,
    # but can be a fallback.
    text = text.replace('\n', '<br>')
    # Simple bolding for text like **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return text

def clear_chatbot_session(session_id):
    """Clear chat history for a given session"""
    try:
        session = ChatbotSession.query.filter_by(session_id=session_id).first()
        if session:
            session.conversation_history = "[]"
            session.last_activity = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error clearing session: {e}")
        return False

def handle_resume_review_request(user_input, student_id, conversation_context):
    """Handle resume review requests from students"""
    try:
        if not student_id:
            return "<p><i>Please log in as a student to review your resume.</i></p>"
        
        student = StudentProfile.query.get(student_id)
        if not student or not student.resume_file:
            return "<p><b>Resume Review:</b></p><p><i>You haven't uploaded a resume yet. Please upload your resume in your profile first.</i></p>"
        
        # Get resume text using the function from routes.py
        from routes import get_resume_text
        resume_text = get_resume_text(student)
        
        if not resume_text:
            return "<p><b>Resume Review:</b></p><p><i>Could not read your resume file. Please upload a valid PDF.</i></p>"
        
        context = get_context_for_student(student_id)
        enhanced_prompt = f"""
{context}

{conversation_context}

The student wants to review their resume. Please provide a comprehensive analysis in simple, clear language.

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Resume Content:
{resume_text[:2000]}

Please provide:
1. Overall assessment
2. Key strengths
3. Areas for improvement
4. Specific suggestions
5. Formatting tips

Write in simple language that anyone can understand.
"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"<p><i>Error reviewing resume: {str(e)}</i></p>"

def handle_resume_analysis_request(user_input, student_id, conversation_context):
    """Handle detailed resume analysis with specific focus areas"""
    try:
        if not student_id:
            return "<p><i>Please log in as a student to analyze your resume.</i></p>"
        
        student = StudentProfile.query.get(student_id)
        if not student or not student.resume_file:
            return "<p><b>Resume Analysis:</b></p><p><i>You haven't uploaded a resume yet. Please upload your resume in your profile first.</i></p>"
        
        # Get resume text using the function from routes.py
        from routes import get_resume_text
        resume_text = get_resume_text(student)
        
        if not resume_text:
            return "<p><b>Resume Analysis:</b></p><p><i>Could not read your resume file. Please upload a valid PDF.</i></p>"
        
        # Determine analysis type from user input
        analysis_type = "comprehensive"
        if "skills" in user_input.lower():
            analysis_type = "skills"
        elif "format" in user_input.lower() or "layout" in user_input.lower():
            analysis_type = "formatting"
        elif "grammar" in user_input.lower() or "language" in user_input.lower():
            analysis_type = "grammar"
        
        context = get_context_for_student(student_id)
        
        if analysis_type == "skills":
            enhanced_prompt = f"""
{context}

{conversation_context}

The student wants to analyze the skills in their resume. Please focus on:

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Resume Content:
{resume_text[:2000]}

Please analyze:
1. Technical skills mentioned
2. Soft skills highlighted
3. Skill relevance to their field
4. Missing important skills
5. Skill development suggestions

Write in simple, clear language.
"""
        elif analysis_type == "formatting":
            enhanced_prompt = f"""
{context}

{conversation_context}

The student wants to analyze the formatting of their resume. Please focus on:

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Resume Content:
{resume_text[:2000]}

Please analyze:
1. Overall layout and structure
2. Section organization
3. Visual presentation
4. Readability
5. Formatting improvements

Write in simple, clear language.
"""
        elif analysis_type == "grammar":
            enhanced_prompt = f"""
{context}

{conversation_context}

The student wants to analyze the grammar and language of their resume. Please focus on:

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Resume Content:
{resume_text[:2000]}

Please analyze:
1. Grammar and spelling
2. Language quality
3. Writing style
4. Professional tone
5. Language improvements

Write in simple, clear language.
"""
        else:
            enhanced_prompt = f"""
{context}

{conversation_context}

The student wants a comprehensive analysis of their resume. Please provide:

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Resume Content:
{resume_text[:2000]}

Please analyze:
1. Overall assessment
2. Content quality
3. Structure and formatting
4. Language and grammar
5. Skills presentation
6. Specific improvements

Write in simple, clear language.
"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"<p><i>Error analyzing resume: {str(e)}</i></p>"

def handle_interview_questions_request(user_input, student_id, conversation_context):
    """Handle interview question requests"""
    try:
        if not student_id:
            return "<p><i>Please log in as a student to get interview questions.</i></p>"
        
        student = StudentProfile.query.get(student_id)
        if not student:
            return "<p><i>Student profile not found.</i></p>"
        
        context = get_context_for_student(student_id)
        
        # Determine question type from user input
        question_type = "general"
        if "technical" in user_input.lower():
            question_type = "technical"
        elif "behavioral" in user_input.lower():
            question_type = "behavioral"
        elif "aptitude" in user_input.lower():
            question_type = "aptitude"
        
        enhanced_prompt = f"""
{context}

{conversation_context}

The student wants interview questions. Please provide {question_type} interview questions.

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Please provide:
1. 5-10 relevant {question_type} interview questions
2. Sample answers or key points for each question
3. Tips for answering these types of questions
4. Common mistakes to avoid

Write in simple, clear language that anyone can understand.
"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"<p><i>Error generating interview questions: {str(e)}</i></p>"

def handle_selection_prediction_request(user_input, student_id, conversation_context):
    """Handle selection prediction requests"""
    try:
        if not student_id:
            return "<p><i>Please log in as a student to get selection predictions.</i></p>"
        
        student = StudentProfile.query.get(student_id)
        if not student:
            return "<p><i>Student profile not found.</i></p>"
        
        # Get recent applications
        recent_applications = Application.query.filter_by(student_id=student_id).order_by(Application.applied_date.desc()).limit(3).all()
        
        if not recent_applications:
            return "<p><b>Selection Prediction:</b></p><p><i>You haven't applied to any jobs yet. Apply to some jobs first to get selection predictions.</i></p>"
        
        context = get_context_for_student(student_id)
        
        enhanced_prompt = f"""
{context}

{conversation_context}

The student wants to know their selection chances. Please analyze their profile and recent applications.

Student Profile: {student.full_name} ({student.roll_number})
Branch: {student.branch}, CGPA: {student.cgpa}

Recent Applications:
{chr(10).join([f"- {app.job_posting.title} at {app.job_posting.company.company_name} (Status: {app.status})" for app in recent_applications])}

Please provide:
1. Overall selection chances analysis
2. Factors affecting their selection
3. Strengths they can highlight
4. Areas for improvement
5. Tips to increase selection chances

Write in simple, encouraging language that motivates the student.
"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"<p><i>Error predicting selection chances: {str(e)}</i></p>"

def handle_coding_request(user_input, student_id, conversation_context):
    """Handle coding and programming related questions"""
    try:
        context = get_context_for_student(student_id)
        enhanced_prompt = f"""
{context}

{conversation_context}

The student is asking about coding/programming. Please help them with:
- Code debugging and error fixing
- Programming concepts explanation
- Algorithm and data structure help
- Best practices and tips
- Step-by-step problem solving

Student Question: {user_input}

Please provide a clear, step-by-step explanation that a beginner can understand. Use code examples where helpful.
"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"<p><i>Error helping with coding: {str(e)}</i></p>"

def handle_engineering_request(user_input, student_id, conversation_context):
    """Handle engineering and technical questions"""
    try:
        context = get_context_for_student(student_id)
        enhanced_prompt = f"""
{context}

{conversation_context}

The student is asking about engineering/technical topics. Please help them with:
- Math and physics problems
- Engineering concepts
- Circuit analysis
- Mechanical design
- Calculations and formulas
- Step-by-step problem solving

Student Question: {user_input}

Please provide a clear, step-by-step explanation that a beginner can understand. Use examples and analogies where helpful.
"""
        
        response = model.generate_content(enhanced_prompt)
        return response.text
    except Exception as e:
        return f"<p><i>Error helping with engineering: {str(e)}</i></p>"
