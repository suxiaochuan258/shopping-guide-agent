"""启动脚本"""

import sys
import os
# 将 hello-agents 仓库的根目录添加到路径中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
