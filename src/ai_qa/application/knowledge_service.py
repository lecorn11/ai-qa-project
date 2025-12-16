from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_qa.domain.entities import DocumentChunk, KnowledgeBase
from ai_qa.domain.ports import VectorStorePort, LLMPort

class KnowledgeService:
    """知识库服务"""

    def __init__(
            self,
            vector_store: VectorStorePort,
            llm: LLMPort,
            chunk_size: int = 500,
            chunk_overlap: int = 50
    ):
        self._vector_store = vector_store
        self._llm = llm

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
    
    def query(self, question: str, top_k: int = 3) -> str:
        """基于知识库回答问题(RAG)
        
        Args:
            question: 用户问题
            top_k: 检索的文档块数量

        Returns:
            AI 的回答
        """

        # 1. 检索相关文档
        relevtant_chunks = self._vector_store.search(question,top_k)

        if not relevtant_chunks:
            return "知识库中没有找到相关内容"
        
        # 2. 构建上下文
        context = "\n\n".join([chunk.content for chunk in relevtant_chunks])

        # 3. 构建 RAG Prompt
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

        # 4. 调用 LLM 生成回答
        response = self._llm.chat(messages, system_prompt=system_prompt)

        return response

    def get_relevant_chunks(self, question: str, top_k: int = 3) -> list[DocumentChunk]:
        """获取相关文档块（用于调试或展示来源）"""
        return self._vector_store.search(question, top_k=top_k)

    @property
    def chunk_count(self) -> int:
        """返回知识库中的文档块数量"""
        return self._vector_store.count



