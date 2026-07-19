"""
智能电商导购数据模型
包含请求、商品详情、测评分析、比价及最终决策建议
适配 HelloAgents 框架 + FastAPI + Vue3 前端
"""

from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

# ============ 枚举规范（新增：适配前后端，避免乱码） ============
class ProductCategoryEnum(str, Enum):
    SMARTPHONE = "智能手机"
    LAPTOP = "笔记本电脑"
    HEADPHONE = "耳机"
    CLOTHES = "服饰"
    HOME_APPLIANCE = "家电"
    OTHER = "其他"

# 🌟 新增：监控指标模型
class MonitoringMetrics(BaseModel):
    latency_ms: int
    llm_cost_cny: float
    total_requests: int

class ShoppingReport(BaseModel):
    category: str
    search_timestamp: str
    budget_range: str
    recommended_products: List[dict]
    decision_matrix: List[dict]
    best_overall: str
    best_budget: str
    expert_tips: List[str]
    overall_summary: str
    # 🌟 核心修改：允许返回 metrics 字段
    metrics: Optional[MonitoringMetrics] = None

# ============ 请求模型 ============

class ShoppingRequest(BaseModel):
    """用户购物意向请求（对接前端表单）"""
    product_category: str = Field(..., description="产品类别", example="智能手机")
    # 预算范围：保留你的设计，增加验证
    budget_range: Dict[str, int] = Field(..., description="预算范围", example={"min": 3000, "max": 5000})
    usage_scenarios: List[str] = Field(default=[], description="使用场景", example=["游戏驱动", "长途出差", "拍照录像"])
    brand_preference: List[str] = Field(default=[], description="品牌倾向", example=["华为", "苹果", "小米"])
    core_features: List[str] = Field(default=[], description="必须具备的功能", example=["防水", "无线充电", "1T内存"])
    free_text_input: Optional[str] = Field(default="", description="其他个性化要求")

    # 验证预算合法性
    @field_validator("budget_range")
    def check_budget(cls, v):
        if v["min"] < 0 or v["max"] < 0 or v["min"] > v["max"]:
            raise ValueError("预算范围不合法")
        return v

# ============ 核心数据组件 ============

class ProductSpec(BaseModel):
    """商品硬件/核心参数"""
    key: str = Field(..., description="参数名称,如'处理器'")
    value: str = Field(..., description="参数数值,如'骁龙8 Gen3'")
    is_highlight: bool = Field(default=False, description="是否为该产品的核心卖点")

class PriceHistory(BaseModel):
    """价格走势信息（修复：价格非负，优化字段）"""
    current_price: float = Field(..., ge=0, description="当前售价")
    historical_low: float = Field(..., ge=0, description="历史最低价")
    is_good_deal: bool = Field(default=False, description="当前是否值得购买")
    discount_tag: Optional[str] = Field(default="", description="优惠活动标签")

class ReviewSentiment(BaseModel):
    """用户评价情绪分析（修复：分数0-10验证）"""
    positive_tags: List[str] = Field(default=[], description="好评关键词")
    negative_tags: List[str] = Field(default=[], description="差评/吐槽点")
    summary: str = Field(default="", description="口碑总结")
    expert_score: float = Field(..., ge=0, le=10, description="专业评测分(0-10)")

# ============ 最终响应模型 ============

class ProductDetail(BaseModel):
    """单体商品全维度画像"""
    product_id: str = Field(..., description="商品唯一ID")
    name: str = Field(..., description="商品完整名称")
    brand: str = Field(..., description="品牌名")
    main_image: str = Field(default="", description="主图链接")
    image_url: Optional[str] = None
    specs: List[ProductSpec] = Field(default=[], description="详细规格参数列表")
    price_info: PriceHistory = Field(..., description="价格分析")
    sentiment: ReviewSentiment = Field(..., description="口碑画像")
    recommend_reason: str = Field(default="", description="推荐理由")
    buy_link: str = Field(default="#", description="直达购买链接")

class ShoppingReport(BaseModel):
    """最终导购对比报告（顶层响应模型，对接API）"""
    category: str = Field(..., description="产品类别")
    search_timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="数据生成时间"
    )

    # 核心推荐列表（默认3款，适配AI输出）
    recommended_products: List[ProductDetail] = Field(default=[], description="精选对比列表(3款)")

    # 决策矩阵（简化类型，前端完美对接）
    decision_matrix: List[Dict] = Field(default=[], description="对比表格数据")

    # 最终建议
    best_overall: str = Field(default="", description="综合首选型号")
    best_budget: str = Field(default="", description="性价比首选型号")
    expert_tips: List[str] = Field(default=[], description="避雷建议")
    overall_summary: str = Field(default="", description="导购总结")