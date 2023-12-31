# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The HuggingFace Authors.

import time

from pytest import TempPathFactory

from cache_maintenance.clean_directory import clean_directory


def test_clean_directory(tmp_path_factory: TempPathFactory) -> None:
    hf_datasets_cache_directory = tmp_path_factory.mktemp("test_clean_directory") / "hf_datasets_cache"
    hf_datasets_cache_directory.mkdir(parents=True, exist_ok=True)
    expired_time_interval_seconds = 2

    test_dataset_cache = hf_datasets_cache_directory / "medium/datasets/test_dataset_cache"
    test_dataset_cache.mkdir(parents=True, exist_ok=True)
    cache_file = test_dataset_cache / "foo"
    cache_file.touch()

    # ensure file exists
    assert cache_file.is_file()
    folder_pattern = f"{hf_datasets_cache_directory}/*/datasets/*"
    # try to delete it inmediatly after creation, it should remain
    clean_directory(str(folder_pattern), expired_time_interval_seconds)
    assert cache_file.is_file()

    # try to delete it after more that time interval, it should be deleted
    cache_file.touch()
    time.sleep(expired_time_interval_seconds + 2)
    clean_directory(str(folder_pattern), expired_time_interval_seconds)
    assert not cache_file.is_file()
