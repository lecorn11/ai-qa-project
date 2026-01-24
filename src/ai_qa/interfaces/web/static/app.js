const API_BASE = '/api/v1';

// ============ 状态管理 ============
let token = localStorage.getItem('token');
let currentUser = null;
let currentConversationId = null;
let currentKnowledgeBaseId = null;
let knowledgeBases = [];
let conversations = [];
let mcpServers = [];
let mcpSettings = {
    enabled: false,
    selected_servers: []
};

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
    loadMcpSettings();
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

    container.innerHTML = '';

    messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = `message ${msg.role}`;

        if (msg.role === 'assistant' && msg.reasoning_steps && msg.reasoning_steps.length > 0) {
            // Assistant 消息且有推理步骤，使用推理链渲染
            div.innerHTML = buildAgentMessageHTML(msg.reasoning_steps, msg.content);
        } else {
            // 普通消息
            div.textContent = msg.content;
        }

        container.appendChild(div);
    });

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

    const useAgent = document.getElementById('useAgent').checked;
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
        if (useAgent) {
            // Agent 模式
            await sendAgentMessage(message, typingId);
        } else {
            // 普通模式 / 知识库模式
            await sendNormalMessage(message, useKnowledge, kbId, typingId);
        }
        
        // 刷新会话列表（更新标题）
        loadConversations();
        
    } catch (error) {
        console.error('发送失败:', error);
        removeTypingIndicator(typingId);
        appendMessage('assistant', '抱歉，发生了错误，请重试。');
    }
}

async function sendNormalMessage(message, useKnowledge, kbId, typingId) {
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
}

async function sendAgentMessage(message, typingId) {
    const body = {
        content: message
    };

    // 如果启用了 MCP，自动带上选中的 servers
    if (mcpSettings.enabled && mcpSettings.selected_servers.length > 0) {
        body.mcp_servers = mcpSettings.selected_servers;
    }

    const response = await fetch(`${API_BASE}/conversations/${currentConversationId}/messages/agent/stream`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(body)
    });

    // 移除加载动画
    removeTypingIndicator(typingId);

    // 处理流式响应
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let steps = [];            // 按时间顺序记录所有步骤
    let answerContent = '';    // 最终回答
    let messageElement = null; // 消息 DOM 元素

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
            if (!line.startsWith('data: ')) continue;

            const rawData = line.slice(6).trim();
            if (!rawData) continue;

            try {
                const event = JSON.parse(rawData);

                switch (event.type) {
                    case 'thinking':
                        // 记录思考步骤
                        steps.push({ type: 'thinking', content: event.content });
                        if (!messageElement) {
                            messageElement = appendAgentMessage(steps, answerContent);
                        } else {
                            updateAgentMessage(messageElement, steps, answerContent);
                        }
                        scrollToBottom();
                        break;

                    case 'tool_start':
                        // 记录工具调用开始
                        steps.push({
                            type: 'tool_start',
                            tool: event.tool,
                            input: event.input
                        });
                        if (!messageElement) {
                            messageElement = appendAgentMessage(steps, answerContent);
                        } else {
                            updateAgentMessage(messageElement, steps, answerContent);
                        }
                        scrollToBottom();
                        break;

                    case 'tool_result':
                        // 记录工具调用结果
                        steps.push({
                            type: 'tool_result',
                            tool: event.tool,
                            output: event.output
                        });
                        if (!messageElement) {
                            messageElement = appendAgentMessage(steps, answerContent);
                        } else {
                            updateAgentMessage(messageElement, steps, answerContent);
                        }
                        scrollToBottom();
                        break;

                    case 'answer':
                        // 流式回答
                        answerContent += event.content;
                        if (!messageElement) {
                            messageElement = appendAgentMessage(steps, answerContent);
                        } else {
                            updateAgentMessage(messageElement, steps, answerContent);
                        }
                        scrollToBottom();
                        break;

                    case 'done':
                        // 完成
                        break;
                }
            } catch (e) {
                console.error('解析 Agent 事件失败:', e, rawData);
            }
        }
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

