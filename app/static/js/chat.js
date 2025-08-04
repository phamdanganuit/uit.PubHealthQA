
let chatHistory = [];
let isWaitingForResponse = false;
let currentUser = null;
let currentSessionId = null;
let chatSessions = [];

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status on page load
    console.log('Page loaded, checking auth status...');
    checkAuthStatus();
    
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const sourcesPanel = document.getElementById('sources-panel');
    const sourcesContent = document.getElementById('sources-content');
    
    addRippleEffect();
    
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        if (this.scrollHeight > 120) {
            this.style.height = '120px';
            this.style.overflowY = 'auto';
        }
    });
    
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); 
            
            const message = userInput.value.trim();
            
            if (message === '' || isWaitingForResponse) {
                return;
            }
            
            animateSend();
            
            addUserMessage(message);
            
            userInput.value = '';
            userInput.style.height = 'auto';
            
            sendMessageToServer(message);
        }
    });
    
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        
        if (message === '' || isWaitingForResponse) {
            return;
        }
        
        animateSend();
        
        addUserMessage(message);
        
        userInput.value = '';
        userInput.style.height = 'auto';
        
        sendMessageToServer(message);
    });
    
    userInput.focus();
    
    chatMessages.addEventListener('wheel', function(e) {
        e.stopPropagation();
    });
    
    // Removed tilt effects as requested
});

