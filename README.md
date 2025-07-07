# College Placement Portal

A comprehensive Flask-based web application that serves as a college placement portal connecting students, companies, and CDC (Career Development Cell) officers. The platform facilitates the entire placement process with AI-powered features.

View my real time project on this : https://collegeplacementportal.onrender.com

## 🚀 Features

### Core Functionality
- **User Management**: Three user types (Students, Companies, CDC Officers)
- **Job Posting & Applications**: Complete job application workflow
- **Interview Management**: Schedule interviews, provide feedback, track rounds
- **Mock Interviews**: CDC can schedule and provide feedback for mock interviews
- **Application Tracking**: Real-time status updates and notifications

### AI-Powered Features
- **Intelligent Chatbot**: Google Gemini-powered assistant for career guidance
- **Resume Analysis**: Comprehensive resume review with grammar, skills, and formatting analysis
- **Selection Prediction**: ML-based prediction of selection chances
- **Interview Question Generation**: AI-generated technical, behavioral, and aptitude questions

## 🤖 Enhanced Chatbot Features

### Resume Review Commands
- `review resume` - Comprehensive resume analysis
- `analyze resume grammar` - Grammar and language analysis
- `analyze resume skills` - Skills presentation analysis
- `analyze resume formatting` - Structure and formatting review

### Interview Preparation
- `interview questions technical` - Technical interview questions
- `interview questions behavioral` - Behavioral interview questions
- `interview questions aptitude` - Aptitude test preparation

### Career Guidance
- `selection chances` - Selection prediction analysis
- General career advice and placement tips

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CollegePlacementPortal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   GOOGLE_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_secret_key_here
   MAIL_USERNAME=your_email@example.com
   MAIL_PASSWORD=your_email_password
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## 🔧 Configuration

### API Keys
- **Google Gemini API**: Required for chatbot functionality
- Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Email Configuration
Update email settings in `config.py` for notifications:
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

## 📱 Usage

### For Students
1. **Register/Login** as a student
2. **Complete Profile** with resume content
3. **Browse Jobs** and apply to eligible positions
4. **Use AI Chatbot** for career guidance
5. **Review Resume** with AI analysis
6. **Track Applications** and interview status

### For Companies
1. **Register/Login** as a company
2. **Post Job Openings** with specific criteria
3. **Review Applications** from students
4. **Schedule Interviews** and provide feedback
5. **Track Hiring Process**

### For CDC Officers
1. **Register/Login** as CDC officer
2. **Manage Companies** and job postings
3. **Monitor Applications** across all students
4. **Schedule Mock Interviews** and provide feedback
5. **Generate Reports** and provide guidance

## 🎯 AI Chatbot Commands

### Resume Analysis
```
review resume
analyze resume grammar
analyze resume skills
analyze resume formatting
```

### Interview Preparation
```
interview questions technical
interview questions behavioral
interview questions aptitude
```

### Career Guidance
```
selection chances
How to improve my resume?
Interview preparation tips
Communication skills improvement
Career guidance for my branch
```

## 📊 Database Models

- **User Management**: User, StudentProfile, CompanyProfile, CDCProfile
- **Job System**: JobPosting, Application, InterviewRound, InterviewFeedback
- **AI Features**: ResumeAnalysis, SelectionPrediction, ChatbotSession, JDQuestions
- **Mock Interviews**: MockInterview

## 🔒 Security Features

- **Password Hashing**: Secure password storage
- **Session Management**: Flask-Login integration
- **Role-based Access**: Different permissions for each user type
- **File Upload Security**: Restricted file types and sizes

## 🚀 Deployment

### Production Setup
1. Set environment variables for production
2. Use production WSGI server (Gunicorn, uWSGI)
3. Configure reverse proxy (Nginx)
4. Set up SSL certificates
5. Use production database (PostgreSQL, MySQL)

### Environment Variables
```bash
FLASK_ENV=production
SECRET_KEY=your_secure_secret_key
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=your_database_url
MAIL_SERVER=your_smtp_server
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

## 📝 API Documentation

### Chatbot API
- **POST** `/chatbot/api` - Send message to chatbot
- **POST** `/chatbot/clear` - Clear chat session

### Resume Review API
- **GET/POST** `/resume/review` - Comprehensive resume analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Updates

### Recent Updates
- Enhanced chatbot with comprehensive resume analysis
- Added selection prediction functionality
- Improved interview question generation
- Better UI/UX for chatbot interface
- Added resume review dedicated page

### Planned Features
- Email notifications for application updates
- Advanced analytics dashboard
- Mobile app development
- Integration with job portals
- Video interview support 