function appendAgentMessage(steps, answerContent) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = 'message assistant';

    div.innerHTML = buildAgentMessageHTML(steps, answerContent);

    container.appendChild(div);
    scrollToBottom();
    return div;
}

function updateAgentMessage(element, steps, answerContent) {
    element.innerHTML = buildAgentMessageHTML(steps, answerContent);
}

function buildAgentMessageHTML(steps, answerContent) {
    let html = '';

    // 1. 展示推理链（思考 + 工具调用按时间顺序交替）
    // 确保 steps 是数组
    if (Array.isArray(steps) && steps.length > 0) {
        let stepNumber = 0;  // 步骤计数器（只计算思考步骤）

        let stepsHtml = steps.map(step => {
            if (step.type === 'thinking') {
                stepNumber++;
                return `<div class="step-item step-thinking">` +
                    `<span class="step-number">步骤 ${stepNumber}</span>` +
                    `<span class="step-content">${escapeHtml(step.content)}</span>` +
                    `</div>`;
            } else if (step.type === 'tool_start') {
                return `<div class="step-item step-tool">` +
                    `<span class="step-label">调用工具</span>` +
                    `<span class="step-tool-name">${formatToolName(step.tool)}</span>` +
                    `<div class="step-tool-input">${escapeHtml(step.input || '{}')}</div>` +
                    `</div>`;
            } else if (step.type === 'tool_result') {
                const isError = step.output && (step.output.includes('denied') || step.output.includes('错误'));
                const resultClass = isError ? 'step-result-error' : 'step-result-success';
                const statusIcon = isError ? '✗' : '✓';
                return `<div class="step-item step-result ${resultClass}">` +
                    `<span class="step-status">${statusIcon}</span>` +
                    `<span class="step-content">${escapeHtml(step.output || '执行中...')}</span>` +
                    `</div>`;
            }
            return '';
        }).join('');

        html += `<div class="reasoning-chain">` +
            `<div class="reasoning-header" onclick="toggleReasoning(this)">` +
            `<span class="reasoning-toggle">▼</span>` +
            `<span>推理过程（${stepNumber} 步）</span>` +
            `</div>` +
            `<div class="reasoning-steps expanded">${stepsHtml}</div>` +
            `</div>`;
    }

    // 2. 展示最终回答
    if (answerContent) {
        html += `<div class="message-text">${escapeHtml(answerContent)}</div>`;
    }

    return html;
}

function toggleReasoning(header) {
    const toggle = header.querySelector('.reasoning-toggle');
    const content = header.nextElementSibling;

    toggle.classList.toggle('collapsed');
    content.classList.toggle('collapsed');
}

function formatToolName(name) {
    const nameMap = {
        'calculator': '计算器',
        'get_current_time': '获取时间',
        'search_knowledge_base': '知识库搜索'
    };
    return nameMap[name] || name;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ MCP 工具管理 ============
async function loadMcpSettings() {
    try {
        const response = await fetch(`${API_BASE}/mcp/settings`, {
            headers: authHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            // 后端返回 mcp_enabled 和 servers，转换为前端格式
            mcpSettings = {
                enabled: data.mcp_enabled,
                selected_servers: data.servers
            };
            updateMcpUI();
        }
    } catch (error) {
        console.error('加载 MCP 设置失败:', error);
    }
}

async function loadMcpServers() {
    try {
        const response = await fetch(`${API_BASE}/mcp/servers`, {
            headers: authHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            mcpServers = data.servers;
            renderMcpServers();
        }
    } catch (error) {
        console.error('加载 MCP 服务列表失败:', error);
    }
}

function updateMcpUI() {
    const enabled = mcpSettings.enabled;

    // 更新侧边栏开关
    document.getElementById('mcpEnabled').checked = enabled;

    // 更新状态文本
    const statusElement = document.getElementById('mcpStatus');
    const statusText = statusElement.querySelector('.mcp-status-text');

    if (enabled && mcpSettings.selected_servers && mcpSettings.selected_servers.length > 0) {
        statusElement.classList.add('enabled');
        statusText.textContent = `已启用 ${mcpSettings.selected_servers.length} 个服务`;
    } else if (enabled) {
        statusElement.classList.add('enabled');
        statusText.textContent = '已启用，未选择服务';
    } else {
        statusElement.classList.remove('enabled');
        statusText.textContent = '未启用';
    }
}

async function toggleMcpEnabled(event) {
    const enabled = event.target.checked;

    try {
        const response = await fetch(`${API_BASE}/mcp/settings`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                mcp_enabled: enabled,
                servers: mcpSettings.selected_servers
            })
        });

        if (response.ok) {
            const data = await response.json();
            mcpSettings = {
                enabled: data.mcp_enabled,
                selected_servers: data.servers
            };
            updateMcpUI();
        } else {
            const data = await response.json();
            alert(data.detail || '保存失败');
            event.target.checked = !enabled;
        }
    } catch (error) {
        console.error('保存 MCP 设置失败:', error);
        alert('保存失败，请重试');
        event.target.checked = !enabled;
    }
}

