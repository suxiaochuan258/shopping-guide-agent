"""LLM服务模块"""

from hello_agents import HelloAgentsLLM
from ..config import get_settings
from tenacity import retry, stop_after_attempt, wait_exponential

# 全局LLM实例
_llm_instance = None

@retry(
    stop=stop_after_attempt(2),  # 最多重试2次
    wait=wait_exponential(multiplier=1, min=1, max=3)  # 等待时间递增
)

def get_llm() -> HelloAgentsLLM:
    """
    获取LLM实例(单例模式)

    Returns:
        HelloAgentsLLM实例
    """
    global _llm_instance

    if _llm_instance is None:
        settings = get_settings()

        # HelloAgentsLLM会自动从环境变量读取配置
        # 包括OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL等
        _llm_instance = HelloAgentsLLM()

        print(f"✅ LLM服务初始化成功")
        print(f"   提供商: {_llm_instance.provider}")
        print(f"   模型: {_llm_instance.model}")

    return _llm_instance


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None
