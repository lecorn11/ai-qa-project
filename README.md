# AI 智能问答系统
基于 LangChain 和 FastAPI 构建的智能对话应用，支持流式响应，采用 Clean Architecture 架构设计

## ✨ 功能特性
- **智能对话**：接入通义千问大模型，支持多轮对话
- **流式响应**：AI 回复逐字显示，类似打字机体验
- **Clean Architecture**：清晰的分层架构，易于扩展和维护
- **可拔插设计**：轻松切换不同的 LLM 提供商
- **对话记忆**：支持上下文记忆，理解连续对话

## 🛠️ 技术栈
| 层级 | 技术 |
|-----|------|
|**后端框架**| FastAPI |
|**AI 框架**| LangChain |
|**LLM**|  通义千问（Qwen） |
|**前端**|HTML + CSS + JavaScript|
|**配置管理**| Pydantic Settings |

## 📁 项目结构
```
ai-qa-project/
├── src/ai_qa/
│   ├── domain/                 # 领域层：实体和接口定义
│   │   ├── entities.py         # Message, Conversation 实体
│   │   └── ports.py            # LLMPort, MemoryPort 接口
│   │
│   ├── application/            # 应用层：业务逻辑编排
│   │   └── chat_service.py     # 聊天服务
│   │
│   ├── infrastructure/         # 基础设施层：外部服务实现
│   │   ├── llm/
│   │   │   └── qwen_adapter.py # 通义千问适配器
│   │   └── memory/
│   │       └── in_memory.py    # 内存存储
│   │
│   ├── interfaces/             # 接口层：对外暴露
│   │   ├── api/                # FastAPI 路由
│   │   ├── cli/                # 命令行入口
│   │   └── web/                # 前端静态文件
│   │
│   └── config/                 # 配置管理
│       └── settings.py
│
├── .env                        # 环境变量（不提交到 Git）
├── .env.example                # 环境变量示例
├── pyproject.toml              # 项目配置
├── requirements.txt            # 依赖列表
└── README.md
```

## 🚀 快速开始
### 1. 克隆项目
```bash
git clone https://github.com/your-username/ai-qa-project.git
cd ai-qa-project
```

### 2. 创建虚拟环境
```bash
conda create -n ai-qa python=3.12 -y
conda activate ai-qa
```

### 3. 安装依赖
```bash
pip install -e .
```

### 4. 配置环境变量
复制环境变量示例文件并填入你的 API Key：
```bash
cp .env.example .env
```

编辑 '.env' 文件：
```env
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-turbo
```

### 5. 启动服务
```bash
python run_api.py
```

### 6. 访问应用

- Web 界面：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 📖 API 文档
| 方法 | 端点 | 描述 |
|-----|------|------|
| POST | `/api/v1/conversations/{session_id}/messages` | 发送消息（非流式） |
| POST | `/api/v1/conversations/{session_id}/messages/stream` | 发送消息（流式） |
| GET | `/api/v1/conversations/{session_id}/messages` | 获取对话历史 |
| GET | `/api/v1/conversations` | 获取会话列表 |
| DELETE | `/api/v1/conversations/{session_id}` | 删除会话 |

详细文档请访问 `/docs` 查看 Swagger UI。

## 🗺️ 未来计划
- [] RAG 文档问答：上传文档，基于文档内容回答
- [] 多模型支持：添加 OpenAI、Claude 等模型
- [] 持久化存储：支持 Redis/数据库存储对话
- [] 用户系统：多用户支持
- [] Docker 部署：容器化部署方案

## 📄 许可证

MIT License