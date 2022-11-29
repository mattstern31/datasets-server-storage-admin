# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 The HuggingFace Authors.

import logging
import os
from typing import Optional

from appdirs import user_cache_dir  # type:ignore

DATASET_SEPARATOR = "--"
ASSET_DIR_MODE = 0o755


def init_assets_dir(assets_directory: Optional[str] = None) -> str:
    # set it to the default cache location on the machine, if ASSETS_DIRECTORY is null
    if assets_directory is None:
        assets_directory = user_cache_dir("datasets_server_assets")
    os.makedirs(assets_directory, exist_ok=True)
    logging.info(f"Assets directory: {assets_directory}")
    return assets_directory