import os

from dotenv import load_dotenv

# Load .env file if present (local dev). In production, set env vars directly.
load_dotenv()

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_SESSIONS = 50
SESSION_TTL_MINUTES = 30
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
QWEN_BASE_URL = os.environ.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-plus")
