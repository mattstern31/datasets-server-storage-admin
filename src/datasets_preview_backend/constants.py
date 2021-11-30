from typing import List

DEFAULT_APP_HOSTNAME: str = "localhost"
DEFAULT_APP_PORT: int = 8000
DEFAULT_ASSETS_DIRECTORY: None = None
DEFAULT_DATASETS_ENABLE_PRIVATE: bool = False
DEFAULT_DATASETS_REVISION: str = "master"
DEFAULT_EXTRACT_ROWS_LIMIT: int = 100
DEFAULT_LOG_LEVEL: str = "INFO"
DEFAULT_MAX_AGE_LONG_SECONDS: int = 21600  # 6 * 60 * 60 = 6 hours
DEFAULT_MAX_AGE_SHORT_SECONDS: int = 120  # 2 minutes
DEFAULT_MONGO_CACHE_DATABASE: str = "datasets_preview_cache"
DEFAULT_MONGO_QUEUE_DATABASE: str = "datasets_preview_queue"
DEFAULT_MONGO_URL: str = "mongodb://localhost:27018"
DEFAULT_WEB_CONCURRENCY: int = 2

DEFAULT_MAX_LOAD_PCT: int = 50
DEFAULT_MAX_MEMORY_PCT: int = 60
DEFAULT_WORKER_SLEEP_SECONDS: int = 5

DEFAULT_REFRESH_PCT: int = 1

DEFAULT_CONFIG_NAME: str = "default"
# these datasets take too much time, we block them beforehand
DATASETS_BLOCKLIST: List[str] = [
    "imthanhlv/binhvq_news21_raw",
    "SaulLu/Natural_Questions_HTML_Toy",
    "SaulLu/Natural_Questions_HTML_reduced_all",
    "z-uo/squad-it",
    "kiyoung2/aistage-mrc",
    "SaulLu/Natural_Questions_HTML",
]

FORCE_REDOWNLOAD: str = "force_redownload"
