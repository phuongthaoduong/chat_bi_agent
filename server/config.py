import os

from dotenv import load_dotenv

# Load .env file if present (local dev). In production, set env vars directly.
load_dotenv(override=True)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_SESSIONS = 50
SESSION_TTL_MINUTES = 30
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
