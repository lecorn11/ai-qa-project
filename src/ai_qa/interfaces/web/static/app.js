const API_BASE = '/api/v1';
let sessionId = 'session_' + Date.now();

// 页面加载时获取知识库状态
document.addEventListener('DOMContentLoaded', () => {
    updateKnowledgeStatus();
    
    // 监听开关变化
    document.getElementById('useKnowledge').addEventListener('change', (e) => {
        updateToggleButton(e.target.checked);
    });
});

// 切换知识库面板显示
function toggleKnowledgePanel() {
    const panel = document.getElementById('knowledgePanel');
    const isVisible = panel.style.display !== 'none';
    panel.style.display = isVisible ? 'none' : 'block';
    
    if (!isVisible) {
        updateKnowledgeStatus();
    }
}

// 更新知识库状态
async function updateKnowledgeStatus() {
    try {
        const response = await fetch(`${API_BASE}/knowledge/status`);
        const data = await response.json();
        
        document.getElementById('kbStatus').textContent = data.is_ready ? '✅ 就绪' : '⚪ 未初始化';
        document.getElementById('kbChunkCount').textContent = data.document_count;
        
        // 如果知识库有内容，自动开启开关
        if (data.is_ready) {
            document.getElementById('useKnowledge').checked = true;
            updateToggleButton(true);
        }
    } catch (error) {
        console.error('获取知识库状态失败:', error);
    }
}

// 更新切换按钮样式
function updateToggleButton(active) {
    const btn = document.getElementById('kbToggleBtn');
    if (active) {
        btn.classList.add('active');
    } else {
        btn.classList.remove('active');
    }
}

// 上传文档
async function uploadDocument() {
    const content = document.getElementById('docContent').value.trim();
    const title = document.getElementById('docTitle').value.trim();
    
    if (!content) {
        alert('请输入文档内容');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/knowledge/documents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, title: title || null })
        });
        
        const data = await response.json();
        alert(data.message);
        
        // 清空输入
        document.getElementById('docContent').value = '';
        document.getElementById('docTitle').value = '';
        
        // 刷新状态
        updateKnowledgeStatus();
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请重试');
    }
}

// 清空知识库
async function clearKnowledge() {
    if (!confirm('确定要清空知识库吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE}/knowledge/documents`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        alert(data.message);
        
        // 刷新状态并关闭开关
        document.getElementById('useKnowledge').checked = false;
        updateToggleButton(false);
        updateKnowledgeStatus();
    } catch (error) {
        console.error('清空失败:', error);
        alert('清空失败，请重试');
    }
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const useKnowledge = document.getElementById('useKnowledge').checked;
    
    // 清空输入
    input.value = '';
    
    // 移除欢迎消息
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    // 显示用户消息
    appendMessage('user', message);
    
    // 显示加载动画
    const typingId = showTypingIndicator();
    
    try {
        const response = await fetch(`${API_BASE}/conversations/${sessionId}/messages/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: message, use_knowledge: useKnowledge })
        });
        
        // 移除加载动画
        removeTypingIndicator(typingId);
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        let messageElement = null;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;
                    
                    assistantMessage += data;
                    
                    if (!messageElement) {
                        messageElement = appendMessage('assistant', assistantMessage);
                    } else {
                        messageElement.textContent = assistantMessage;
                    }
                    
                    scrollToBottom();
                }
            }
        }
    } catch (error) {
        console.error('发送失败:', error);
        removeTypingIndicator(typingId);
        appendMessage('assistant', '抱歉，发生了错误，请重试。');
    }
}

// 添加消息到聊天区域
function appendMessage(role, content) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = content;
    container.appendChild(div);
    scrollToBottom();
    return div;
}

// 显示加载动画
function showTypingIndicator() {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing_' + Date.now();
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    scrollToBottom();
    return div.id;
}

// 移除加载动画
function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
}

// 滚动到底部
function scrollToBottom() {
    const container = document.getElementById('chatContainer');
    container.scrollTop = container.scrollHeight;
}

// 回车发送
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}