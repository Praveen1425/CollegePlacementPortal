// Chatbot JavaScript for College Placement Portal

document.addEventListener('DOMContentLoaded', function() {
    // Reference to chat container and form
    const chatContainer = document.getElementById('chatContainer');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('message');
    
    // Scroll to the bottom of the chat container
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Scroll to bottom on page load
    scrollToBottom();
    
    // Handle form submission via AJAX
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            // Only prevent default if we're using AJAX
            // For now, we'll let the form submit normally
            // event.preventDefault();
            
            // Ensure the message is not empty
            if (messageInput.value.trim() === '') {
                event.preventDefault();
                return;
            }
        });
    }
    
    // Handle suggested questions
    const suggestedQuestions = document.querySelectorAll('.suggested-question');
    
    suggestedQuestions.forEach(function(question) {
        question.addEventListener('click', function() {
            if (messageInput) {
                messageInput.value = question.textContent.trim();
                messageInput.focus();
            }
        });
    });
    
    // AJAX version of chat (can be enabled if needed)
    /*
    function sendMessage(message) {
        fetch('/chatbot/api', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Create a bot message element
            displayBotMessage(data.response);
            
            // Clear input field
            messageInput.value = '';
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            displayBotMessage('Sorry, I encountered an error. Please try again.');
        });
    }
    
    function displayUserMessage(message) {
        const userMessageHTML = `
            <div class="message user-message">
                <div class="message-content">
                    <p>${message}</p>
                    <div class="message-time">You</div>
                </div>
            </div>
        `;
        
        chatContainer.insertAdjacentHTML('beforeend', userMessageHTML);
    }
    
    function displayBotMessage(message) {
        const botMessageHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    <div class="bot-indicator">
                        <i class="fas fa-robot"></i>
                        <span class="bot-name">Placement Assistant</span>
                    </div>
                    <p>${message}</p>
                    <div class="message-time">
                        Just now
                    </div>
                </div>
            </div>
        `;
        
        chatContainer.insertAdjacentHTML('beforeend', botMessageHTML);
    }
    */
    
    // Add animation to bot messages
    const botMessages = document.querySelectorAll('.bot-message .message-content p');
    
    botMessages.forEach(function(message) {
        message.innerHTML = message.innerHTML.replace(/\n/g, '<br>');
    });
    
    // Create typing indicator (can be used with AJAX version)
    function createTypingIndicator() {
        const typingHTML = `
            <div class="message bot-message" id="typing-indicator">
                <div class="message-content">
                    <div class="bot-indicator">
                        <i class="fas fa-robot"></i>
                        <span class="bot-name">Placement Assistant</span>
                    </div>
                    <p>
                        <span class="typing-dot">.</span>
                        <span class="typing-dot">.</span>
                        <span class="typing-dot">.</span>
                    </p>
                </div>
            </div>
        `;
        
        chatContainer.insertAdjacentHTML('beforeend', typingHTML);
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
});
