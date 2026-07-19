// 电商导购助手 类型定义
// 严格对齐后端 Pydantic 模型：backend/app/models/schemas.py

// ============ 用户购物请求表单（对接前端首页表单） ============
export interface ShoppingFormData {
  product_category: string               // 产品类别
  budget_range: {
    min: number
    max: number
  }
  usage_scenarios: string[]              // 使用场景
  brand_preference: string[]             // 品牌倾向
  core_features: string[]                // 核心功能
  free_text_input: string                // 个性化要求
}

// ============ 商品参数 ============
export interface ProductSpec {
  key: string                            // 参数名称
  value: string                          // 参数数值
  is_highlight: boolean                  // 是否核心卖点
}

// ============ 价格信息 ============
export interface PriceHistory {
  current_price: number                  // 当前售价
  historical_low: number                 // 历史最低价
  is_good_deal: boolean                  // 是否值得买
  discount_tag?: string                  // 优惠标签
}

// ============ 评价分析 ============
export interface ReviewSentiment {
  positive_tags: string[]                // 好评关键词
  negative_tags: string[]                // 差评关键词
  summary: string                        // 口碑总结
  expert_score: number                   // 专业评分 0-10
}

// ============ 商品详情 ============
export interface ProductDetail {
  product_id: string                     // 商品ID
  name: string                           // 商品名称
  brand: string                          // 品牌
  main_image: string                     // 主图链接
  specs: ProductSpec[]                   // 参数列表
  price_info: PriceHistory               // 价格信息
  sentiment: ReviewSentiment             // 口碑分析
  recommend_reason: string               // 推荐理由
  buy_link: string                       // 购买链接
}

// ============ 最终导购报告（对接后端返回数据） ============
export interface ShoppingReport {
  category: string                        // 商品类别
  search_timestamp: string                // 生成时间
  recommended_products: ProductDetail[]   // 推荐商品列表
  decision_matrix: Record<string, any>[]  // 对比矩阵
  best_overall: string                    // 综合首选
  best_budget: string                    // 性价比首选
  expert_tips: string[]                   // 避雷建议
  overall_summary: string                 // 总结
}

// ============ 接口响应格式 ============
export interface ShoppingResponse {
  success: boolean
  message: string
  data?: ShoppingReport
}