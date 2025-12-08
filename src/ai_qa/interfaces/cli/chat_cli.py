from ai_qa.config.settings import settings
from ai_qa.infrastructure.llm.qwen_adapter import QwenAdapter
from ai_qa.infrastructure.memory.in_memory import InMemoryConversationMemory
from ai_qa.application.chat_service import ChatService

def main():
    # 1. 创建基础设施层实例
    llm = QwenAdapter(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model_name=settings.llm_model
    )
    memory = InMemoryConversationMemory()

    # 2. 创建应用层服务（依赖注入）
    chat_service = ChatService(
        llm=llm,
        memory=memory,
        system_prompt="你是一个友好的助手，回答尽量简洁。"
    )

    # 3. 开始对话
    session_id = "cli_user"

    print("=" * 50)
    print("AI 智能问答系统（输入 'quit' 退出，'clear' 清除历史")
    print("=" * 50)

    while True:
        user_input = input("\n你: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("再见！")
            break

        if user_input.lower() == "clear":
            chat_service.clear_conversation(session_id)
            print("对话历史已清除。")
            continue

        response = chat_service.chat(session_id, user_input)
        print(f"\nAI: {response}")

if __name__ == "__main__":
    main()  


