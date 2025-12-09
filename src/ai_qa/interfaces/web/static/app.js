// ========== 配置 ==========
const API_BASE_URL = '/api/v1';
const SESSION_ID = 'web_user_' + Date.now();  // 简单的会话ID生成

// ========== DOM 元素 ==========
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// ========== 工具函数 ==========
function formatTime(date) {
    return new Date(date).toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ========== 消息渲染 ==========
function addMessage(role, content, timestamp = new Date()) {
    // 移除欢迎消息
    const welcomeMsg = chatContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(content)}</div>
        <div class="message-time">${formatTime(timestamp)}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message assistant';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatContainer.appendChild(indicator);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function createStreamingMessage() {
    const welcomeMsg = chatContainer.querySelector(".welcome-message");
    if(welcomeMsg){
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content"></div>
        <div class="message-time">${formatTime(new Date())}</div>
    `;

    chatContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageDiv.querySelector('.message-content')
}

// ========== API 调用 ==========
// 非流式调用
async function sendMessage(content) {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations/${SESSION_ID}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) {
            throw new Error('API 请求失败');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('发送消息失败:', error);
        throw error;
    }
}
// 流式调用
async function sendMessageStream(content,onChunk) {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations/${SESSION_ID}/messages/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) {
            throw new Error('API 请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            
            if(done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n');
            
            for(const line of lines) {
                if(line.startsWith('data: ')){
                    const data = line.slice(6);
                    if (data === '[DONE]'){
                        return;
                    }
                    onChunk(data)
                }
            }

        }
    } catch (error) {
        console.error('发送消息失败:', error);
        throw error;
    }
}

// ========== 事件处理 ==========
async function handleSend() {
    const content = messageInput.value.trim();
    
    if (!content) return;

    // 禁用输入
    messageInput.value = '';
    messageInput.disabled = true;
    messageInput.style.height = 'auto';
    sendButton.disabled = true;

    // 显示用户消息
    addMessage('user', content);

    // 显示加载动画
    showTypingIndicator();

    try {
        // // 调用 API
        // const response = await sendMessage(content);
        
        // 移除加载动画
        removeTypingIndicator();
        const contentElement = createStreamingMessage();
        let fullContent = '';

        await sendMessageStream(content, (chunk) => {
            fullContent += chunk;
            contentElement.innerHTML = escapeHtml(fullContent);
            scrollToBottom();
        });
        
        // // 显示 AI 回复
        // addMessage('assistant', response.content, response.timestamp);
    } catch (error) {
        removeTypingIndicator();
        addMessage('assistant', '抱歉，发生了错误，请稍后重试。');
    } finally {
        // 恢复输入
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// ========== 事件监听 ==========
sendButton.addEventListener('click', handleSend);

messageInput.addEventListener('keydown', (e) => {
    // Enter 发送，Shift+Enter 换行
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

// 自动调整输入框高度
messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
});

// 页面加载完成后聚焦输入框
window.addEventListener('load', () => {
    messageInput.focus();
});