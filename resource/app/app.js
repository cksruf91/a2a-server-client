const API_BASE_URL = 'http://localhost:9201';
const COMPLETE_ENDPOINT = '/chat/complete';
const STREAM_ENDPOINT = '/chat/stream'
let currentMode = 'normal';
let roomId = 'test-room-' + Date.now();
let chatHistory = []; // Store chat history as [["user", "message"], ["assistant", "response"]]
let currentSessionId = null; // Track current session ID

// Session Management
const SESSION_STORAGE_KEY = 'mcp_chat_sessions';

function getSessions() {
    const sessionsJson = localStorage.getItem(SESSION_STORAGE_KEY);
    return sessionsJson ? JSON.parse(sessionsJson) : {};
}

function saveSessions(sessions) {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
}

function getCurrentSession() {
    if (!currentSessionId) return null;
    const sessions = getSessions();
    return sessions[currentSessionId] || null;
}

function saveCurrentSession() {
    if (!currentSessionId || chatHistory.length === 0) return;

    const sessions = getSessions();
    const container = document.getElementById('chatContainer');

    // Get the first user message as title (fallback to timestamp)
    let title = 'New Chat';
    if (chatHistory.length > 0) {
        const firstUserMsg = chatHistory.find(msg => msg[0] === 'user');
        if (firstUserMsg) {
            title = firstUserMsg[1].substring(0, 50) + (firstUserMsg[1].length > 50 ? '...' : '');
        }
    }

    sessions[currentSessionId] = {
        id: currentSessionId,
        title: title,
        roomId: roomId,
        chatHistory: chatHistory,
        chatHTML: container.innerHTML,
        mode: currentMode,
        timestamp: Date.now(),
        lastUpdated: Date.now()
    };

    saveSessions(sessions);
    renderSessionList();
}

function loadSession(sessionId) {
    const sessions = getSessions();
    const session = sessions[sessionId];

    if (!session) return;

    currentSessionId = sessionId;
    roomId = session.roomId;
    chatHistory = session.chatHistory || [];
    currentMode = session.mode || 'normal';

    // Restore chat container
    const container = document.getElementById('chatContainer');
    container.innerHTML = session.chatHTML;

    // Re-attach delete button event handlers
    reattachDeleteHandlers();

    // Update mode toggle
    setMode(currentMode);

    // Update session list to show active session
    renderSessionList();
}

function reattachDeleteHandlers() {
    const container = document.getElementById('chatContainer');
    const deleteButtons = container.querySelectorAll('.delete-message-btn');

    deleteButtons.forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const messageDiv = btn.closest('.message');
            if (messageDiv) {
                deleteMessage(messageDiv);
            }
        };
    });
}

function startNewChat() {
    // Save current session before starting new
    if (currentSessionId && chatHistory.length > 0) {
        saveCurrentSession();
    }

    // Reset to new session
    currentSessionId = 'session-' + Date.now();
    roomId = 'test-room-' + Date.now();
    chatHistory = [];

    // Clear chat container
    const container = document.getElementById('chatContainer');
    container.innerHTML = `
        <div class="message assistant">
            <div class="message-bubble">
                Hello! I'm your MCP assistant with Plan-and-Execute capabilities!
            </div>
            <div class="message-time">Just now</div>
        </div>
    `;

    renderSessionList();
    console.log('Started new chat:', currentSessionId);
}

function deleteSession(sessionId, event) {
    event.stopPropagation(); // Prevent loading the session

    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }

    const sessions = getSessions();
    delete sessions[sessionId];
    saveSessions(sessions);

    // If deleting current session, start new chat
    if (currentSessionId === sessionId) {
        startNewChat();
    } else {
        renderSessionList();
    }
}