function addRippleEffect() {
    const interactiveElements = document.querySelectorAll('button, .suggestion-item');
    
    interactiveElements.forEach(element => {
        element.classList.add('ripple');
        
        element.addEventListener('click', function(e) {
            const rect = element.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            element.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

function animateSend() {
    const sendButton = document.querySelector('form button');
    sendButton.classList.add('animate-send');
    
    // Tạo hiệu ứng rung nhẹ
    document.querySelector('.input-group').classList.add('pulse-once');
    
    setTimeout(() => {
        sendButton.classList.remove('animate-send');
        document.querySelector('.input-group').classList.remove('pulse-once');
    }, 500);
}


// applyMessageTilt function removed as requested - no more tilt effects

/**
 * @param {HTMLElement} element
 */
function scrollToBottom(element) {
    setTimeout(() => {
        element.scrollTop = element.scrollHeight;
    }, 50);
    
    setTimeout(() => {
        element.scrollTo({
            top: element.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

/**
 * @param {string} message 
 */
function addUserMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">
                <i class="bi bi-person"></i>
            </div>
            <div class="message-text">
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    
    // Removed tilt effects
    
    scrollToBottom(chatMessages);
    
    chatHistory.push({role: 'user', content: message});
    
    showTypingIndicator();
    
    document.getElementById('sources-panel').style.display = 'none';
    
    isWaitingForResponse = true;
}


function showTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    typingIndicator.style.display = 'block';
    typingIndicator.style.opacity = '0';
    
    setTimeout(() => {
        typingIndicator.style.transition = 'opacity 0.3s ease';
        typingIndicator.style.opacity = '1';
    }, 10);
}

/**
 * @param {string} message - Nội dung tin nhắn
 * @param {Array} sources - Nguồn tham khảo
 */
function addBotMessage(message, sources = []) {
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Hiệu ứng fade out cho typing indicator
    typingIndicator.style.opacity = '0';
    
    setTimeout(() => {
        // Ẩn đang nhập
        typingIndicator.style.display = 'none';
        
        // Tạo phần tử HTML cho tin nhắn
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        
        // Xử lý markdown trong tin nhắn (sử dụng thư viện marked.js)
        const markedMessage = marked.parse(message);
        
        // Tạo nội dung tin nhắn
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-avatar">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-text">
                    ${markedMessage}
                </div>
            </div>
        `;
        
        // Thêm tin nhắn vào khung chat
        chatMessages.appendChild(messageElement);
        
        // Removed tilt effects
        
        // Cập nhật lịch sử chat
        chatHistory.push({role: 'assistant', content: message});
        
        // Hiển thị nguồn tham khảo nếu có
        if (sources && sources.length > 0) {
            displaySources(sources);
        }
        
        // Cập nhật trạng thái
        isWaitingForResponse = false;
        
        // Cuộn xuống tin nhắn mới nhất - cải tiến
        scrollToBottom(chatMessages);
        
        // Thêm cuộn lần thứ hai sau khi các hình ảnh có thể đã được tải
        setTimeout(() => {
            scrollToBottom(chatMessages);
        }, 500);
    }, 300);
}

/**
 * Hiển thị nguồn tham khảo
 * @param {Array} sources - Danh sách nguồn tham khảo
 */
function displaySources(sources) {
    const sourcesPanel = document.getElementById('sources-panel');
    const sourcesContent = document.getElementById('sources-content');
    
    // Xóa nội dung cũ
    sourcesContent.innerHTML = '';
    
    // Thêm từng nguồn vào panel
    sources.forEach((source, index) => {
        const sourceElement = document.createElement('div');
        sourceElement.className = 'source-item';
        
        // Xử lý metadata để hiển thị thông tin nguồn phù hợp
        let sourceMetaText = '';
        if (source.metadata) {
            if (source.metadata.title) {
                sourceMetaText += `<strong>${escapeHtml(source.metadata.title)}</strong>`;
            }
            if (source.metadata.law_id) {
                sourceMetaText += ` - ${escapeHtml(source.metadata.law_id)}`;
            }
        }
        
        sourceElement.innerHTML = `
            <div>
                <div class="mb-1">${sourceMetaText || 'Nguồn không xác định'}</div>
                <div class="small text-muted">${escapeHtml(source.content)}</div>
                <div class="small mt-1"><span class="badge bg-primary">Điểm tương đồng: ${(source.similarity * 100).toFixed(1)}%</span></div>
            </div>
        `;
        
        sourcesContent.appendChild(sourceElement);
    });
    
    // Hiển thị panel nguồn với hiệu ứng
    sourcesPanel.style.display = 'block';
    sourcesPanel.style.opacity = '0';
    
    setTimeout(() => {
        sourcesPanel.style.transition = 'opacity 0.5s ease';
        sourcesPanel.style.opacity = '1';
    }, 10);
}

/**
 * Gửi tin nhắn đến server và xử lý phản hồi
 * @param {string} message - Nội dung tin nhắn
 */
async function sendMessageToServer(message) {
    try {
        // Chuẩn bị dữ liệu gửi đi
        const data = {
            message: message,
            history: chatHistory.slice(0, -1) // Không gửi tin nhắn vừa thêm vào
        };
        
        // Gọi API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });
        
        // Kiểm tra phản hồi
        if (!response.ok) {
            throw new Error(`Lỗi kết nối: ${response.status}`);
        }
        
        // Xử lý dữ liệu phản hồi
        const responseData = await response.json();
        
        // Update current session ID
        if (responseData.session_id && responseData.session_id !== 'anonymous') {
            currentSessionId = responseData.session_id;
            // Reload chat history if this is a new session
            if (currentUser) {
                await loadChatHistory();
            }
        }
        
        // Thêm tin nhắn của bot vào khung chat
        addBotMessage(responseData.answer, responseData.sources);
        
    } catch (error) {
        console.error('Lỗi:', error);
        
        // Ẩn đang nhập
        document.getElementById('typing-indicator').style.display = 'none';
        
        // Hiển thị thông báo lỗi
        addBotMessage('Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.');
        
        // Cập nhật trạng thái
        isWaitingForResponse = false;
    }
}

/**
 * Thêm gợi ý vào ô nhập liệu
 * @param {HTMLElement} element - Phần tử chứa gợi ý
 */
// addSuggestion function removed as suggestions were replaced with chat history

/**
 * Escape HTML để ngăn chặn XSS
 * @param {string} html - Chuỗi cần escape
 * @return {string} Chuỗi đã được escape
 */
function escapeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

/**
 * Authentication Functions
 */

/**
 * Check if user is authenticated and update UI
 */
async function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        updateAuthUI(false);
        clearChatHistory(false);  // User not logged in
        return;
    }
    
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const userData = await response.json();
            currentUser = userData;
            console.log('User authenticated successfully, loading chat history...'); // Debug log
            updateAuthUI(true);
            // Load chat history immediately after successful auth
            await loadChatHistory();
        } else {
            // Token invalid or expired
            localStorage.removeItem('access_token');
            currentUser = null;
            currentSessionId = null;
            chatSessions = [];
            updateAuthUI(false);
            clearChatHistory(false);  // User not logged in
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        localStorage.removeItem('access_token');
        currentUser = null;
        currentSessionId = null;
        chatSessions = [];
        updateAuthUI(false);
        clearChatHistory(false);  // User not logged in
    }
}

/**
 * Update authentication UI
 * @param {boolean} isLoggedIn - Whether user is logged in
 */
function updateAuthUI(isLoggedIn) {
    const notLoggedInSection = document.getElementById('not-logged-in');
    const loggedInSection = document.getElementById('logged-in');
    const sidebarAuth = document.getElementById('sidebar-auth');
    const newChatBtn = document.getElementById('new-chat-btn');
    
    if (isLoggedIn) {
        notLoggedInSection.style.display = 'none';
        loggedInSection.style.display = 'block';
        if (sidebarAuth) sidebarAuth.style.display = 'none';
        if (newChatBtn) newChatBtn.style.display = 'block';
    } else {
        notLoggedInSection.style.display = 'block';
        loggedInSection.style.display = 'none';
        if (sidebarAuth) sidebarAuth.style.display = 'block';
        if (newChatBtn) newChatBtn.style.display = 'none';
    }
}

/**
 * Logout function
 */
async function logout() {
    const token = localStorage.getItem('access_token');
    
    try {
        if (token) {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
    } catch (error) {
        console.error('Error during logout:', error);
    } finally {
        // Always remove token and update UI
        localStorage.removeItem('access_token');
        currentUser = null;
        currentSessionId = null;
        chatSessions = [];
        
        // Update auth UI
        updateAuthUI(false);
        
        // Clear and hide chat history
        clearChatHistory(false);  // User not logged in after logout
        
        // Clear current chat but keep welcome message
        const chatMessages = document.getElementById('chat-messages');
        const welcomeMessage = chatMessages.querySelector('.bot-message');
        chatMessages.innerHTML = '';
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
        }
        
        // Show logout message
        addBotMessage('Bạn đã đăng xuất thành công. Một số tính năng có thể bị hạn chế.');
    }
}

/**
 * Get auth headers for API requests
 * @returns {Object} Headers object with authorization if available
 */
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

/**
 * Chat History Functions
 */

/**
 * Load chat history from server
 */
async function loadChatHistory() {
    const historyLoading = document.getElementById('history-loading');
    const historyEmpty = document.getElementById('history-empty');
    const historyItems = document.getElementById('history-items');
    
    if (!currentUser) {
        clearChatHistory(false);  // User not logged in
        return;
    }
    
    // Show loading state
    historyLoading.style.display = 'block';
    historyEmpty.style.display = 'none';
    historyItems.innerHTML = '';
    
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            clearChatHistory(false);  // User not logged in
            return;
        }
        
        const response = await fetch('/api/chat/sessions', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            chatSessions = await response.json();
            console.log('Loaded chat sessions:', chatSessions.length); // Debug log
            displayChatSessions(chatSessions);
        } else {
            console.error('Failed to load chat history, status:', response.status);
            showHistoryEmpty(true);  // User is logged in but failed to load
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
        showHistoryEmpty(true);  // User is logged in but error occurred
    } finally {
        historyLoading.style.display = 'none';
    }
}

/**
 * Display chat sessions in sidebar
 */
function displayChatSessions(sessions) {
    const historyItems = document.getElementById('history-items');
    const historyEmpty = document.getElementById('history-empty');
    
    console.log('Displaying sessions:', sessions?.length || 0); // Debug log
    
    if (!sessions || sessions.length === 0) {
        showHistoryEmpty(true);  // User is logged in but no chat sessions
        return;
    }
    
    historyEmpty.style.display = 'none';
    historyItems.innerHTML = '';
    
    sessions.forEach(session => {
        const sessionElement = document.createElement('div');
        sessionElement.className = 'chat-session-item';
        sessionElement.innerHTML = `
            <div class="session-content" onclick="loadChatSession('${session.session_id}')">
                <div class="session-title">${escapeHtml(session.title)}</div>
                <div class="session-meta">
                    ${formatDate(session.updated_at)} • ${session.message_count} tin nhắn
                </div>
            </div>
            <button class="btn-session-delete" onclick="event.stopPropagation(); deleteChatSession('${session.session_id}')" title="Xóa">
                ×
            </button>
        `;
        
        if (session.session_id === currentSessionId) {
            sessionElement.classList.add('active');
        }
        
        historyItems.appendChild(sessionElement);
    });
    
    console.log('Chat sessions displayed successfully'); // Debug log
}

/**
 * Show empty history state
 * @param {boolean} isLoggedIn - Whether user is logged in
 */
function showHistoryEmpty(isLoggedIn = false) {
    const historyEmpty = document.getElementById('history-empty');
    const historyItems = document.getElementById('history-items');
    const historyLoading = document.getElementById('history-loading');
    const historyEmptyText = document.getElementById('history-empty-text');
    
    historyLoading.style.display = 'none';
    historyItems.innerHTML = '';
    historyEmpty.style.display = 'block';
    
    // Update text based on login status
    if (isLoggedIn) {
        historyEmptyText.textContent = 'Chưa có cuộc trò chuyện nào';
    } else {
        historyEmptyText.textContent = 'Đăng nhập để xem lịch sử chat';
    }
}

/**
 * Clear chat history completely
 * @param {boolean} isLoggedIn - Whether user is logged in
 */
function clearChatHistory(isLoggedIn = false) {
    const historyItems = document.getElementById('history-items');
    const historyLoading = document.getElementById('history-loading');
    const historyEmpty = document.getElementById('history-empty');
    const historyEmptyText = document.getElementById('history-empty-text');
    
    // Clear all elements
    historyItems.innerHTML = '';
    historyLoading.style.display = 'none';
    historyEmpty.style.display = 'block';
    
    // Update text based on login status
    if (isLoggedIn) {
        historyEmptyText.textContent = 'Chưa có cuộc trò chuyện nào';
    } else {
        historyEmptyText.textContent = 'Đăng nhập để xem lịch sử chat';
    }
    
    // Reset variables
    chatSessions = [];
    currentSessionId = null;
    
    // Clear any existing session clicks by removing event listeners
    document.querySelectorAll('.chat-session-item').forEach(item => {
        item.onclick = null;
        item.classList.add('disabled');
    });
}

/**
 * Load specific chat session
 */
async function loadChatSession(sessionId) {
    if (!currentUser) return;
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/chat/sessions/${sessionId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const sessionData = await response.json();
            
            // Clear current chat
            const chatMessages = document.getElementById('chat-messages');
            // Keep only the bot welcome message
            const welcomeMessage = chatMessages.querySelector('.bot-message');
            chatMessages.innerHTML = '';
            if (welcomeMessage) {
                chatMessages.appendChild(welcomeMessage);
            }
            
            // Set current session
            currentSessionId = sessionId;
            
            // Load messages
            sessionData.messages.forEach(msg => {
                if (msg.role === 'user') {
                    addUserMessageFromHistory(msg.content);
                } else {
                    addBotMessageFromHistory(msg.content);
                }
            });
            
            // Update active session in sidebar
            document.querySelectorAll('.chat-session-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[onclick="loadChatSession('${sessionId}')"]`)?.closest('.chat-session-item')?.classList.add('active');
            
        } else {
            console.error('Failed to load chat session');
        }
    } catch (error) {
        console.error('Error loading chat session:', error);
    }
}

/**
 * Create new chat session
 */
async function createNewChat() {
    // Clear current chat
    const chatMessages = document.getElementById('chat-messages');
    // Keep only the bot welcome message
    const welcomeMessage = chatMessages.querySelector('.bot-message');
    chatMessages.innerHTML = '';
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }
    
    // Reset current session
    currentSessionId = null;
    
    // Update active session in sidebar
    document.querySelectorAll('.chat-session-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Focus on input
    document.getElementById('user-input').focus();
}

/**
 * Delete chat session
 */
async function deleteChatSession(sessionId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`/api/chat/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            // If deleting current session, create new chat
            if (sessionId === currentSessionId) {
                createNewChat();
            }
            
            // Reload chat history
            await loadChatHistory();
        } else {
            console.error('Failed to delete chat session');
        }
    } catch (error) {
        console.error('Error deleting chat session:', error);
    }
}

/**
 * Add user message from history (without sending to server)
 */
function addUserMessageFromHistory(message) {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">
                <i class="bi bi-person"></i>
            </div>
            <div class="message-text">
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    scrollToBottom(chatMessages);
}

/**
 * Add bot message from history (without sending to server)
 */
function addBotMessageFromHistory(message) {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    
    const markedMessage = marked.parse(message);
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-text">
                ${markedMessage}
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageElement);
    scrollToBottom(chatMessages);
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Hôm qua';
    } else if (diffDays < 7) {
        return `${diffDays} ngày trước`;
    } else {
        return date.toLocaleDateString('vi-VN');
    }
} 