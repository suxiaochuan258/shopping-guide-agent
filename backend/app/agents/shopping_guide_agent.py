"""智能电商导购多智能体系统 - 最终修复版"""

import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from duckduckgo_search import DDGS

from hello_agents import SimpleAgent
from ..services.llm_service import get_llm
from ..models.schemas import (
    ShoppingRequest, ShoppingReport, ProductDetail,
    ProductSpec, PriceHistory, ReviewSentiment
)
from ..config import get_settings
from backend.logger import logger
from tavily import TavilyClient

# ============ 1. 联网搜索函数 ============
# 从配置文件读取API Key（推荐，避免硬编码）
settings = get_settings()
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)

def search_real_products(query: str, free_text_input) -> str:
    """
    替换DDGS的Tavily搜索工具，专为商品调研优化
    """
    try:
        # 👇 【关键修改】自动追加 2026 最新关键词，通用所有商品，不绑定机型
        enhanced_query = f"{query} 2026年最新款 在售 官方价格 详细参数 真机图片"

        # 👇 我只加了这一行：用户填了个性化要求，就拼进搜索词；没填就不影响原有逻辑
        if free_text_input.strip():
            enhanced_query += f" {free_text_input.strip()}"

        # 核心参数配置
        response = tavily_client.search(
            query=enhanced_query,  # 👈 使用增强后的查询
            search_depth="advanced",
            max_results=12,
            include_answer=True,
            include_raw_content=True,
            include_images=True  # 👈 打开图片，让前端显示真实商品图
        )

        # 格式化结果，方便LLM读取
        result_text = "搜索结果：\n"
        for idx, item in enumerate(response["results"]):
            result_text += f"\n--- 结果 {idx+1} ---\n"
            result_text += f"标题：{item['title']}\n"
            result_text += f"摘要：{item['snippet']}\n"
            result_text += f"详情：{item['raw_content'][:500]}\n"
            result_text += f"来源：{item['url']}\n"

        # 👇 【追加】把商品图片也一起返回，让前端能显示
        result_text += "\n📷 商品图片链接：\n"
        for img in response.get("images", [])[:6]:  # 最多返回6张，避免过多
            result_text += f"- {img}\n"

        return result_text

    except Exception as e:
        print(f"[Tavily搜索异常] {str(e)}")
        return "搜索服务暂时不可用，请稍后重试"

# def search_real_products(keyword: str) -> str:
#     search_query = f"{keyword} 2026 最新参数 官网价格 评价"
#
#     logger.info(f"🔍 正在检索实时数据: {search_query}")
#     try:
#         # 提示：如果警告包重命名，可以忽略，功能目前是正常的
#         with DDGS() as ddgs:
#             results = ddgs.text(
#                 f"{keyword} 推荐商品 型号 价格 2026",
#                 max_results=3 # 稍微减少结果以节省 Token
#             )
#         if not results:
#             return "未找到实时商品数据"
#         return "\n".join([f"- {res['title']}: {res['body']}" for res in results])
#     except Exception as e:
#         logger.error(f"搜索失败: {str(e)}")
#         return "联网搜索服务暂时不可用"

# ============ 2. 工具适配器 ============
class SearchTool:
    def __init__(self):
        self.name = "search_real_products"
        self.description = "联网搜索实时商品信息、型号、价格和参数"

    def get_parameters(self):
        from dataclasses import dataclass
        @dataclass
        class Param:
            name: str
            type: str
        return [Param(name="keyword", type="string")]

    def run(self, args: dict) -> str:
        # 兼容多种参数名传递
        kw = args.get("keyword") or args.get("query") or args.get("input") or ""
        return search_real_products(kw)

