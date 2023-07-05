# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 The HuggingFace Authors.

ASSETS_CACHE_APPNAME = "datasets_server_assets"
CACHE_COLLECTION_RESPONSES = "cachedResponsesBlue"
CACHE_MONGOENGINE_ALIAS = "cache"
CACHED_ASSETS_CACHE_APPNAME = "datasets_server_cached_assets"
PARQUET_METADATA_CACHE_APPNAME = "datasets_server_parquet_metadata"
DUCKDB_INDEX_CACHE_APPNAME = "datasets_server_duckdb_index"
METRICS_COLLECTION_CACHE_TOTAL_METRIC = "cacheTotalMetric"
METRICS_COLLECTION_JOB_TOTAL_METRIC = "jobTotalMetric"
METRICS_MONGOENGINE_ALIAS = "metrics"
QUEUE_COLLECTION_JOBS = "jobsBlue"
QUEUE_COLLECTION_LOCKS = "locks"
QUEUE_MONGOENGINE_ALIAS = "queue"
QUEUE_TTL_SECONDS = 600  # 10 minutes

DEFAULT_DIFFICULTY = 50
DEFAULT_INPUT_TYPE = "dataset"
DEFAULT_JOB_RUNNER_VERSION = 1
PROCESSING_STEP_CONFIG_INFO_VERSION = 2
PROCESSING_STEP_CONFIG_OPT_IN_OUT_URLS_COUNT_VERSION = 3
PROCESSING_STEP_CONFIG_PARQUET_AND_INFO_VERSION = 3
PROCESSING_STEP_CONFIG_PARQUET_METADATA_VERSION = 1
PROCESSING_STEP_CONFIG_PARQUET_VERSION = 5
PROCESSING_STEP_CONFIG_SIZE_VERSION = 2
PROCESSING_STEP_CONFIG_SPLIT_NAMES_FROM_INFO_VERSION = 3
PROCESSING_STEP_CONFIG_SPLIT_NAMES_FROM_STREAMING_VERSION = 3
PROCESSING_STEP_DATASET_CONFIG_NAMES_VERSION = 1
PROCESSING_STEP_DATASET_INFO_VERSION = 2
PROCESSING_STEP_DATASET_IS_VALID_VERSION = 4
PROCESSING_STEP_DATASET_OPT_IN_OUT_URLS_COUNT_VERSION = 2
PROCESSING_STEP_DATASET_PARQUET_VERSION = 2
PROCESSING_STEP_DATASET_SIZE_VERSION = 2
PROCESSING_STEP_DATASET_SPLIT_NAMES_VERSION = 3
PROCESSING_STEP_SPLIT_DUCKDB_INDEX_VERSION = 1
PROCESSING_STEP_SPLIT_FIRST_ROWS_FROM_PARQUET_VERSION = 2
PROCESSING_STEP_SPLIT_FIRST_ROWS_FROM_STREAMING_VERSION = 3
PROCESSING_STEP_SPLIT_IMAGE_URL_COLUMNS_VERSION = 1
PROCESSING_STEP_SPLIT_OPT_IN_OUT_URLS_COUNT_VERSION = 2
PROCESSING_STEP_SPLIT_OPT_IN_OUT_URLS_SCAN_VERSION = 4

PROCESSING_STEP_CONFIG_PARQUET_AND_INFO_ROW_GROUP_SIZE_FOR_AUDIO_DATASETS = 100
PROCESSING_STEP_CONFIG_PARQUET_AND_INFO_ROW_GROUP_SIZE_FOR_IMAGE_DATASETS = 100
PROCESSING_STEP_CONFIG_PARQUET_AND_INFO_ROW_GROUP_SIZE_FOR_BINARY_DATASETS = 100
PARQUET_REVISION = "refs/convert/parquet"

ERROR_CODES_TO_RETRY = "CreateCommitError,LockedDatasetTimeoutError"
