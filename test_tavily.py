import traceback
import sys
import os

try:
    print("正在加载环境变量...")
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="backend/.env")
    
    key = os.getenv("TAVILY_API_KEY")
    print(f"读取到的 TAVILY_API_KEY 长度: {len(key) if key else 0}")
    
    from tavily import TavilyClient
    client = TavilyClient(api_key=key)
    
    print("开始调用 Tavily API...")
    res = client.search(query="主动降噪耳机 推荐 2026", include_images=True)
    print("🎉 调用成功！部分返回结果：")
    print(str(res)[:500])
except Exception as e:
    print("\n❌ 捕获到异常：")
    traceback.print_exc(file=sys.stdout)
