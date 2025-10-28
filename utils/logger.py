import os
import logging

# 取得 main.py 所在目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))  # 回到 project root
LOG_PATH = os.path.join(BASE_DIR, "tech_agent.log")


class SuppressGoogleAuthInfoFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "The user provided Google Cloud credentials" not in record.getMessage()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

for handler in logging.getLogger().handlers:
    handler.addFilter(SuppressGoogleAuthInfoFilter())

# 避免過多日誌訊息
for noisy_logger in [
    "azure.core.pipeline.policies.http_logging_policy",
    "azure.core.pipeline",
    "azure.cosmos",
    "azure.identity",
    "azure",
    "openai",
    "httpx",
    "google.auth", 
    "google.auth._default",
    "google.genai",
    "google.api_core.client_info",
    "google.api_core.bidi",            
    "google.cloud",
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# 提供共用 logger
logger = logging.getLogger(__name__)
