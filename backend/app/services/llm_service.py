"""LLM服务模块 - LangChain 适配版"""

import os
from langchain_openai import ChatOpenAI
from ..config import get_settings
from tenacity import retry, stop_after_attempt, wait_exponential

# 全局LLM实例
_llm_instance = None

@retry(
    stop=stop_after_attempt(2),  # 最多重试2次
    wait=wait_exponential(multiplier=1, min=1, max=3)  # 等待时间递增
)
def get_llm() -> ChatOpenAI:
    """
    获取 LangChain ChatOpenAI 实例 (单例模式)

    Returns:
        ChatOpenAI 实例
    """
    global _llm_instance

    if _llm_instance is None:
        settings = get_settings()

        # 读取密钥、Base URL 及模型 ID
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or settings.openai_base_url
        model = os.getenv("LLM_MODEL_ID") or os.getenv("OPENAI_MODEL") or settings.openai_model

        if not api_key:
            raise ValueError("OPENAI_API_KEY 或 LLM_API_KEY 未配置，无法初始化 LLM")

        _llm_instance = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0.7
        )

        print(f"✅ LangChain LLM服务初始化成功")
        print(f"   API Base URL: {base_url}")
        print(f"   Model: {model}")

    return _llm_instance


def reset_llm():
    """重置LLM实例"""
    global _llm_instance
    _llm_instance = None
