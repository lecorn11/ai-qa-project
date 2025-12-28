# 测试配置是否能正确加载
import sys
sys.path.insert(0,"src")

from ai_qa.config.settings import settings

print("配置加载测试:")
print(f"LLM API Key: {settings.llm_api_key.get_secret_value()}")
print(f"LLM Base URL: {settings.llm_base_url}")
print(f"LLM Model Name: {settings.llm_model}")  
print(f"App Environment: {settings.app_env}")
print(f"Debug Mode: {settings.debug}")