"""基于 LangGraph 状态机的智能电商导购系统"""

import os
import json
import re
from typing import Dict, Any, List, Optional, TypedDict
from urllib.parse import quote

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from ..services.llm_service import get_llm
from ..services.unsplash_service import get_unsplash_service
from ..models.schemas import (
    ShoppingRequest, ShoppingReport, ProductDetail,
    ProductSpec, PriceHistory, ReviewSentiment
)
from ..config import get_settings
from backend.logger import logger
from tavily import TavilyClient

# ============ 1. 联网搜索工具 ============
settings = get_settings()
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def search_real_products(query: str, free_text_input: str) -> str:
    """基于 Tavily 联网检索商品实时信息，失败则自动降级使用 DuckDuckGo 检索"""
    try:
        # 优先将用户的具体个性化需求（如 iPhone 17）放在检索词最前面
        text_clean = free_text_input.replace("想要", "").replace("需要", "").strip()
        if text_clean:
            enhanced_query = f"{text_clean} {query} 2026款 在售 官方价格 详细参数"
        else:
            enhanced_query = f"{query} 2026年最新款 在售 官方价格 详细参数 真机图片"

        logger.info(f"🔍 正在检索实时数据: {enhanced_query}")
        response = tavily_client.search(
            query=enhanced_query,
            search_depth="advanced",
            max_results=12,
            include_images=True
        )

        result_text = "搜索结果：\n"
        results = response.get("results") or [] if response else []
        for idx, item in enumerate(results):
            result_text += f"\n--- 结果 {idx+1} ---\n"
            result_text += f"标题：{item['title']}\n"
            result_text += f"摘要：{item.get('content', item.get('snippet', ''))}\n"
            result_text += f"详情：{item.get('raw_content', '')[:500]}\n"
            result_text += f"来源：{item['url']}\n"

        result_text += "\n📷 商品图片链接：\n"
        images = response.get("images") or [] if response else []
        for img in images[:6]:
            result_text += f"- {img}\n"

        return result_text
    except Exception as e:
        logger.error(f"[Tavily搜索异常] {str(e)}")
        
        # 降级使用 DuckDuckGo 网页检索
        try:
            logger.info(f"🔌 [Tavily 检索失效] 正在降级调用 DuckDuckGo 网页检索...")
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                ddg_query = f"{query} 2026款 价格 参数"
                results = ddgs.text(ddg_query, max_results=6)
                if results:
                    result_text = "DuckDuckGo 检索结果：\n"
                    for idx, res in enumerate(results):
                        result_text += f"\n--- 结果 {idx+1} ---\n"
                        result_text += f"标题：{res.get('title')}\n"
                        result_text += f"摘要：{res.get('body')}\n"
                        result_text += f"来源：{res.get('href')}\n"
                    return result_text
        except Exception as ddg_err:
            logger.error(f"[DuckDuckGo搜索异常] {ddg_err}")

        return "搜索服务暂时不可用，请稍后重试"

# ============ 2. 状态定义 ============
class AgentState(TypedDict):
    request: ShoppingRequest
    retry_count: int
    error_feedback: Optional[str]
    research_raw: str
    sentiment_raw: str
    final_report: Optional[Dict[str, Any]]

# ============ 3. 提示词定义 ============
PRODUCT_RESEARCH_AGENT_PROMPT = """你是一个专业的商品调研专家。你的任务是从搜索结果中筛选出3-4款最符合用户要求的最新、在售商品，并提炼其关键规格参数和真实价格。
注意：当前时间是2026年，请务必保证筛选出的商品具备时效性。"""

SENTIMENT_ANALYST_AGENT_PROMPT = """你是一个专业的口碑情绪分析师。请结合调研出的商品数据，分析它们的用户反馈。
要求提炼出红榜（核心卖点与好评）和黑榜（翻车吐槽、细节缺陷等），给出专业评分(0-10分)，并指出该商品不适合什么样的人群。"""

