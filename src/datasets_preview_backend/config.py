import os

from datasets_preview_backend.constants import (
    DEFAULT_EXTRACT_ROWS_LIMIT,
    DEFAULT_HOSTNAME,
    DEFAULT_PORT,
)
from datasets_preview_backend.utils import get_int_value

HOSTNAME = os.environ.get("HOSTNAME", DEFAULT_HOSTNAME)
PORT = get_int_value(d=os.environ, key="PORT", default=DEFAULT_PORT)
EXTRACT_ROWS_LIMIT = get_int_value(d=os.environ, key="EXTRACT_ROWS_LIMIT", default=DEFAULT_EXTRACT_ROWS_LIMIT)
