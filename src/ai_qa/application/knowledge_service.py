from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_qa.domain.entities import DocumentChunk, KnowledgeBase, MessageRole, Message
from ai_qa.domain.ports import VectorStorePort, LLMPort, ConversationMemoryPort
from ai_qa.infrastructure.database.models import Document as DocumentModel

class KnowledgeService:
    """知识库服务"""

    def __init__(
            self,
            vector_store: VectorStorePort,
            llm: LLMPort,
            memory: ConversationMemoryPort,
            db = None, # 数据库服务
            chunk_size: int = 500,
            chunk_overlap: int = 50
    ):
        self._vector_store = vector_store
        self._llm = llm
        self._memory = memory
        self._db = db

        # 文本切分器
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap= chunk_overlap,
            length_function=len,
        )

        self._knowledge_base: KnowledgeBase = None
    
    def create_knowledge_base(self, name: str, descripton: str = "") -> KnowledgeBase:
        """创建知识库"""
        self._knowledge_base = KnowledgeBase(name=name,description=descripton)
        self._vector_store.clear()
        return self._knowledge_base
    
    def add_text(self, text: str, metadata: dict = None) -> int:
        """添加文本到知识库
        
        Arg:
            text: 文本内容
            metadata: 元数据（如来源、标题等）
        
        Returns:
            添加的文档块数量
        """
        if metadata is None:
            metadata = {}

        # 切分文本
        texts = self._splitter.split_text(text)

        # 创建文档块
        chunks = [
            DocumentChunk(content=t, metadata=metadata) 
            for t in texts
        ]
        
        # 添加到向量存储
        self._vector_store.add_documents(chunks)

        # 更新知识库统计
        if self._knowledge_base:
            self._knowledge_base.documnet_count += len(chunks)

        return len(chunks)

    def add_file(self, file_path: str) -> int:
        """从文件添加内容到知识库
        
        Args:
            file_path: 文件路径
        
        Returns:
            添加的文档块数量
        """

        with open(file_path, 'r',encoding='utf-8') as f:
            text = f.read()

        metadata = {"source": file_path}
        return self.add_text(text,metadata)
    
    def add_document(
            self,
            knowledge_base_id: int,
            title: str,
            content: str,
            file_type: str = "text",
            file_size: int = None,
            file_path: str = None
    ) -> int:
        """添加文档到知识库"""
        # 1. 创建文档记录
        doc = DocumentModel(
            knowledge_base_id=knowledge_base_id,
            title=title,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size or len(content.encode('utf-8'))
        )
        self._db.add(doc)
        self._db.flush()

        # 2. 切分文件
        text_chunks = self._splitter.split_text(content)

        # 3. 创建 DocumentChunk 实体
        chunks = []
        for i, text in enumerate(text_chunks):
            chunk = DocumentChunk(
                content=text,
                document_id=doc.id,
                chunk_id=i,
                metadata={"title":title}
            )
            chunks.append(chunk)
        
        # 4. 向量化存储
        self._vector_store.add_documents(chunks, knowledge_base_id=knowledge_base_id)

        # 5. 提交事务
        self._db.commit()

        return len(chunks)

    def _rewrite_query(self, session_id: str, question: str) -> str:
        """根据对话历史改写查询（解决指代问题）"""

        # 获取历史对话
        conversation = self._memory.get_conversation(session_id)
       
        # 如果没有历史对话，则直接返回原问题
        if not conversation.messages:
            return question

        # 构建历史对话文本
        history_text = ""
        for msg in conversation.messages[-6:]:
            role = "用户" if msg.role == MessageRole.USER else "AI"
            history_text += f"{role}: {msg.content}\n"
        
        # 构建改写提示词
        rewrtie_prompt = f""" 你的任务是：将用户的问题改写成一个独立完整的问题。

        规则：
        1. 如果问题中有代替（它、他、这个等），根据对话历史替换成具体指代
        2. 如果问题已经完整清晰，直接返回原问题
        2. 只输出改写后的问题，不要任何解释

        对话历史：
        {history_text}

        当前问题：
        {question}

        改写后的问题："""

        # 调用 LLM 进行改写
        messages = [Message(role=MessageRole.USER, content=rewrtie_prompt)]
        rewritten = self._llm.chat(messages)

        return rewritten.strip()

    def query(self, question: str, knowledge_base_id: int,session_id: str = None, top_k: int = 3) -> str:
        """基于知识库回答问题(RAG)
        
        Args:
            question: 用户问题
            knowledge_base_id: 知识库 ID
            session_id: 会话 ID
            top_k: 检索的文档块数量

        Returns:
            AI 的回答
        """
        # 1. 查询改写（如果有 session_id）
        search_query = question
        if session_id:
            search_query = self._rewrite_query(session_id,question)
            if search_query != question:
                print(f"[查询改写]{question} -> {search_query}")
        
        # 2. 检索相关文档
        relevtant_chunks = self._vector_store.search(search_query, knowledge_base_id, top_k)

        if not relevtant_chunks:
            return "知识库中没有找到相关内容"
        
        # 3. 构建上下文
        context = "\n\n".join([chunk.content for chunk in relevtant_chunks])

        # 4. 构建 RAG Prompt
        from ai_qa.domain.entities import Message, MessageRole

        system_prompt = """
            你是一个知识库问答助手。请根据以下提供的参考内容回答用户的问题。
            如果参考内容中没有相关信息，请诚实地说"根据现有资料无法回答这个问题"。
            回答时请简洁明了，直接回答问题。
            """
        
        user_message = f"""
            参考内容：
            {context}

            用户问题：{question}

            请根据参考内容回答问题：
            """
        
        messages = [Message(role=MessageRole.USER, content=user_message)]

        # 5. 调用 LLM 生成回答
        response = self._llm.chat(messages, system_prompt=system_prompt)

        return response
    
    def query_stream(self, question: str, knowledge_base_id: int, session_id: str = None, top_k: int = 3) -> str:
        """基于知识库回答问题(RAG)
        
        Args:
            question: 用户问题
            session_id: 会话 ID
            top_k: 检索的文档块数量

        Returns:
            AI 的回答
        """
        # 1. 查询改写（如果有 session_id）
        search_query = question
        if session_id:
            search_query = self._rewrite_query(session_id,question)
            if search_query != question:
                print(f"[查询改写]{question} -> {search_query}")
        
        # 2. 检索相关文档
        relevtant_chunks = self._vector_store.search(search_query, knowledge_base_id, top_k)

        if not relevtant_chunks:
            return "知识库中没有找到相关内容"
        
        # 3. 构建上下文
        context = "\n\n".join([chunk.content for chunk in relevtant_chunks])

        # 4. 构建 RAG Prompt
        from ai_qa.domain.entities import Message, MessageRole

        system_prompt = """
            你是一个知识库问答助手。请根据以下提供的参考内容回答用户的问题。
            如果参考内容中没有相关信息，请诚实地说"根据现有资料无法回答这个问题"。
            回答时请简洁明了，直接回答问题。
            """
        
        user_message = f"""
            参考内容：
            {context}

            用户问题：{question}

            请根据参考内容回答问题：
            """
        
        messages = [Message(role=MessageRole.USER, content=user_message)]

        # 5. 调用 LLM 生成回答

        for chunk in self._llm.chat_stream(messages, system_prompt=system_prompt):
            yield chunk

    def get_relevant_chunks(self, question: str, top_k: int = 3) -> list[DocumentChunk]:
        """获取相关文档块（用于调试或展示来源）"""
        return self._vector_store.search(question, top_k=top_k)

    def get_chunk_count(self, knowledge_base_id: int = None) -> int:
        """返回知识库中的文档块数量"""
        return self._vector_store.count(knowledge_base_id=knowledge_base_id)