CHIEF_ADVISOR_AGENT_PROMPT = """你是首席电商导购专家。你的终极任务是将调研和评价数据整合为一份严谨的 JSON 报告。

### ⛔ 严格禁忌（违反将导致系统崩溃）：
1. **禁止嵌套**：`recommended_products` 必须是平铺的列表 `[]`，严禁按价格或品牌分层。
2. **禁止对象化**：`best_overall` 和 `best_budget` 必须是纯字符串（型号名），严禁返回 `{"model": "..."}`。
3. **数据完整**：每个产品必须包含 `product_id`, `price_info` 和 `sentiment` 结构。
4. **绝对禁止虚构伪造**：严禁出现 "A品牌"、"某品牌" 等占位符！所有商品名称必须是真实市场存在的真实品牌与真实型号。
5. **对比矩阵键名一字不差**：`decision_matrix` 中的每个对象，必须包含 key 为 `"项目"` 的对比维度（如"续航"、"画质"、"性价比"等），以及其余每个商品的 `name` 【完全一字不差的全称】作为键名，绝不能简写、错填或漏填！

### 🚨 核心指令：
1. **智能品类契合**：根据商品的实际品类特征（如手机看处理器/屏幕，耳机看降噪/续航，相机看感光元件/重量/画质，服装看材质/版型），动态提炼 3-4 个最核心的规格项。
2. **数据提取优先级**：优先寻找并提取商品的【真实全称】、【当前价格】、【核心参数】。
3. **拒绝模糊**：不要只提供市场趋势分析，必须输出具体的商品型号。

### 📄 输出模板（通用规范）：
你必须且只能输出如下格式的 JSON，不要包含任何前导词或总结语：
```json
{
  "category": "商品类别",
  "search_timestamp": "2026-04-06",
  "recommended_products": [
    {
      "product_id": "p1",
      "name": "商品真实全称A",
      "brand": "品牌A",
      "main_image": "",
      "specs": [{"key": "品类核心参数1", "value": "参数值1", "is_highlight": true}],
      "price_info": {
        "current_price": 2999.0,
        "historical_low": 2600.0,
        "is_good_deal": true,
        "discount_tag": "近期好价"
      },
      "sentiment": {
        "positive_tags": ["核心好评1"],
        "negative_tags": ["短板吐槽1"],
        "summary": "口碑综述",
        "expert_score": 9.0
      },
      "recommend_reason": "推荐理由",
      "buy_link": ""
    }
  ],
  "decision_matrix": [
    {"项目": "品类核心对比维度1", "商品真实全称A": "评价/数值A", "商品真实全称B": "评价/数值B"}
  ],
  "best_overall": "商品真实全称A",
  "best_budget": "商品真实全称B",
  "expert_tips": ["避雷提示"],
  "overall_summary": "全文总结"
}
```
"""

