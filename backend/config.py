from dotenv import load_dotenv
import os

_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_env_path)

OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "big-pickle")
OPENCODE_URL = os.getenv("OPENCODE_URL", "https://opencode.ai/zen/v1/chat/completions")

MAX_FILE_SIZE_MB = 20
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
DATASET_TTL_SECONDS = 3600
