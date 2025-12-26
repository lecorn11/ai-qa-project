const API_BASE = '/api/v1';

// ============ 状态管理 ============
let token = localStorage.getItem('token');
let currentUser = null;
let currentConversationId = null;
let currentKnowledgeBaseId = null;
let knowledgeBases = [];
let conversations = [];

// ============ 初始化 ============
document.addEventListener('DOMContentLoaded', () => {
    // 检查登录状态
    if (token) {
        checkAuth();
    }
    
    // 监听文件选择
    document.getElementById('fileInput').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('uploadFileBtn').style.display = 'inline-block';
        } else {
            document.getElementById('fileName').textContent = '';
            document.getElementById('uploadFileBtn').style.display = 'none';
        }
    });
    
    // 监听知识库开关
    document.getElementById('useKnowledge').addEventListener('change', (e) => {
        document.getElementById('kbSelect').disabled = !e.target.checked;
    });
    
    // 监听知识库选择
    document.getElementById('kbSelect').addEventListener('change', (e) => {
        currentKnowledgeBaseId = e.target.value ? e.target.value : null;
    });
});

// ============ 认证相关 ============
function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegister() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            checkAuth();
        } else {
            alert(data.detail || '登录失败');
        }
    } catch (error) {
        console.error('登录失败:', error);
        alert('登录失败，请重试');
    }
}

async function register() {
    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email: email || null })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('注册成功，请登录');
            showLogin();
            document.getElementById('loginUsername').value = username;
        } else {
            alert(data.detail || '注册失败');
        }
    } catch (error) {
        console.error('注册失败:', error);
        alert('注册失败，请重试');
    }
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            showApp();
        } else {
            logout();
        }
    } catch (error) {
        console.error('认证检查失败:', error);
        logout();
    }
}

function logout() {
    token = null;
    currentUser = null;
    currentConversationId = null;
    localStorage.removeItem('token');
    document.getElementById('authContainer').style.display = 'flex';
    document.getElementById('appContainer').style.display = 'none';
}

function showApp() {
    document.getElementById('authContainer').style.display = 'none';
    document.getElementById('appContainer').style.display = 'flex';
    document.getElementById('currentUser').textContent = currentUser.username;
    
    // 加载数据
    loadKnowledgeBases();
    loadConversations();
}

// ============ API 请求工具 ============
function authHeaders() {
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// ============ 知识库管理 ============
async function loadKnowledgeBases() {
    try {
        const response = await fetch(`${API_BASE}/knowledge-bases`, {
            headers: authHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            knowledgeBases = data.knowledge_bases;
            renderKnowledgeBases();
            updateKbSelect();
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
    }
}

function renderKnowledgeBases() {
    const container = document.getElementById('kbList');
    
    if (knowledgeBases.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无知识库</div>';
        return;
    }
    
    container.innerHTML = knowledgeBases.map(kb => `
        <div class="list-item ${currentKnowledgeBaseId === kb.id ? 'selected' : ''}"
             onclick="selectKnowledgeBase('${kb.id}')">
            <div class="list-item-title">📚 ${kb.name}</div>
            <div class="list-item-sub">${kb.document_count} 文档 · ${kb.chunk_count} 块</div>
        </div>
    `).join('');
}

function updateKbSelect() {
    const select = document.getElementById('kbSelect');
    select.innerHTML = '<option value="">选择知识库</option>' +
        knowledgeBases.map(kb => `<option value="${kb.id}">${kb.name}</option>`).join('');
    
    // 如果有知识库，启用开关
    const checkbox = document.getElementById('useKnowledge');
    checkbox.disabled = knowledgeBases.length === 0;
}

function selectKnowledgeBase(kbId) {
    currentKnowledgeBaseId = kbId;
    renderKnowledgeBases();
    showKbDetailModal(kbId);
}

function showCreateKbModal() {
    document.getElementById('createKbModal').style.display = 'flex';
    document.getElementById('newKbName').value = '';
    document.getElementById('newKbDesc').value = '';
}

function hideCreateKbModal() {
    document.getElementById('createKbModal').style.display = 'none';
}

async function createKnowledgeBase() {
    const name = document.getElementById('newKbName').value.trim();
    const description = document.getElementById('newKbDesc').value.trim();
    
    if (!name) {
        alert('请输入知识库名称');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/knowledge-bases`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ name, description: description || null })
        });
        
        if (response.ok) {
            hideCreateKbModal();
            loadKnowledgeBases();
        } else {
            const data = await response.json();
            alert(data.detail || '创建失败');
        }
    } catch (error) {
        console.error('创建知识库失败:', error);
        alert('创建失败，请重试');
    }
}

async function showKbDetailModal(kbId) {
    const kb = knowledgeBases.find(k => k.id === kbId);
    if (!kb) return;
    
    document.getElementById('kbDetailTitle').textContent = kb.name;
    document.getElementById('kbDocCount').textContent = kb.document_count;
    document.getElementById('kbChunkCount').textContent = kb.chunk_count;
    document.getElementById('kbDetailModal').style.display = 'flex';
    
    // 清空上传表单
    document.getElementById('fileInput').value = '';
    document.getElementById('fileName').textContent = '';
    document.getElementById('uploadFileBtn').style.display = 'none';
    document.getElementById('docContent').value = '';
    document.getElementById('docTitle').value = '';
}

function hideKbDetailModal() {
    document.getElementById('kbDetailModal').style.display = 'none';
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file || !currentKnowledgeBaseId) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/knowledge-bases/${currentKnowledgeBaseId}/documents/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
            loadKnowledgeBases();
            showKbDetailModal(currentKnowledgeBaseId);
        } else {
            alert(data.detail || '上传失败');
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败，请重试');
    }
}

async function uploadText() {
    const content = document.getElementById('docContent').value.trim();
    const title = document.getElementById('docTitle').value.trim();
    
    if (!content || !currentKnowledgeBaseId) {
        alert('请输入文档内容');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/knowledge-bases/${currentKnowledgeBaseId}/documents/text`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ content, title: title || null })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
            loadKnowledgeBases();
            showKbDetailModal(currentKnowledgeBaseId);
        } else {
            alert(data.detail || '添加失败');
        }
    } catch (error) {
        console.error('添加失败:', error);
        alert('添加失败，请重试');
    }
}

