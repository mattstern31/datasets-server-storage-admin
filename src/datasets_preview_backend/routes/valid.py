import logging
import time

from starlette.requests import Request
from starlette.responses import Response

from datasets_preview_backend.config import MAX_AGE_LONG_SECONDS
from datasets_preview_backend.exceptions import Status400Error, StatusError
from datasets_preview_backend.io.cache import (
    get_valid_or_stalled_dataset_names,
    is_dataset_name_valid_or_stalled,
)
from datasets_preview_backend.routes._utils import get_response

logger = logging.getLogger(__name__)


async def valid_datasets_endpoint(_: Request) -> Response:
    logger.info("/valid")
    content = {
        "valid": get_valid_or_stalled_dataset_names(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return get_response(content, 200, MAX_AGE_LONG_SECONDS)


async def is_valid_endpoint(request: Request) -> Response:
    dataset_name = request.query_params.get("dataset")
    logger.info(f"/is-valid, dataset={dataset_name}")
    try:
        if not isinstance(dataset_name, str):
            raise Status400Error("Parameter 'dataset' is required")
        content = {
            "valid": is_dataset_name_valid_or_stalled(dataset_name),
        }
        return get_response(content, 200, MAX_AGE_LONG_SECONDS)
    except StatusError as err:
        return get_response(err.as_content(), err.status_code, MAX_AGE_LONG_SECONDS)