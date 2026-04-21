/**
 * ChestGuard NeuralScan — Chat Interface
 * Handles chat panel, messaging, typing indicators, and AI responses.
 */

document.addEventListener('DOMContentLoaded', () => {
    const chatFab = document.getElementById('chat-fab');
    const chatPanel = document.getElementById('chat-panel');
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // FAB toggle
    chatFab.addEventListener('click', () => {
        toggleChat();
    });

    // Close button
    chatCloseBtn.addEventListener('click', () => {
        if (AppState.chatOpen) toggleChat();
    });

    // Send message
    chatSendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Quick questions
    addQuickQuestions();

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, 'user');
        chatInput.value = '';

        // Show typing indicator
        const typingId = showTyping();

        // Update status
        document.getElementById('chat-status').textContent = 'Thinking...';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remove typing indicator
            removeTyping(typingId);

            if (data.error && !data.response) {
                addMessage('Sorry, I encountered an error. Please try again.', 'ai');
            } else {
                // Typewriter effect for AI response
                await typewriterMessage(data.response, 'ai');
            }

        } catch (error) {
            removeTyping(typingId);
            addMessage('Connection error. Please check if the server is running.', 'ai');
        }

        document.getElementById('chat-status').textContent = 'Ready';
    }

    function addMessage(text, role) {
        const msg = document.createElement('div');
        msg.className = `chat-msg ${role}`;
        
        const icon = role === 'ai' ? 'fa-robot' : 'fa-user';
        
        msg.innerHTML = `
            <div class="chat-msg-avatar"><i class="fas ${icon}"></i></div>
            <div class="chat-msg-content"><p>${formatText(text)}</p></div>
        `;
        
        chatMessages.appendChild(msg);
        scrollToBottom();
        return msg;
    }

    async function typewriterMessage(text, role) {
        const msg = document.createElement('div');
        msg.className = `chat-msg ${role}`;
        msg.innerHTML = `
            <div class="chat-msg-avatar"><i class="fas fa-robot"></i></div>
            <div class="chat-msg-content"><p></p></div>
        `;
        chatMessages.appendChild(msg);
        
        const contentEl = msg.querySelector('p');
        const formattedText = formatText(text);
        
        // Fast typewriter - reveal in chunks
        const chunkSize = 3;
        for (let i = 0; i < formattedText.length; i += chunkSize) {
            contentEl.innerHTML = formattedText.substring(0, i + chunkSize);
            scrollToBottom();
            await new Promise(r => setTimeout(r, 8));
        }
        contentEl.innerHTML = formattedText;
        scrollToBottom();
    }

    function showTyping() {
        const id = 'typing-' + Date.now();
        const msg = document.createElement('div');
        msg.className = 'chat-msg ai';
        msg.id = id;
        msg.innerHTML = `
            <div class="chat-msg-avatar"><i class="fas fa-robot"></i></div>
            <div class="chat-msg-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(msg);
        scrollToBottom();
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatText(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    function addQuickQuestions() {
        // Add quick question buttons after the initial AI message
        const quickDiv = document.createElement('div');
        quickDiv.className = 'chat-msg ai';
        quickDiv.style.flexDirection = 'column';
        quickDiv.style.alignItems = 'flex-start';
        quickDiv.style.paddingLeft = '42px';
        
        const questions = [
            'What do my results mean?',
            'Should I be worried?',
            'What tests should I get?',
            'Explain the NeuralScore'
        ];
        
        let html = '<div style="display:flex;flex-wrap:wrap;gap:6px;">';
        questions.forEach(q => {
            html += `<button class="btn btn-outline btn-sm" onclick="quickQuestion('${q}')" style="font-size:0.75rem;padding:4px 10px;">${q}</button>`;
        });
        html += '</div>';
        
        quickDiv.innerHTML = html;
        chatMessages.appendChild(quickDiv);
    }
});

// Global quick question handler
function quickQuestion(question) {
    const input = document.getElementById('chat-input');
    if (input.disabled) {
        showToast('Please analyze an X-ray first', 'warning');
        return;
    }
    input.value = question;
    document.getElementById('chat-send-btn').click();
}