async function deleteKnowledgeBase() {
    if (!currentKnowledgeBaseId) return;
    if (!confirm('确定要删除这个知识库吗？此操作不可恢复。')) return;
    
    try {
        const response = await fetch(`${API_BASE}/knowledge-bases/${currentKnowledgeBaseId}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        
        if (response.ok) {
            hideKbDetailModal();
            currentKnowledgeBaseId = null;
            loadKnowledgeBases();
        } else {
            const data = await response.json();
            alert(data.detail || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}

// ============ 会话管理 ============
async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            headers: authHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            conversations = data.conversations;
            renderConversations();
        }
    } catch (error) {
        console.error('加载会话失败:', error);
    }
}

function renderConversations() {
    const container = document.getElementById('conversationList');
    
    if (conversations.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无会话</div>';
        return;
    }
    
    container.innerHTML = conversations.map(conv => `
        <div class="list-item ${String(currentConversationId) === String(conv.session_id) ? 'selected' : ''}"
             onclick="selectConversation('${conv.session_id}')">
            <div class="list-item-title">${conv.title || '新对话'}</div>
            <div class="list-item-sub">${formatTime(conv.updated_at)}</div>
        </div>
    `).join('');
}

function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    
    // 今天
    if (diff < 86400000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    // 昨天
    if (diff < 172800000) {
        return '昨天';
    }
    // 其他
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

async function createNewConversation() {

    currentConversationId = null;  // 清空当前会话 ID
    clearChat();                   // 清空聊天区域
    renderConversations();         // 更新列表选中状态

    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            method: 'POST',
            headers: authHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            currentConversationId = data.session_id;
            loadConversations();
            clearChat();
            return data.session_id;
        }
    } catch (error) {
        console.error('创建会话失败:', error);
        return null;
    }
}

async function doCreateConversation() {
    try {
        const response = await fetch(`${API_BASE}/conversations`, {
            method: 'POST',
            headers: authHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            currentConversationId = data.session_id;
            return data.session_id;
        }
    } catch (error) {
        console.error('创建会话失败:', error);
        return null;
    }
}


async function selectConversation(sessionId) {
    currentConversationId = String(sessionId);
    renderConversations();
    await loadMessages(String(sessionId));
}

async function loadMessages(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/conversations/${sessionId}/messages`, {
            headers: authHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderMessages(data.messages);
        }
    } catch (error) {
        console.error('加载消息失败:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('chatContainer');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <p>👋 你好！我是 AI 助手，可以回答你的问题。</p>
                <p>💡 选择知识库后开启「知识库模式」，我会基于文档内容回答。</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = messages.map(msg => `
        <div class="message ${msg.role}">${msg.content}</div>
    `).join('');
    
    scrollToBottom();
}

function clearChat() {
    document.getElementById('chatContainer').innerHTML = `
        <div class="welcome-message">
            <p>👋 你好！我是 AI 助手，可以回答你的问题。</p>
            <p>💡 选择知识库后开启「知识库模式」，我会基于文档内容回答。</p>
        </div>
    `;
}

// ============ 聊天功能 ============
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 确保有会话
    if (!currentConversationId) {
        const sessionId = await doCreateConversation();
        if (!sessionId) {
            alert('创建会话失败，请重试');
            return;
        }
    }
    
    const useKnowledge = document.getElementById('useKnowledge').checked;
    const kbId = document.getElementById('kbSelect').value;
    
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
        // 构建请求体
        const body = { 
            content: message, 
            use_knowledge: useKnowledge
        };
        if (useKnowledge && kbId) {
            body.knowledge_base_id = kbId;
        }
        
        const response = await fetch(`${API_BASE}/conversations/${currentConversationId}/messages/stream`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(body)
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
            const lines = chunk.split('\n\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const rawData = line.slice(6);
                    if (rawData === '[DONE]') continue;
                    
                    try {
                        const data = JSON.parse(rawData);
                        assistantMessage += data;
                    } catch (e) {
                        assistantMessage += rawData;
                    }
                    
                    if (!messageElement) {
                        messageElement = appendMessage('assistant', assistantMessage);
                    } else {
                        messageElement.textContent = assistantMessage;
                    }
                    
                    scrollToBottom();
                }
            }
        }
        
        // 刷新会话列表（更新标题）
        loadConversations();
        
    } catch (error) {
        console.error('发送失败:', error);
        removeTypingIndicator(typingId);
        appendMessage('assistant', '抱歉，发生了错误，请重试。');
    }
}

function appendMessage(role, content) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = content;
    container.appendChild(div);
    scrollToBottom();
    return div;
}

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

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    const container = document.getElementById('chatContainer');
    container.scrollTop = container.scrollHeight;
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// ============ UI 辅助 ============
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const iconId = sectionId === 'kbSection' ? 'kbToggleIcon' : 'convToggleIcon';
    const icon = document.getElementById(iconId);
    
    section.classList.toggle('collapsed');
    icon.classList.toggle('collapsed');
}