# ============ 4. 状态机节点 Nodes 业务实现 ============
def research_node(state: AgentState) -> Dict[str, Any]:
    req = state["request"]
    query = f"{req.product_category} 推荐"
    if req.brand_preference:
        query += " " + " ".join(req.brand_preference)
    
    # 联网搜索
    search_results = search_real_products(query, req.free_text_input)
    
    # AI 整理
    llm = get_llm()
    prompt = f"用户需求：类别={req.product_category}，预算={req.budget_range['min']}-{req.budget_range['max']}元。"
    if req.free_text_input.strip():
        prompt += f" 个性化偏好/指定型号：{req.free_text_input.strip()}（请务必优先围绕此偏好筛选商品）\n"
    else:
        prompt += "\n"
    if state.get("error_feedback"):
        prompt += f"上一次校验报错：{state['error_feedback']}\n请在本次整理中进行针对性修复。\n"
    prompt += f"\n联网检索结果如下：\n{search_results}"
    
    messages = [
        SystemMessage(content=PRODUCT_RESEARCH_AGENT_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    return {"research_raw": response.content}

def sentiment_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    messages = [
        SystemMessage(content=SENTIMENT_ANALYST_AGENT_PROMPT),
        HumanMessage(content=f"请对以下调研商品进行口碑和情绪红黑榜分析：\n\n{state['research_raw']}")
    ]
    response = llm.invoke(messages)
    return {"sentiment_raw": response.content}

def advisor_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    req = state["request"]
    
    prompt = f"""请整合以下商品调研数据与口碑分析，生成一份结构化且完美的导购报告：
用户需求：类别={req.product_category}，预算范围={req.budget_range['min']}-{req.budget_range['max']}元。
特定偏好/指定型号：{req.free_text_input if req.free_text_input.strip() else '无'}
【重要规则】：如果用户指定了具体型号或系列（如 iPhone 17 系列），推荐列表的第一位必须是该指定型号/系列，且列表中应优先展示该系列的细分型号（如标准版、Pro、Pro Max）！

【商品调研原始信息】
{state['research_raw']}

【口碑红黑榜情绪分析】
{state['sentiment_raw']}
"""
    messages = [
        SystemMessage(content=CHIEF_ADVISOR_AGENT_PROMPT),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        
        # 使用正则表达式健壮地匹配并提取 JSON
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError("模型输出未包含 JSON 结构")
            
        data = json.loads(match.group())
        
        # 进行嵌套格式清洗扁平化，以防 Pydantic 校验报错
        raw_products = data.get('recommended_products')
        if isinstance(raw_products, dict):
            logger.info("🔧 检测到嵌套字典，正在强制平铺产品列表...")
            flattened = []
            for value in raw_products.values():
                if isinstance(value, list):
                    flattened.extend(value)
                else:
                    flattened.append(value)
            data['recommended_products'] = flattened

        if not isinstance(data.get('recommended_products'), list):
            data['recommended_products'] = []

        # 校验并还原为 Pydantic 验证格式
        report = ShoppingReport(**data)
        report_dict = report.model_dump() if hasattr(report, "model_dump") else report.dict()
        return {"final_report": report_dict}
        
    except Exception as e:
        logger.error(f"[AdvisorNode 解析报错] {e}")
        return {"final_report": None}

def search_product_image(product_name: str) -> Optional[str]:
    """通过 Tavily 搜索真实的商品图片，若失败则降级使用 DuckDuckGo，最后使用 Unsplash 兜底"""
    # 1. 尝试使用 Tavily 搜图 (最精准的真实商品图)
    try:
        settings = get_settings()
        if settings.TAVILY_API_KEY:
            tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
            res = tavily.search(query=f"{product_name} 真机图片 官方图", max_results=3, include_images=True)
            images = res.get("images") or [] if res else []
            if images and isinstance(images, list):
                for img in images:
                    if img.startswith("http"):
                        logger.info(f"📸 [Tavily 搜图成功] 商品: {product_name} -> {img}")
                        return img
    except Exception as e:
        logger.error(f"[Tavily图片搜索异常] {e}")

    # 2. 降级使用 DuckDuckGo 免 Key 搜图
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            # 搜索时加“真机图片”过滤掉无关杂图
            results = ddgs.images(f"{product_name} 真机图片", max_results=3)
            if results:
                for res in results:
                    img = res.get("image")
                    if img and img.startswith("http"):
                        logger.info(f"📸 [DuckDuckGo 搜图成功] 商品: {product_name} -> {img}")
                        return img
    except Exception as e:
        logger.error(f"[DDG图片搜索异常] {e}")

    # 3. 最终由 Unsplash 摄影图兜底
    try:
        unsplash_svc = get_unsplash_service()
        img = unsplash_svc.get_photo_url(product_name)
        if img:
            logger.info(f"📸 [Unsplash 搜图成功] 商品: {product_name} -> {img}")
            return img
    except Exception as e:
        logger.error(f"[Unsplash图片搜索异常] {e}")

    return None

def image_link_node(state: AgentState) -> Dict[str, Any]:
    report = state.get("final_report")
    if not report:
        return {}

    products = report.get("recommended_products", [])
    
    for product in products:
        name = product.get("name", "")
        # 调用搜图引擎
        img_url = search_product_image(name)
        product["main_image"] = img_url or ""
            
        # 补全淘宝外链
        if not product.get("buy_link") or product.get("buy_link") in ["", "#", None]:
            search_name = product.get("name") or state["request"].product_category
            product["buy_link"] = f"https://s.taobao.com/search?q={quote(str(search_name))}"
            
    return {"final_report": report}

def retry_feedback_node(state: AgentState) -> Dict[str, Any]:
    count = state.get("retry_count", 0) + 1
    feedback = "生成的报告数据校验未通过，产品推荐列表为空。已为您启动反射自纠错第 {} 次重试...".format(count)
    logger.warning(feedback)
    return {
        "retry_count": count,
        "error_feedback": feedback
    }

# ============ 5. 编排状态图 (LangGraph Compiler) ============
def route_after_validation(state: AgentState) -> str:
    report = state.get("final_report")
    if not report or not report.get("recommended_products"):
        state["error_feedback"] = "产品推荐列表为空，请重新生成。"
        return "retry" if state.get("retry_count", 0) < 2 else "fallback"

    # 🌟 Reflection 核心：检测是否包含虚构/占位品牌
    fake_brand_keywords = ["A品牌", "某品牌", "品牌A", "未知品牌", "虚拟", "X200"]
    products = report.get("recommended_products", [])
    for p in products:
        b_name = str(p.get("brand", ""))
        p_name = str(p.get("name", ""))
        if any(kw in b_name or kw in p_name for kw in fake_brand_keywords):
            logger.warning(f"🚨 [Reflection 触发] 拦截到虚构商品: {p_name} ({b_name})")
            state["error_feedback"] = f"生成的商品 '{p_name}' 包含虚构品牌词，违反真实性原则！请剔除假商品，重新推荐真实存在的品牌（如宝丽来、富士、佳能、索尼等）。"
            return "retry" if state.get("retry_count", 0) < 2 else "fallback"

    return "end"

workflow = StateGraph(AgentState)

# 注册节点
workflow.add_node("research", research_node)
workflow.add_node("sentiment", sentiment_node)
workflow.add_node("advisor", advisor_node)
workflow.add_node("image_link", image_link_node)
workflow.add_node("retry_feedback", retry_feedback_node)

# 注册连线
workflow.add_edge(START, "research")
workflow.add_edge("research", "sentiment")
workflow.add_edge("sentiment", "advisor")
workflow.add_edge("advisor", "image_link")

# 注册带判断 of 边
workflow.add_conditional_edges(
    "image_link",
    route_after_validation,
    {
        "retry": "retry_feedback",
        "fallback": END,
        "end": END
    }
)
workflow.add_edge("retry_feedback", "research")

# 编译 Graph 实例
compiled_graph = workflow.compile()

# ============ 6. 包装为 MultiAgentShoppingAdvisor 单例接口 ============
class MultiAgentShoppingAdvisor:
    def __init__(self):
        self.graph = compiled_graph
        logger.info("✅ LangGraph 智能导购状态图加载成功")

    def generate_shopping_report(self, request: ShoppingRequest) -> ShoppingReport:
        initial_state = {
            "request": request,
            "retry_count": 0,
            "error_feedback": None,
            "research_raw": "",
            "sentiment_raw": "",
            "final_report": None
        }

        try:
            from langchain_community.callbacks import get_openai_callback

            # 运行图状态机并统计 Token 消耗 (同步调用)
            with get_openai_callback() as cb:
                final_state = self.graph.invoke(initial_state)
                prompt_tokens = cb.prompt_tokens
                completion_tokens = cb.completion_tokens

            report_data = final_state.get("final_report")

            if not report_data:
                raise ValueError("状态机执行结束，未产出有效报告")

            # 最终检验格式并还原为 Pydantic 传回路由层
            report = ShoppingReport(**report_data)
            report._prompt_tokens = prompt_tokens
            report._completion_tokens = completion_tokens
            return report

        except Exception as e:
            logger.error(f"❌ [LangGraph 链路执行崩溃]: {e}")
            return self._create_fallback_report(request)

    def _create_fallback_report(self, request: ShoppingRequest) -> ShoppingReport:
        """容灾服务降级兜底"""
        p1 = ProductDetail(
            product_id="f1", name="索尼 WH-1000XM5", brand="Sony",
            main_image="", specs=[], recommend_reason="行业降噪标杆",
            price_info=PriceHistory(current_price=2299.0, historical_low=1999.0, is_good_deal=True, discount_tag="热卖"),
            sentiment=ReviewSentiment(positive_tags=["降噪极强"], negative_tags=["折叠不便"], summary="全能之选", expert_score=9.0),
            buy_link=f"https://s.taobao.com/search?q={quote('索尼 WH-1000XM5')}"
        )
        return ShoppingReport(
            category=request.product_category,
            search_timestamp="2026-04-06",
            recommended_products=[p1],
            decision_matrix=[],
            best_overall="索尼 WH-1000XM5",
            best_budget="待更新",
            expert_tips=["由于流量较大已触发降级保护，建议您在 618 期间选购此推荐型号"],
            overall_summary="系统已自动为您进行降级服务，已展示推荐型号."
        )

# 单例导出
_instance = None
def get_shopping_advisor_agent():
    global _instance
    if _instance is None:
        _instance = MultiAgentShoppingAdvisor()
    return _instance