# ============ 3. Agent 提示词 ============
# 增加了对 JSON 格式的严厉要求
CHIEF_ADVISOR_AGENT_PROMPT ="""你是首席电商导购专家。你的终极任务是将调研和评价数据整合为一份严谨的 JSON 报告。

### ⛔ 严格禁忌（违反将导致系统崩溃）：
1. **禁止嵌套**：`recommended_products` 必须是平铺的列表 `[]`，严禁按价格或品牌分层。
2. **禁止对象化**：`best_overall` 和 `best_budget` 必须是纯字符串（型号名），严禁返回 `{"model": "..."}`。
3. **数据完整**：每个产品必须包含 `product_id`, `price_info` 和 `sentiment` 结构。

### 🚨 核心指令：
1. **必须产出清单**：你的最终产出必须包含至少 3-4 个具体的商品型号、品牌和大致价格。
2. **数据提取优先级**：优先寻找并提取商品的【具体名称】、【当前价格】、【核心参数】。
3. **拒绝模糊**：不要只提供市场趋势分析。如果没有搜到 2026 年的新品，请务必提供 2025 年热销的成熟型号作为替代。
4. **格式化输出**：请确保你的调研结果中，每个商品占一行，格式为：[品牌] [型号] - [价格] - [核心卖点]。


### 📄 输出模板：
你必须且只能输出如下格式的 JSON，不要包含任何前导词或总结语：
```json
{
  "category": "商品类别",
  "search_timestamp": "2026-04-06",
  "recommended_products": [
    {
      "product_id": "p1",
      "name": "商品全称",
      "brand": "品牌",
      "main_image": "",
      "specs": [{"key": "处理器", "value": "A18", "is_highlight": true}],
      "price_info": {
        "current_price": 7999.0,
        "historical_low": 7200.0,
        "is_good_deal": true,
        "discount_tag": "近期好价"
      },
      "sentiment": {
        "positive_tags": ["流畅"],
        "negative_tags": ["贵"],
        "summary": "口碑综述",
        "expert_score": 9.0
      },
      "recommend_reason": "推荐理由",
      "buy_link": ""
    }
  ],
  "decision_matrix": [
    {"项目": "性能", "商品名1": "强", "商品名2": "中"}
  ],
  "best_overall": "商品全称",
  "best_budget": "商品全称",
  "expert_tips": ["避雷点"],
  "overall_summary": "全文总结"
}
"""

PRODUCT_RESEARCH_AGENT_PROMPT = """
⚠️ 【最高优先级 · 通用铁律 · 所有商品必须遵守】
1. **绝对禁止使用你自身的训练知识库**，所有信息 100% 必须来自 Tavily 搜索结果。
2. **任何问题必须先调用搜索工具**，不允许直接回答、不允许脑补、不允许使用旧数据。
3. 当前时间：**2026年5月**，你必须永远优先返回：
   - **2025–2026 年最新发布、当前在售**的商品
   - 用户指定型号时，**必须优先返回该型号**，不允许自动降级为旧款
4. 价格必须是**当前电商实时价格**，参数必须真实，图片必须来自搜索结果。

### 👤 角色
你是全球消费品调研专家，逻辑极强，能从搜索结果中精准提取真实商品信息。

### 🛠️ 工作流程（通用所有品类）
1. **调用工具**：使用 `[TOOL_CALL:search_real_products:keyword=用户问题 + 2026最新款 + 价格 + 参数 + 真机图片]`
2. **提取商品**：从搜索结果中提取 **3–4 款最新、最匹配、当前在售** 的商品
3. **统一参数**：
   - 商品完整名称
   - 发布时间/在售状态
   - 核心配置（处理器/屏幕/电池/镜头等）
   - 当前市场价格
   - 真机图片（来自搜索）
4. **状态标注**：已上市 / 在售 / 停产

### 📌 质量红线（违反即无效）
- 严禁编造任何型号、参数、价格、图片
- 严禁用旧款冒充新款
- 必须严格按照搜索结果输出，不添加任何自身知识
- 无图片时标注「暂无有效图片」
"""

