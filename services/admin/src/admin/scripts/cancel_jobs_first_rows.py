# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 The HuggingFace Authors.

import logging

from libcommon.logger import init_logger
from libqueue.queue import Queue, connect_to_queue

from admin.config import AppConfig
from admin.utils import JobType

if __name__ == "__main__":
    app_config = AppConfig()
    init_logger(app_config.common.log_level, "cancel_jobs_first_rows")
    logger = logging.getLogger("cancel_jobs_first_rows")
    connect_to_queue(database=app_config.queue.mongo_database, host=app_config.cache.mongo_url)
    Queue(type=JobType.FIRST_ROWS.value).cancel_started_jobs()
    logger.info("all the started jobs in the first_rows/ queue have been cancelled and re-enqueued")
