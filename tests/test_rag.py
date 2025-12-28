from ai_qa.application import knowledge_service
from ai_qa.config.settings import settings
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.embedding.dashscope_embedding import DashScopeEmbeddingAdapter
from ai_qa.infrastructure.vectorstore.faiss_store import FaissVectorStore
from ai_qa.application.knowledge_service import KnowledgeService

# 1. 创建基础设施
# LLM服务
llm = QwenAdapter(
    api_key=settings.llm_api_key.get_secret_value(),
    base_url=settings.llm_base_url,
    model_name=settings.llm_model
)
# Embedding 服务
embedding = DashScopeEmbeddingAdapter(
    api_key=settings.llm_api_key.get_secret_value(),
    model_name=settings.embedding_model_name
)
# 向量存储库
vector_store = FaissVectorStore(
    embedding=embedding
)

# 2. 创建知识库服务
knowledge_service = KnowledgeService(vector_store,llm,)

# 3. 创建知识库并添加内容
knowledge_service.create_knowledge_base("测试知识库")

# 准备测试文档
test_documents = """
# Python 编程语言

Python 是一种解释型、面向对象、动态数据类型的高级程序设计语言。
Python 由 Guido van Rossum 于 1989 年底发明，第一个公开发行版发行于 1991 年。
Python 的设计哲学强调代码的可读性和简洁的语法。

## Python 的特点

1. 简单易学：Python 有极其简单的语法，适合初学者入门。
2. 免费开源：Python 是 FLOSS（自由/开放源码软件）之一。
3. 可移植性：Python 可以运行在多种操作系统上，如 Windows、Linux、macOS 等。
4. 丰富的库：Python 拥有大量的第三方库，可以快速实现各种功能。

## Python 的应用领域

Python 广泛应用于以下领域：
- Web 开发：Django、Flask、FastAPI
- 数据科学：NumPy、Pandas、Matplotlib
- 人工智能：TensorFlow、PyTorch、LangChain
- 自动化运维：Ansible、SaltStack
- 爬虫开发：Scrapy、BeautifulSoup

# FastAPI 框架

FastAPI 是一个用于构建 API 的现代、快速（高性能）的 Web 框架。
它基于 Python 3.6+ 的类型提示，使用 Starlette 和 Pydantic。

## FastAPI 的特点

1. 高性能：与 NodeJS 和 Go 相当的性能。
2. 快速开发：自动生成 API 文档。
3. 类型检查：利用 Python 类型提示进行数据验证。
4. 异步支持：原生支持 async/await。

# LangChain 框架

LangChain 是一个用于开发由语言模型驱动的应用程序的框架。
它提供了一套工具，用于将大型语言模型与其他数据源和计算资源连接起来。

## LangChain 的核心概念

1. Models：支持多种 LLM，如 OpenAI、Anthropic 等。
2. Prompts：提供 Prompt 模板和管理功能。
3. Chains：将多个组件串联起来完成复杂任务。
4. Memory：为对话提供上下文记忆。
5. Agents：让 LLM 自主决定使用哪些工具。
"""
chunk_count = knowledge_service.add_text(test_documents)
print(f"已添加 {chunk_count} 个文档块到知识库")

# 4. 测试 RAG 回答
print("\n" + "=" * 50)
print("开始 RAG 问答测试")
print("=" * 50)

questions = [
    "Python 是谁发明的？",
    "FastAPI 有什么特点？",
    "LangChain 的核心概念有哪些？",
    "Java 的特点是什么？"  # 故意问一个知识库中没有的问题
]

for q in questions:
    print(f"\n 问题：{q}")
    answer = knowledge_service.query(q)
    print(f"回答：{answer}")
    print("-" * 40)

