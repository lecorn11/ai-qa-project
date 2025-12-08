from ai_qa.domain.ports import LLMPort

class BaseLLMAdapter(LLMPort):
    """LLM 适配器基类
    
    提供一些通用功能，具体 LLM 实现继承此类
    """
    api_key: str
    base_url: str
    model_name: str

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
    