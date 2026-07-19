import logging
import os

# 1. 自动定位目录：确保无论你在哪启动，路径都对
# 获取当前文件 (logger.py) 所在的 backend 目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# 2. 强力创建目录：如果 logs 文件夹不存在，直接建一个
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 3. 配置日志格式
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

# 获取主记录器
logger = logging.getLogger("shopping-assistant")
logger.setLevel(logging.INFO)

# --- 关键：配置输出到控制台 ---
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# --- 关键：配置输出到文件 ---
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 这一步是为了防止日志重复打印
logger.propagate = False