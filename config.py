"""项目全局配置：品类、平台、路径与抓取参数。"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 目标品类与平台
CATEGORIES = ["polo衫", "牛仔裤"]
PLATFORMS = ["淘宝", "拼多多", "抖音"]

# 目录
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
REPORT_PATH = os.path.join(BASE_DIR, "output", "report.md")

# SQLite 数据库（清洗后入库）
DB_PATH = os.path.join(PROCESSED_DIR, "ecommerce_prices.db")

# 抓取参数
REQUEST_TIMEOUT = 8          # 秒
RETRY_TIMES = 2
REQUEST_INTERVAL = 1.0       # 限流间隔（秒）
MIN_SKUS_PER_GROUP = 15      # 每个「平台 × 品类」目标 SKU 数

# 备用数据（真实抓取被拦截时的兜底，标记为 reference）
FALLBACK_SEED = 42

# MySQL 连接（专用分析账号，只授权本项目库；建库请用 sql/01_create_schema.sql + root）
MYSQL = {
    "host": "localhost",
    "port": 3306,
    "user": "ecom_user",
    "password": "ecom_pass_2026",
    "database": "ecommerce_prices",
    "charset": "utf8mb4",
}