function renderSessionList() {
    const sessions = getSessions();
    const sessionList = document.getElementById('sessionList');

    const sessionArray = Object.values(sessions).sort((a, b) => b.lastUpdated - a.lastUpdated);

    if (sessionArray.length === 0) {
        sessionList.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">No saved chats</p>';
        return;
    }

    sessionList.innerHTML = sessionArray.map(session => {
        const date = new Date(session.lastUpdated);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        const isActive = session.id === currentSessionId;

        return `
            <div class="session-item ${isActive ? 'active' : ''}" onclick="loadSession('${session.id}')">
                <div class="session-title">${session.title}</div>
                <div class="session-date">${dateStr}</div>
                <button class="delete-session-btn" onclick="deleteSession('${session.id}', event)" title="Delete chat">×</button>
            </div>
        `;
    }).join('');
}

function deleteMessage(messageDiv) {
    const messageIndex = parseInt(messageDiv.getAttribute('data-message-index'));

    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }

    // Remove from DOM
    messageDiv.remove();

    // Remove from chatHistory (find and remove the pair)
    // Since messages are added in pairs (user + assistant), we need to handle this carefully
    if (messageIndex < chatHistory.length) {
        chatHistory.splice(messageIndex, 1);

        // Update indices for remaining messages
        const container = document.getElementById('chatContainer');
        const messages = container.querySelectorAll('.message[data-message-index]');
        messages.forEach(msg => {
            const idx = parseInt(msg.getAttribute('data-message-index'));
            if (idx > messageIndex) {
                msg.setAttribute('data-message-index', idx - 1);
            }
        });
    }

    // Auto-save session
    saveCurrentSession();
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const container = document.querySelector('.container');

    sidebar.classList.toggle('open');
    container.classList.toggle('sidebar-open');
}

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function addMessage(text, isUser = false, addDeleteBtn = true) {
    const container = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

    // Set data attribute to track message in chatHistory
    const messageIndex = chatHistory.length;
    messageDiv.setAttribute('data-message-index', messageIndex);

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // Apply markdown rendering for assistant messages
    if (!isUser && text) {
        bubble.innerHTML = marked.parse(text);
    } else {
        bubble.textContent = text;
    }

    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString();

    // Add delete button if requested
    if (addDeleteBtn) {
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-message-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete message';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteMessage(messageDiv);
        };
        messageDiv.appendChild(deleteBtn);
    }

    messageDiv.appendChild(bubble);
    messageDiv.appendChild(time);
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;

    return messageDiv;
}

function addLoadingIndicator() {
    const container = document.getElementById('chatContainer');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loadingIndicator';

    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'message-bubble';
    loadingBubble.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;

    loadingDiv.appendChild(loadingBubble);
    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;

    return loadingDiv;
}

function removeLoadingIndicator() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.remove();
    }
}

function showError(message) {
    const container = document.getElementById('chatContainer');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `Error: ${message}`;
    container.appendChild(errorDiv);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    addMessage(message, true);
    input.value = '';

    const sendBtn = document.querySelector('.send-btn');
    sendBtn.disabled = true;

    const loading = addLoadingIndicator();

    try {
        if (currentMode === 'normal') {
            await sendNormalMessage(message);
        } else {
            await sendStreamMessage(message);
        }
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Failed to send message');
    } finally {
        removeLoadingIndicator();
        sendBtn.disabled = false;
    }
}

