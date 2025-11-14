// CashPilot AI - Frontend JavaScript
// API Configuration
const API_BASE = 'http://localhost:8000';

// Global State
let currentUser = null;
let accessToken = null;
let currentConversationId = null;
let conversations = [];

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', init);

function init() {
    // Check for saved session
    const savedToken = localStorage.getItem('accessToken');
    const savedUser = localStorage.getItem('currentUser');

    if (savedToken && savedUser) {
        accessToken = savedToken;
        currentUser = JSON.parse(savedUser);
        showChatScreen();
        loadConversations();
    }

    // Setup event listeners
    setupAuthForms();
}

// ==============================================================================
// Authentication
// ==============================================================================

function setupAuthForms() {
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    document.getElementById('toggleLink').addEventListener('click', toggleAuthForm);
}

function toggleAuthForm() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const toggleText = document.getElementById('toggleText');

    if (loginForm.classList.contains('hidden')) {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        toggleText.innerHTML = 'Don\'t have an account? <a id="toggleLink" class="text-primary-500 hover:text-primary-400 cursor-pointer underline">Register</a>';
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        toggleText.innerHTML = 'Already have an account? <a id="toggleLink" class="text-primary-500 hover:text-primary-400 cursor-pointer underline">Login</a>';
    }

    document.getElementById('toggleLink').addEventListener('click', toggleAuthForm);
    hideMessages();
}

async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    // Disable button and show loading state
    const loginBtn = document.getElementById('loginBtn');
    const loginBtnText = document.getElementById('loginBtnText');
    loginBtn.disabled = true;
    loginBtnText.textContent = 'Logging in...';
    hideMessages();

    try {
        const response = await fetch(`${API_BASE}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        // Re-enable button
        loginBtn.disabled = false;
        loginBtnText.textContent = 'Login';

        if (response.ok) {
            accessToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            showSuccess('✅ Login successful! Taking you to your dashboard...');
            setTimeout(() => {
                showChatScreen();
                loadConversations();
            }, 1500);
        } else {
            // For 401 Unauthorized or 500 (Supabase auth error), assume user doesn't exist
            if (response.status === 401 || response.status === 500) {
                // Show catchy message and switch to register
                showInfo("🚀 New here? Let's get you started! Create your account below.");

                setTimeout(() => {
                    // Pre-fill email and switch to register form
                    document.getElementById('registerEmail').value = email;

                    // Switch to register form if not already there
                    if (document.getElementById('loginForm').classList.contains('hidden') === false) {
                        toggleAuthForm();
                    }

                    // Focus on name field
                    setTimeout(() => {
                        document.getElementById('registerName').focus();
                    }, 300);
                }, 3000); // Wait 3 seconds before redirecting
            } else {
                // Other errors (server issues, etc.)
                const errorMsg = data.detail || 'Login failed';
                showError(errorMsg);
            }
        }
    } catch (error) {
        loginBtn.disabled = false;
        loginBtnText.textContent = 'Login';
        showError('Connection error. Make sure the server is running on port 8000.');
    }
}

async function handleRegister(e) {
    e.preventDefault();

    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    // Disable button and show loading state
    const registerBtn = document.getElementById('registerBtn');
    const registerBtnText = document.getElementById('registerBtnText');
    registerBtn.disabled = true;
    registerBtnText.textContent = 'Creating account...';
    hideMessages();

    try {
        const response = await fetch(`${API_BASE}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        // Re-enable button
        registerBtn.disabled = false;
        registerBtnText.textContent = 'Register';

        if (response.ok) {
            accessToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showSuccess('🎉 Welcome aboard! Taking you to your dashboard...');
            setTimeout(() => {
                showChatScreen();
                loadConversations();
            }, 2000);
        } else {
            // Check if user already exists - ONLY show welcome back for 400 Bad Request
            // This indicates the user definitely already exists (not other errors)
            const errorMsg = data.detail || 'Registration failed';
            if (response.status === 400 &&
                (errorMsg.toLowerCase().includes('already') ||
                 errorMsg.toLowerCase().includes('exists') ||
                 errorMsg.toLowerCase().includes('in use'))) {

                // First show the error message
                showError(errorMsg);

                // After 1.5 seconds, show welcome back message
                setTimeout(() => {
                    showInfo("👋 Welcome back! Let's log you in!");
                }, 1500);

                // After 4 seconds total, redirect to login
                setTimeout(() => {
                    // Pre-fill email and switch to login form
                    document.getElementById('loginEmail').value = email;

                    // Switch to login form if not already there
                    if (document.getElementById('registerForm').classList.contains('hidden') === false) {
                        toggleAuthForm();
                    }

                    // Focus on password field
                    setTimeout(() => {
                        document.getElementById('loginPassword').focus();
                    }, 300);
                }, 4000);
            } else {
                // For all other errors (server errors, validation errors, etc.)
                showError(errorMsg);
            }
        }
    } catch (error) {
        registerBtn.disabled = false;
        registerBtnText.textContent = 'Register';
        showError('Connection error. Make sure the server is running on port 8000.');
    }
}

