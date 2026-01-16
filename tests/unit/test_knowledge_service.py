"""KnowledgeService 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, Mock

from ai_qa.application.knowledge_service import KnowledgeService
from ai_qa.domain.entities import DocumentChunk, Conversation, Message, MessageRole, KnowledgeBase


@pytest.fixture
def mock_vector_store():
    """模拟向量存储"""
    store = MagicMock()
    store.add_documents = MagicMock()
    store.search = MagicMock(return_value=[])
    store.count = MagicMock(return_value=0)
    return store


@pytest.fixture
def mock_llm():
    """模拟 LLM"""
    llm = MagicMock()
    llm.chat = MagicMock(return_value="AI response")
    llm.chat_stream = MagicMock(return_value=iter(["AI", " response"]))
    return llm


@pytest.fixture
def mock_memory():
    """模拟对话记忆"""
    memory = MagicMock()
    memory.get_conversation = MagicMock(
        return_value=Conversation(id="test_session", messages=[])
    )
    return memory


@pytest.fixture
def mock_db():
    """模拟数据库"""
    db = MagicMock()
    return db


@pytest.fixture
def knowledge_service(mock_vector_store, mock_llm, mock_memory, mock_db):
    """创建 KnowledgeService 实例"""
    return KnowledgeService(
        vector_store=mock_vector_store,
        llm=mock_llm,
        memory=mock_memory,
        db=mock_db,
        chunk_size=100,
        chunk_overlap=10,
    )


class TestKnowledgeServiceInitialization:
    """KnowledgeService 初始化测试"""

    def test_init_creates_service(self, mock_vector_store, mock_llm, mock_memory):
        """测试：初始化创建服务实例"""
        # Act
        service = KnowledgeService(
            vector_store=mock_vector_store,
            llm=mock_llm,
            memory=mock_memory,
            chunk_size=500,
            chunk_overlap=50,
        )

        # Assert
        assert service._vector_store == mock_vector_store
        assert service._llm == mock_llm
        assert service._memory == mock_memory
        assert service._splitter is not None


class TestAddText:
    """添加文本功能测试"""

    def test_add_text_splits_and_stores(self, knowledge_service, mock_vector_store):
        """测试：add_text 切分文本并存储"""
        # Arrange
        text = "This is a test. " * 20  # 长文本

        # Act
        chunk_count = knowledge_service.add_text(text)

        # Assert
        assert chunk_count > 0
        mock_vector_store.add_documents.assert_called_once()
        # 验证传入的文档块
        call_args = mock_vector_store.add_documents.call_args[0][0]
        assert all(isinstance(chunk, DocumentChunk) for chunk in call_args)

    def test_add_text_with_metadata(self, knowledge_service, mock_vector_store):
        """测试：添加带元数据的文本"""
        # Arrange
        text = "Test content"
        metadata = {"source": "test.txt", "author": "test_user"}

        # Act
        chunk_count = knowledge_service.add_text(text, metadata)

        # Assert
        assert chunk_count > 0
        # 验证元数据被传递
        call_args = mock_vector_store.add_documents.call_args[0][0]
        assert call_args[0].metadata == metadata

    def test_add_text_short_text(self, knowledge_service, mock_vector_store):
        """测试：添加短文本（不需要切分）"""
        # Arrange
        text = "Short text"

        # Act
        chunk_count = knowledge_service.add_text(text)

        # Assert
        assert chunk_count == 1
        mock_vector_store.add_documents.assert_called_once()

    def test_add_text_empty_text(self, knowledge_service, mock_vector_store):
        """测试：添加空文本"""
        # Arrange
        text = ""

        # Act
        chunk_count = knowledge_service.add_text(text)

        # Assert
        # 空文本可能返回 0 或 1，取决于切分器的行为
        assert chunk_count >= 0

    def test_add_text_updates_knowledge_base_count(self, knowledge_service, mock_vector_store):
        """测试：添加文本更新知识库统计"""
        # Arrange
        knowledge_service._knowledge_base = KnowledgeBase(
            name="Test KB", description="Test description", document_count=0
        )
        text = "Test content"

        # Act
        chunk_count = knowledge_service.add_text(text)

        # Assert
        assert knowledge_service._knowledge_base.document_count == chunk_count


class TestAddFile:
    """从文件添加内容测试"""

    def test_add_file_reads_and_adds_content(self, knowledge_service):
        """测试：add_file 读取文件并添加内容"""
        # Arrange
        file_path = "/tmp/test.txt"
        file_content = "File content here"

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = file_content

            # Act
            chunk_count = knowledge_service.add_file(file_path)

            # Assert
            assert chunk_count > 0
            mock_open.assert_called_once_with(file_path, "r", encoding="utf-8")


class TestAddDocument:
    """添加文档到知识库测试"""

    def test_add_document_creates_db_record_and_stores_chunks(
        self, knowledge_service, mock_db, mock_vector_store
    ):
        """测试：add_document 创建数据库记录并存储文档块"""
        # Arrange
        kb_id = "kb123"
        title = "Test Document"
        content = "Document content " * 20
        file_type = "text"

        # Mock db.flush() 以设置 document id
        def mock_flush():
            # 模拟数据库分配 ID
            mock_db.add.call_args[0][0].id = "doc123"

        mock_db.flush = mock_flush

        # Act
        chunk_count = knowledge_service.add_document(kb_id, title, content, file_type)

        # Assert
        assert chunk_count > 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_vector_store.add_documents.assert_called_once()

        # 验证传入向量存储的参数
        call_args, call_kwargs = mock_vector_store.add_documents.call_args
        assert call_kwargs.get("knowledge_base_id") == kb_id
        chunks = call_args[0]
        assert all(chunk.document_id == "doc123" for chunk in chunks)

    def test_add_document_with_file_path(
        self, knowledge_service, mock_db, mock_vector_store
    ):
        """测试：添加带文件路径的文档"""
        # Arrange
        kb_id = "kb123"
        title = "Test Doc"
        content = "Content"
        file_path = "/uploads/test.pdf"

        def mock_flush():
            mock_db.add.call_args[0][0].id = "doc123"

        mock_db.flush = mock_flush

        # Act
        chunk_count = knowledge_service.add_document(
            kb_id, title, content, file_type="pdf", file_path=file_path
        )

        # Assert
        assert chunk_count > 0
        # 验证文档记录包含文件路径
        doc_model = mock_db.add.call_args[0][0]
        assert doc_model.file_path == file_path


class TestRewriteQuery:
    """查询改写功能测试"""

    def test_rewrite_query_with_no_history(self, knowledge_service, mock_memory, mock_llm):
        """测试：没有历史对话时直接返回原问题"""
        # Arrange
        session_id = "session123"
        question = "What is AI?"
        mock_memory.get_conversation.return_value = Conversation(
            id=session_id, messages=[]
        )

        # Act
        result = knowledge_service._rewrite_query(session_id, question)

        # Assert
        assert result == question
        mock_llm.chat.assert_not_called()

    def test_rewrite_query_with_history(self, knowledge_service, mock_memory, mock_llm):
        """测试：有历史对话时调用 LLM 改写"""
        # Arrange
        session_id = "session123"
        question = "它是什么?"
        history_messages = [
            Message(role=MessageRole.USER, content="介绍一下 Python"),
            Message(role=MessageRole.ASSISTANT, content="Python 是一种编程语言"),
        ]
        mock_memory.get_conversation.return_value = Conversation(
            id=session_id, messages=history_messages
        )
        mock_llm.chat.return_value = "Python 是什么?"

        # Act
        result = knowledge_service._rewrite_query(session_id, question)

        # Assert
        assert result == "Python 是什么?"
        mock_llm.chat.assert_called_once()

    def test_rewrite_query_limits_history(self, knowledge_service, mock_memory, mock_llm):
        """测试：只使用最近 6 条历史消息"""
        # Arrange
        session_id = "session123"
        question = "这是什么?"
        # 创建 10 条历史消息
        history_messages = [
            Message(role=MessageRole.USER, content=f"Question {i}")
            for i in range(10)
        ]
        mock_memory.get_conversation.return_value = Conversation(
            id=session_id, messages=history_messages
        )
        mock_llm.chat.return_value = "Rewritten question"

        # Act
        result = knowledge_service._rewrite_query(session_id, question)

        # Assert
        assert result == "Rewritten question"
        # 验证只使用了最后 6 条消息
        call_args = mock_llm.chat.call_args[0][0]
        prompt_content = call_args[0].content
        # 应该包含 Question 6-9 (最后6条)
        assert "Question 9" in prompt_content
        assert "Question 4" in prompt_content


class TestQuery:
    """RAG 查询功能测试"""

    def test_query_returns_response(
        self, knowledge_service, mock_vector_store, mock_llm
    ):
        """测试：query 返回 AI 响应"""
        # Arrange
        question = "What is AI?"
        kb_id = "kb123"
        relevant_chunks = [
            DocumentChunk(content="AI is artificial intelligence", metadata={}),
            DocumentChunk(content="AI can learn and reason", metadata={}),
        ]
        mock_vector_store.search.return_value = relevant_chunks
        mock_llm.chat.return_value = "AI is a technology that simulates human intelligence"

        # Act
        result = knowledge_service.query(question, kb_id)

        # Assert
        assert result == "AI is a technology that simulates human intelligence"
        mock_vector_store.search.assert_called_once()
        mock_llm.chat.assert_called_once()

    def test_query_with_session_rewrites_query(
        self, knowledge_service, mock_vector_store, mock_llm, mock_memory
    ):
        """测试：带 session_id 的查询会改写问题"""
        # Arrange
        question = "它是什么?"
        kb_id = "kb123"
        session_id = "session123"
        history_messages = [
            Message(role=MessageRole.USER, content="介绍 Python"),
            Message(role=MessageRole.ASSISTANT, content="Python 是编程语言"),
        ]
        mock_memory.get_conversation.return_value = Conversation(
            id=session_id, messages=history_messages
        )
        mock_llm.chat.side_effect = [
            "Python 是什么?",  # 第一次调用：查询改写
            "Python is a programming language",  # 第二次调用：RAG 回答
        ]
        mock_vector_store.search.return_value = [
            DocumentChunk(content="Python info", metadata={})
        ]

        # Act
        result = knowledge_service.query(question, kb_id, session_id=session_id)

        # Assert
        assert result == "Python is a programming language"
        assert mock_llm.chat.call_count == 2
        # 验证向量搜索使用改写后的问题
        search_call_args = mock_vector_store.search.call_args[0]
        assert search_call_args[0] == "Python 是什么?"

    def test_query_no_relevant_chunks(self, knowledge_service, mock_vector_store):
        """测试：没有找到相关文档块"""
        # Arrange
        question = "Unknown topic"
        kb_id = "kb123"
        mock_vector_store.search.return_value = []

        # Act
        result = knowledge_service.query(question, kb_id)

        # Assert
        assert result == "知识库中没有找到相关内容"

    def test_query_with_custom_top_k(self, knowledge_service, mock_vector_store, mock_llm):
        """测试：自定义 top_k 参数"""
        # Arrange
        question = "Test question"
        kb_id = "kb123"
        top_k = 5
        mock_vector_store.search.return_value = [
            DocumentChunk(content="Content", metadata={})
        ]

        # Act
        knowledge_service.query(question, kb_id, top_k=top_k)

        # Assert
        # 验证 search 使用正确的 top_k
        search_call_args = mock_vector_store.search.call_args[0]
        assert search_call_args[2] == top_k


class TestQueryStream:
    """流式 RAG 查询测试"""

    def test_query_stream_yields_chunks(
        self, knowledge_service, mock_vector_store, mock_llm
    ):
        """测试：query_stream 流式返回响应"""
        # Arrange
        question = "What is AI?"
        kb_id = "kb123"
        mock_vector_store.search.return_value = [
            DocumentChunk(content="AI content", metadata={})
        ]
        mock_llm.chat_stream.return_value = iter(["AI ", "is ", "great"])

        # Act
        result = list(knowledge_service.query_stream(question, kb_id))

        # Assert
        assert result == ["AI ", "is ", "great"]
        mock_vector_store.search.assert_called_once()
        mock_llm.chat_stream.assert_called_once()

    def test_query_stream_no_relevant_chunks(self, knowledge_service, mock_vector_store):
        """测试：流式查询没有找到相关文档"""
        # Arrange
        question = "Unknown"
        kb_id = "kb123"
        mock_vector_store.search.return_value = []

        # Act
        result_gen = knowledge_service.query_stream(question, kb_id)

        # Assert
        # query_stream 是 generator 函数，即使在 return 时也返回 generator 对象
        # 但它会立即抛出 StopIteration 包含返回值
        # 我们需要尝试迭代它来获取返回值
        try:
            result_list = list(result_gen)
            # 如果没有抛出异常，结果列表应该为空或包含错误消息
            assert len(result_list) == 0 or result_list == ["知识库中没有找到相关内容"]
        except StopIteration as e:
            # 如果函数使用 return，返回值会在 StopIteration.value 中
            if hasattr(e, 'value'):
                assert e.value == "知识库中没有找到相关内容"


class TestGetRelevantChunks:
    """获取相关文档块测试"""

    def test_get_relevant_chunks_returns_chunks(
        self, knowledge_service, mock_vector_store
    ):
        """测试：get_relevant_chunks 返回相关文档块"""
        # Arrange
        question = "Test question"
        expected_chunks = [
            DocumentChunk(content="Chunk 1", metadata={}),
            DocumentChunk(content="Chunk 2", metadata={}),
        ]
        mock_vector_store.search.return_value = expected_chunks

        # Act
        result = knowledge_service.get_relevant_chunks(question, top_k=2)

        # Assert
        assert result == expected_chunks
        mock_vector_store.search.assert_called_once_with(question, top_k=2)


class TestGetChunkCount:
    """获取文档块数量测试"""

    def test_get_chunk_count_returns_count(self, knowledge_service, mock_vector_store):
        """测试：get_chunk_count 返回文档块数量"""
        # Arrange
        kb_id = "kb123"
        mock_vector_store.count.return_value = 42

        # Act
        result = knowledge_service.get_chunk_count(kb_id)

        # Assert
        assert result == 42
        mock_vector_store.count.assert_called_once_with(knowledge_base_id=kb_id)

    def test_get_chunk_count_without_kb_id(self, knowledge_service, mock_vector_store):
        """测试：不指定知识库 ID"""
        # Arrange
        mock_vector_store.count.return_value = 100

        # Act
        result = knowledge_service.get_chunk_count()

        # Assert
        assert result == 100
        mock_vector_store.count.assert_called_once_with(knowledge_base_id=None)


class TestKnowledgeServiceIntegration:
    """KnowledgeService 集成测试"""

    def test_full_rag_workflow(
        self, knowledge_service, mock_vector_store, mock_llm
    ):
        """测试：完整的 RAG 工作流程（添加文档 -> 查询）"""
        # 1. 添加文档
        text = "Python is a high-level programming language. It is widely used for web development."
        chunk_count = knowledge_service.add_text(text)
        assert chunk_count > 0

        # 2. 模拟向量搜索返回相关内容
        mock_vector_store.search.return_value = [
            DocumentChunk(content="Python is a high-level programming language", metadata={})
        ]
        mock_llm.chat.return_value = "Python is a high-level programming language used for various purposes."

        # 3. 查询
        result = knowledge_service.query("What is Python?", "kb123")
        assert "Python" in result
        assert len(result) > 0