async function sendNormalMessage(text) {
    console.log(`${API_BASE_URL}${COMPLETE_ENDPOINT}`)
    const response = await fetch(`${API_BASE_URL}${COMPLETE_ENDPOINT}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: text,
            roomId: roomId,
            history: chatHistory
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const assistantMessage = data.message || data.text || JSON.stringify(data);
    addMessage(assistantMessage);

    // Update chat history
    chatHistory.push(["user", text]);
    chatHistory.push(["assistant", assistantMessage]);

    // Auto-save session
    saveCurrentSession();
}

async function sendStreamMessage(text) {
    const response = await fetch(`${API_BASE_URL}${STREAM_ENDPOINT}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: text,
            roomId: roomId,
            history: chatHistory
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedText = '';
    let buffer = '';
    let currentEvent = null;  // Move outside the loop to persist across chunks

    removeLoadingIndicator();
    const messageDiv = addMessage('');
    const bubble = messageDiv.querySelector('.message-bubble');

    console.log('Starting SSE stream...');

    while (true) {
        const {done, value} = await reader.read();

        if (done) {
            console.log('Stream done');
            break;
        }

        buffer += decoder.decode(value, {stream: true});
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
            const trimmedLine = line.trim();
            console.log('Processing line:', JSON.stringify(line));

            if (trimmedLine === '') {
                // Empty line marks the end of an event
                console.log('Empty line - resetting event');
                currentEvent = null;
            } else if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
                console.log('Event type:', currentEvent);
            } else if (line.startsWith('data: ')) {
                const dataStr = line.slice(6).trim();
                console.log('Data string:', dataStr);

                if (dataStr && dataStr !== '[DONE]') {
                    try {
                        const data = JSON.parse(dataStr);
                        console.log('Parsed data:', data, 'Event:', currentEvent);

                        if (currentEvent === 'stream') {
                            // Stream mode: accumulate and display contents
                            if (data.contents) {
                                // Remove status message styling when streaming starts
                                bubble.classList.remove('status-message');
                                accumulatedText += data.contents;
                                bubble.textContent = accumulatedText;
                                console.log('Accumulated text length:', accumulatedText.length);
                            }
                        } else {
                            // Non-stream mode: display status message
                            if (data.message) {
                                // Add status message styling for non-stream events
                                bubble.classList.add('status-message');
                                bubble.textContent = `[${currentEvent || 'working'}] ${data.message}`;
                                console.log('Status message:', data.message);
                            }
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e, dataStr);
                    }
                }
            }
        }
    }

    console.log('Final accumulated text:', accumulatedText);

    // After streaming is complete, render markdown
    if (accumulatedText) {
        // Remove status message styling for final response
        bubble.classList.remove('status-message');
        bubble.innerHTML = marked.parse(accumulatedText);

        // Update chat history
        chatHistory.push(["user", text]);
        chatHistory.push(["assistant", accumulatedText]);

        // Auto-save session
        saveCurrentSession();
    } else {
        // If no accumulated text, keep the last status message
        console.warn('No accumulated text, keeping status message');
    }
}

async function showTools() {
    const modal = document.getElementById('toolsModal');
    const toolsList = document.getElementById('toolsList');

    modal.classList.add('show');
    toolsList.innerHTML = `
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE_URL}/tool/list`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const tools = data.tools || [];

        if (tools.length === 0) {
            toolsList.innerHTML = '<p>No tools available</p>';
            return;
        }

        toolsList.innerHTML = tools.map(tool => `
            <div class="tool-item">
                <div class="tool-name">${tool.name || 'Unnamed Tool'}</div>
                <div class="tool-description">${tool.description || 'No description available'}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tools:', error);
        toolsList.innerHTML = `<div class="error-message">Failed to load tools: ${error.message}</div>`;
    }
}

function closeModal() {
    document.getElementById('toolsModal').classList.remove('show');
}

function resetChat() {
    // Confirm before resetting
    if (!confirm('Are you sure you want to reset the chat history? This action cannot be undone.')) {
        return;
    }

    // Clear chat history
    chatHistory = [];

    // Clear chat container (keep only the welcome message)
    const container = document.getElementById('chatContainer');
    container.innerHTML = `
        <div class="message assistant">
            <div class="message-bubble">
                Hello! I'm your MCP assistant with Plan-and-Execute capabilities!
            </div>
            <div class="message-time">Just now</div>
        </div>
    `;

    // Generate new room ID
    roomId = 'test-room-' + Date.now();

    console.log('Chat history reset successfully');
}

// Close modal when clicking outside
document.getElementById('toolsModal').addEventListener('click', (e) => {
    if (e.target.id === 'toolsModal') {
        closeModal();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Start with a new session
    startNewChat();

    // Load session list
    renderSessionList();
});