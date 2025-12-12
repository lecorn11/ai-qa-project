from langchain_community.embeddings import DashScopeEmbeddings

from ai_qa.domain.ports import EmbeddingPort

class DashScopeEmbeddingAdapter(EmbeddingPort):
    """阿里 DashScope Embedding 向量嵌入服务适配器"""

    def __init__(self, api_key: str, model_name: str = "text-embedding-v3"):
        self._client = DashScopeEmbeddings(
            model=model_name,
            dashscope_api_key=api_key
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """将文本列表转换为向量列表"""
        return self._client.embed_documents(texts)
        # 逐个调用 embed_query，避免 embed_documents 的 URL 报错问题
        # return [self._client.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """将查询文本转换为向量"""
        return self._client.embed_query(text)