function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('currentUser');
    accessToken = null;
    currentUser = null;
    currentConversationId = null;
    showAuthScreen();
}

// ==============================================================================
// Screen Management
// ==============================================================================

function showAuthScreen() {
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('chatScreen').classList.add('hidden');
}

function showChatScreen() {
    document.getElementById('authScreen').classList.add('hidden');
    document.getElementById('chatScreen').classList.remove('hidden');
    document.getElementById('userName').textContent = currentUser.name || currentUser.email;
}

// ==============================================================================
// Conversations
// ==============================================================================

async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/chat/conversations`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });

        conversations = await response.json();
        renderConversations();

        // Auto-select first conversation
        if (!currentConversationId && conversations.length > 0) {
            selectConversation(conversations[0].id);
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
    }
}

function renderConversations() {
    const list = document.getElementById('conversationsList');
    list.innerHTML = '';

    if (conversations.length === 0) {
        list.innerHTML = '<div class="text-center text-gray-500 py-4">No conversations yet</div>';
        return;
    }

    conversations.forEach(conv => {
        const isActive = conv.id === currentConversationId;
        const item = document.createElement('div');
        item.className = `p-4 rounded-lg cursor-pointer transition-all ${
            isActive
                ? 'bg-primary-500/20 border border-primary-500/50'
                : 'bg-white/5 hover:bg-white/10'
        }`;

        item.innerHTML = `
            <div class="font-medium text-gray-200 truncate">${conv.title}</div>
            <div class="text-xs text-gray-400 mt-1">${new Date(conv.updated_at).toLocaleDateString()}</div>
        `;

        item.onclick = () => selectConversation(conv.id);
        list.appendChild(item);
    });
}

async function createNewConversation() {
    try {
        const response = await fetch(`${API_BASE}/chat/conversations`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: 'New Conversation' })
        });

        const newConv = await response.json();

        if (!response.ok) {
            // Server returned an error
            const errorMsg = newConv.detail || 'Failed to create conversation';
            showError(errorMsg);
            console.error('Failed to create conversation:', errorMsg);
            return;
        }

        conversations.unshift(newConv);
        renderConversations();
        selectConversation(newConv.id);
    } catch (error) {
        console.error('Failed to create conversation:', error);
        showError('Connection error. Please try again.');
    }
}

async function selectConversation(convId) {
    currentConversationId = convId;
    renderConversations();
    await loadMessages();
}

// ==============================================================================
// Messages
// ==============================================================================

async function loadMessages() {
    if (!currentConversationId) return;

    try {
        const response = await fetch(
            `${API_BASE}/chat/conversations/${currentConversationId}/messages`,
            { headers: { 'Authorization': `Bearer ${accessToken}` } }
        );

        const messages = await response.json();
        renderMessages(messages);
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

function renderMessages(messages) {
    const messagesArea = document.getElementById('messagesArea');
    const welcomeMessage = document.getElementById('welcomeMessage');
    const typingIndicator = document.getElementById('typingIndicator');

    // Show/hide welcome message
    welcomeMessage.style.display = messages.length === 0 ? 'flex' : 'none';

    // Clear existing messages
    Array.from(messagesArea.children).forEach(child => {
        if (child.id !== 'welcomeMessage' && child.id !== 'typingIndicator') {
            child.remove();
        }
    });

    // Render messages
    messages.forEach(msg => {
        const messageEl = createMessageElement(msg);
        messagesArea.insertBefore(messageEl, typingIndicator);
    });

    scrollToBottom();
}

function createMessageElement(msg) {
    const div = document.createElement('div');
    div.className = `flex message-fade-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`;

    const messageContent = `
        <div class="max-w-2xl ${
            msg.role === 'user'
                ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-2xl rounded-br-sm'
                : 'bg-white/10 text-gray-100 rounded-2xl rounded-bl-sm'
        } px-6 py-4">
            <div class="whitespace-pre-wrap">${escapeHtml(msg.content)}</div>
            <div class="text-xs opacity-70 mt-2">${new Date(msg.timestamp).toLocaleTimeString()}</div>
        </div>
    `;

    div.innerHTML = messageContent;
    return div;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();

    if (!content) return;

    // Create conversation if none exists
    if (!currentConversationId) {
        await createNewConversation();
        if (!currentConversationId) return; // Failed to create
    }

    // Disable input
    input.disabled = true;
    document.getElementById('sendBtn').disabled = true;

    // Add user message to UI
    const userMsg = { role: 'user', content, timestamp: new Date().toISOString() };
    const messagesArea = document.getElementById('messagesArea');
    const userMsgEl = createMessageElement(userMsg);
    messagesArea.insertBefore(userMsgEl, document.getElementById('typingIndicator'));

    // Hide welcome
    document.getElementById('welcomeMessage').style.display = 'none';

    // Show typing indicator
    document.getElementById('typingIndicator').classList.remove('hidden');
    scrollToBottom();

    // Clear input
    input.value = '';

    try {
        const response = await fetch(
            `${API_BASE}/chat/conversations/${currentConversationId}/messages`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            }
        );

        const assistantMsg = await response.json();

        // Hide typing indicator
        document.getElementById('typingIndicator').classList.add('hidden');

        // Add assistant message
        const assistantMsgEl = createMessageElement(assistantMsg);
        messagesArea.insertBefore(assistantMsgEl, document.getElementById('typingIndicator'));

        scrollToBottom();
        loadConversations(); // Update sidebar
    } catch (error) {
        console.error('Failed to send message:', error);
        document.getElementById('typingIndicator').classList.add('hidden');
        showError('Failed to send message');
    } finally {
        input.disabled = false;
        document.getElementById('sendBtn').disabled = false;
        input.focus();
    }
}

function sendExampleQuery(element) {
    const query = element.textContent.trim().replace(/"/g, '');
    document.getElementById('messageInput').value = query;
    sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// ==============================================================================
// Utility Functions
// ==============================================================================

function scrollToBottom() {
    const messagesArea = document.getElementById('messagesArea');
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function showError(message) {
    const errorEl = document.getElementById('authError');
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
    setTimeout(() => errorEl.classList.add('hidden'), 5000);
}

function showSuccess(message) {
    const successEl = document.getElementById('authSuccess');
    successEl.textContent = message;
    successEl.classList.remove('hidden');
    setTimeout(() => successEl.classList.add('hidden'), 3000);
}

function showInfo(message) {
    // Use success styling for info messages (positive vibe)
    const successEl = document.getElementById('authSuccess');
    successEl.textContent = message;
    successEl.classList.remove('hidden');
    setTimeout(() => successEl.classList.add('hidden'), 4000);
}

function hideMessages() {
    document.getElementById('authError').classList.add('hidden');
    document.getElementById('authSuccess').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
