import os

from dotenv import load_dotenv

from datasets_preview_backend.constants import (
    DEFAULT_APP_HOSTNAME,
    DEFAULT_APP_PORT,
    DEFAULT_EXTRACT_ROWS_LIMIT,
    DEFAULT_HF_TOKEN,
    DEFAULT_LOG_LEVEL,
)
from datasets_preview_backend.utils import get_int_value, get_str_value

# Load environment variables defined in .env, if any
load_dotenv()

APP_HOSTNAME = os.environ.get("APP_HOSTNAME", DEFAULT_APP_HOSTNAME)
APP_PORT = get_int_value(d=os.environ, key="APP_PORT", default=DEFAULT_APP_PORT)
EXTRACT_ROWS_LIMIT = get_int_value(d=os.environ, key="EXTRACT_ROWS_LIMIT", default=DEFAULT_EXTRACT_ROWS_LIMIT)
HF_TOKEN = get_str_value(d=os.environ, key="HF_TOKEN", default=DEFAULT_HF_TOKEN)
LOG_LEVEL = get_str_value(d=os.environ, key="LOG_LEVEL", default=DEFAULT_LOG_LEVEL)
