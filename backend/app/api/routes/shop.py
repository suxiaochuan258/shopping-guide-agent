# backend/app/api/routes/shop.py
import asyncio
import time
from threading import Lock
from urllib.parse import quote
from fastapi import APIRouter
from ...config import get_settings
from ...models.schemas import ShoppingRequest
from ...agents.shopping_guide_agent import get_shopping_advisor_agent
from ...services.unsplash_service import get_unsplash_service
from backend.logger import logger

# 实时监控指标（简历对齐）
request_count = 0
current_concurrent = 0
lock = Lock()


def calculate_llm_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """根据实际 Token 消耗和配置单价计算模型调用成本"""
    settings = get_settings()
    input_cost = (prompt_tokens / 1000) * settings.llm_input_price_per_k
    output_cost = (completion_tokens / 1000) * settings.llm_output_price_per_k
    return round(input_cost + output_cost, 4)


router = APIRouter(tags=["电商导购助手"])


@router.post("/generate", summary="生成电商导购报告")
async def generate_shopping_report(request: ShoppingRequest):
    global request_count, current_concurrent

    with lock:
        request_count += 1
        current_concurrent += 1

    start_time = time.time()

    try:
        logger.info(f"📥 [Plan阶段] 收到请求：{request.product_category}")
        agent = get_shopping_advisor_agent()

        # 🌟 执行多 Agent 协同流
        raw_result = agent.generate_shopping_report(request)
        
        prompt_tokens = getattr(raw_result, "_prompt_tokens", 0)
        completion_tokens = getattr(raw_result, "_completion_tokens", 0)

        # 🌟 修复关键：将结果统一转化为字典处理
        # 这样无论 Agent 返回的是 Pydantic 模型还是 dict，后续逻辑都统一
        if hasattr(raw_result, "model_dump"):
            report_data = raw_result.model_dump()
        elif hasattr(raw_result, "dict"):
            report_data = raw_result.dict()
        else:
            report_data = raw_result

        # 链路指标计算 (Full-Link Metrics)
        latency_ms = int((time.time() - start_time) * 1000)
        cost_cny = calculate_llm_cost(prompt_tokens, completion_tokens)

        # 注入监控数据（对接前端 Result.vue）
        report_data["metrics"] = {
            "latency_ms": latency_ms,
            "llm_cost_cny": cost_cny,
            "total_requests": request_count,
            "concurrent": current_concurrent
        }

        return {"success": True, "data": report_data}

    except Exception as e:
        logger.error(f"❌ [Execute阶段] 崩溃：{str(e)}")
        # 兜底逻辑：Resilience 层体现
        agent = get_shopping_advisor_agent()
        fallback = agent._create_fallback_report(request)

        # 同样的类型安全转换
        if hasattr(fallback, "model_dump"):
            fb_data = fallback.model_dump()
        elif hasattr(fallback, "dict"):
            fb_data = fallback.dict()
        else:
            fb_data = fallback

        latency_ms = int((time.time() - start_time) * 1000)
        fb_data["metrics"] = {
            "latency_ms": latency_ms,
            "llm_cost_cny": 0.0,
            "total_requests": request_count,
            "concurrent": current_concurrent
        }
        return {"success": True, "message": "触发系统降级服务", "data": fb_data}

    finally:
        with lock:
            current_concurrent -= 1