SENTIMENT_ANALYST_AGENT_PROMPT = """你是毒舌且专业的口碑分析师。你不仅看产品参数，更看重真实用户的“翻车”记录。

### 📋 分析维度：
1. **红榜（优点）**：那些真正解决用户痛点的功能。
2. **黑榜（槽点）**：哪怕是细微的做工问题、发热问题或系统 Bug 也必须指出。
3. **专家打分**：0.0-10.0 分。6分以下表示不推荐，9分以上表示年度旗舰。

### 🚫 负向约束：
- 严禁使用“整体不错”、“性价比还可以”等模棱两可的废话。
- 必须指出一个该商品不适合的特定人群（例如：不适合重度游戏玩家）。
"""

# ============ 4. 主系统类 ============
class MultiAgentShoppingAdvisor:
    def __init__(self):
        try:
            self.llm = get_llm()
            tool = SearchTool()

            self.research_agent = SimpleAgent(
                name="商品调研专家",
                llm=self.llm,
                system_prompt=PRODUCT_RESEARCH_AGENT_PROMPT,
                enable_tool_calling=True
            )
            self.research_agent.add_tool(tool)

            self.sentiment_agent = SimpleAgent("口碑分析专家", self.llm, SENTIMENT_ANALYST_AGENT_PROMPT)
            self.advisor_agent = SimpleAgent("首席导购专家", self.llm, CHIEF_ADVISOR_AGENT_PROMPT)
            logger.info("✅ 多智能体系统初始化完成")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    def generate_shopping_report(self, request: ShoppingRequest) -> ShoppingReport:
        try:
            # 1. 调研
            res_info = self.research_agent.run(f"调研：{request.product_category}, 预算{request.budget_range['min']}-{request.budget_range['max']}")
            # 2. 口碑
            sen_info = self.sentiment_agent.run(f"分析以下商品的口碑：\n{res_info}")
            # 3. 报告
            final_out = self.advisor_agent.run(f"根据以下信息生成JSON：\n需求：{request.product_category}\n信息：{res_info}\n口碑：{sen_info}")

            return self._parse_response(final_out, request)
        except Exception as e:
            logger.error(f"生成过程出错: {e}")
            return self._create_fallback_report(request)

    # 替换 shopping_guide_agent.py 中的 _parse_response 方法
    def _parse_response(self, response: str, request: ShoppingRequest) -> ShoppingReport:
        try:
            # 1. 提取 JSON
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if not match: raise ValueError("未找到JSON")
            data = json.loads(match.group())

            # 🌟 核心修复：如果 AI 返回的是字典 {"价位1": [...], "价位2": [...]}
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

            # 🌟 核心修复：确保数据完整，防止 Pydantic 报错
            if not isinstance(data.get('recommended_products'), list):
                data['recommended_products'] = []

            for i, p in enumerate(data['recommended_products']):
                if not isinstance(p, dict): continue
                # 补齐必填项
                if 'product_id' not in p: p['product_id'] = f"p{i + 1}"
                if 'price_info' not in p:
                    p['price_info'] = {"current_price": 0, "historical_low": 0, "is_good_deal": True}
                if 'sentiment' not in p:
                    p['sentiment'] = {"expert_score": 8.0, "positive_tags": [], "negative_tags": []}

                if not p.get('buy_link'):
                    from urllib.parse import quote
                    search_name = p.get('name', '智能手机')
                    p['buy_link'] = f"https://s.taobao.com/search?q={quote(str(search_name))}"

                try:
                    data = json.loads(match.group())
                    return data  # 直接返回字典
                except:
                    return self._create_fallback_report(request)

            # 3. 校验并返回
            return ShoppingReport(**data)

        except Exception as e:
            logger.warning(f"❌ 解析再次失败，启用兜底: {e}")
            return self._create_fallback_report(request)

    def _create_fallback_report(self, request: ShoppingRequest) -> ShoppingReport:
        """【修复关键】这里不能是 pass，必须返回一个真实的 ShoppingReport 对象"""
        # 创建两个临时的耳机对象
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
            expert_tips=["建议在 618 期间购买"],
            overall_summary="由于数据量过大导致解析波动，已为您展示推荐型号。"
        )

# 单例导出
_instance = None
def get_shopping_advisor_agent():
    global _instance
    if _instance is None:
        _instance = MultiAgentShoppingAdvisor()
    return _instance