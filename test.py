from backend.app.agents.shopping_guide_agent import get_shopping_advisor_agent
from backend.app.models.schemas import ShoppingRequest

# 模拟一个用户请求
req = ShoppingRequest(
    product_category="主动降噪耳机",
    budget_range={"min": 1000, "max": 3000},
    usage_scenarios=["办公室", "长途飞行"],
    brand_preference=[],
    core_features=["降噪强", "佩戴舒适"],
    free_text_input=""
)

# 运行 Agent
advisor = get_shopping_advisor_agent()
report = advisor.generate_shopping_report(req)

print(f"推荐的首选型号是: {report.best_overall}")