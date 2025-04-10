# Simple rule-based chatbot for placement-related queries

import re

# Define patterns and responses
FAQ_RESPONSES = {
    r'(?i).*resume.*': [
        "For a good resume, focus on these key elements: 1) Clear formatting, 2) Relevant skills and experiences, 3) Quantifiable achievements, and 4) No grammar/spelling errors. Keep it to one page if possible.",
        "Here are some resume tips: 1) Use action verbs, 2) Customize for each job, 3) Include relevant projects and internships, 4) Highlight technical skills relevant to the position."
    ],
    
    r'(?i).*interview.*tips.*': [
        "Interview tips: 1) Research the company thoroughly, 2) Practice common questions, 3) Prepare examples of your work/projects, 4) Dress professionally, 5) Arrive early, 6) Ask thoughtful questions.",
        "For technical interviews: 1) Review core concepts, 2) Practice problem-solving aloud, 3) Clarify questions before answering, 4) Show your thought process, 5) Test your solutions with examples."
    ],
    
    r'(?i).*prepare.*technical.*interview.*': [
        "For technical interviews: 1) Study fundamental concepts in your field, 2) Practice coding problems on platforms like LeetCode or HackerRank, 3) Review data structures and algorithms, 4) Be ready to explain your thought process.",
        "Technical interview preparation: 1) Review your resume projects and be ready to discuss them in detail, 2) Practice system design if relevant, 3) Brush up on language-specific concepts, 4) Understand the company's technical stack."
    ],
    
    r'(?i).*placement.*process.*': [
        "The typical placement process includes: 1) Resume submission, 2) Aptitude/technical test, 3) Technical interview, 4) HR interview, and 5) Final selection. The number of rounds may vary by company.",
        "Each company's placement process is slightly different. Generally, there's a pre-placement talk, followed by screening tests, multiple rounds of interviews, and then final selection."
    ],
    
    r'(?i).*aptitude.*test.*': [
        "To prepare for aptitude tests: 1) Practice quantitative problems, 2) Improve logical reasoning, 3) Work on verbal ability, 4) Take timed mock tests, 5) Review basic mathematics (percentages, ratios, etc.)",
        "Aptitude tests typically cover numerical ability, logical reasoning, verbal ability, and sometimes technical knowledge. Regular practice using resources like IndiaBix or previous year questions is helpful."
    ],
    
    r'(?i).*group.*discussion.*': [
        "Group discussion tips: 1) Initiate or conclude if possible, 2) Be clear and concise, 3) Support points with examples, 4) Listen actively, 5) Be respectful of others' views, 6) Include quiet participants.",
        "In group discussions, focus on: 1) Content quality over quantity, 2) Body language, 3) Logical flow of thoughts, 4) Balancing assertiveness with respect, 5) Staying on topic."
    ],
    
    r'(?i).*hr.*interview.*': [
        "For HR interviews: 1) Be ready to discuss your background, 2) Prepare for 'Tell me about yourself', 3) Know why you want to join the company, 4) Ask thoughtful questions, 5) Understand the company culture.",
        "Common HR questions include: 'Why should we hire you?', 'Where do you see yourself in 5 years?', 'What are your strengths/weaknesses?', 'Why do you want to work with us?', 'How do you handle stress?'"
    ],
    
    r'(?i).*dress.*code.*': [
        "For placement interviews, business formal is usually expected. Men: formal shirt, trousers, tie, and formal shoes. Women: formal shirt/blouse with trousers/formal skirt, or a business suit.",
        "When in doubt about dress code, it's better to be slightly overdressed than underdressed. Professional appearance shows you take the opportunity seriously."
    ],
    
    r'(?i).*salary.*negotiation.*': [
        "For salary negotiation: 1) Research industry standards, 2) Know your worth, 3) Consider the entire compensation package, 4) Be professional and reasonable, 5) Get the final offer in writing.",
        "As a fresher, you may have limited negotiation leverage, but you can still discuss: 1) Joining bonuses, 2) Relocation assistance, 3) Training opportunities, 4) Growth paths."
    ],
    
    r'(?i).*resume.*projects.*': [
        "For resume projects: 1) Focus on relevant ones, 2) Explain your role clearly, 3) Highlight technologies used, 4) Quantify impact where possible, 5) Be prepared to discuss in detail.",
        "When showcasing projects, explain: 1) Problem statement, 2) Your solution approach, 3) Technologies/methods used, 4) Challenges faced and overcome, 5) Results and learnings."
    ],
    
    r'(?i).*internship.*': [
        "Internships are valuable because they: 1) Provide real-world experience, 2) Help build your network, 3) Let you apply classroom knowledge, 4) Make your resume stronger, 5) Can lead to full-time offers.",
        "To find internships: 1) Use your college placement cell, 2) Check company websites, 3) Network on LinkedIn, 4) Attend job fairs, 5) Look at internship platforms like Internshala."
    ],
    
    r'(?i).*communication.*skills.*': [
        "Improve communication skills by: 1) Reading regularly, 2) Practicing public speaking, 3) Taking feedback seriously, 4) Joining clubs/debates, 5) Recording and analyzing your speaking.",
        "Communication skills are crucial for placements. Practice with mock interviews, group discussions, and presentations. Focus on clarity, confidence, and conciseness."
    ]
}

def get_chatbot_response(user_input):
    """
    Generate a response for a user query based on predefined patterns.
    
    Args:
        user_input: The user's message
    
    Returns:
        str: The chatbot's response
    """
    # Default responses for unrecognized queries
    default_responses = [
        "I'm sorry, I don't have specific information about that. Could you ask something related to placements, resume preparation, or interviews?",
        "I'm not sure I understand. Try asking about interview tips, resume preparation, or the placement process.",
        "That's beyond my current knowledge. I can help with resume building, interview preparation, and placement processes."
    ]
    
    # Check for greetings
    greeting_patterns = [
        r'(?i)^(hi|hello|hey|greetings|howdy)[\s!]*$',
        r'(?i)^(good\s(morning|afternoon|evening))[\s!]*$'
    ]
    
    for pattern in greeting_patterns:
        if re.match(pattern, user_input.strip()):
            return "Hello! I'm your placement assistant. I can help with interview preparation, resume tips, and other placement-related queries. What would you like to know?"
    
    # Check for thanks
    thanks_patterns = [
        r'(?i)^(thanks|thank you|thankyou|thank you so much|thanks a lot|thank you very much)[\s!]*$'
    ]
    
    for pattern in thanks_patterns:
        if re.match(pattern, user_input.strip()):
            return "You're welcome! If you have any more questions about placements or interview preparation, feel free to ask."
    
    # Check for specific queries
    for pattern, responses in FAQ_RESPONSES.items():
        if re.search(pattern, user_input):
            import random
            return random.choice(responses)
    
    # Return default response if no pattern matched
    import random
    return random.choice(default_responses)