function showMcpSettingsModal() {
    document.getElementById('mcpSettingsModal').style.display = 'flex';
    document.getElementById('mcpEnabledModal').checked = mcpSettings.enabled;
    loadMcpServers();
}

function hideMcpSettingsModal() {
    document.getElementById('mcpSettingsModal').style.display = 'none';
}

async function updateMcpEnabledInModal() {
    const enabled = document.getElementById('mcpEnabledModal').checked;

    try {
        const response = await fetch(`${API_BASE}/mcp/settings`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                mcp_enabled: enabled,
                servers: mcpSettings.selected_servers
            })
        });

        if (response.ok) {
            const data = await response.json();
            mcpSettings = {
                enabled: data.mcp_enabled,
                selected_servers: data.servers
            };
            updateMcpUI();
        } else {
            const data = await response.json();
            alert(data.detail || '保存失败');
            document.getElementById('mcpEnabledModal').checked = !enabled;
        }
    } catch (error) {
        console.error('保存 MCP 设置失败:', error);
        alert('保存失败，请重试');
        document.getElementById('mcpEnabledModal').checked = !enabled;
    }
}

function renderMcpServers() {
    const container = document.getElementById('mcpServersList');

    if (mcpServers.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无可用的 MCP 服务</div>';
        return;
    }

    container.innerHTML = mcpServers.map(server => {
        const isSelected = mcpSettings.selected_servers.includes(server.name);
        return `
            <div class="mcp-server-item">
                <div class="mcp-server-header">
                    <div class="mcp-server-name">
                        <input type="checkbox"
                               class="mcp-server-checkbox"
                               ${isSelected ? 'checked' : ''}
                               onchange="toggleMcpServer('${server.name}', this.checked)">
                        <span>${server.name}</span>
                    </div>
                </div>
                <div class="mcp-server-desc">${server.description || '无描述'}</div>
            </div>
        `;
    }).join('');
}

async function toggleMcpServer(serverName, isSelected) {
    let newSelectedServers = [...mcpSettings.selected_servers];

    if (isSelected) {
        if (!newSelectedServers.includes(serverName)) {
            newSelectedServers.push(serverName);
        }
    } else {
        newSelectedServers = newSelectedServers.filter(s => s !== serverName);
    }

    try {
        const response = await fetch(`${API_BASE}/mcp/settings`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                mcp_enabled: mcpSettings.enabled,
                servers: newSelectedServers
            })
        });

        if (response.ok) {
            const data = await response.json();
            mcpSettings = {
                enabled: data.mcp_enabled,
                selected_servers: data.servers
            };
            updateMcpUI();
        } else {
            const data = await response.json();
            alert(data.detail || '保存失败');
            renderMcpServers();
        }
    } catch (error) {
        console.error('保存 MCP 服务选择失败:', error);
        alert('保存失败，请重试');
        renderMcpServers();
    }
}