# SPDX-License-Identifier: Apache-2.0
# Copyright 2022 The HuggingFace Authors.

import logging
from http import HTTPStatus
from typing import Any, List, Literal, Mapping, Optional

from libcommon.constants import (
    PROCESSING_STEP_SPLIT_NAMES_FROM_DATASET_INFO_VERSION,
    PROCESSING_STEP_SPLIT_NAMES_FROM_STREAMING_VERSION,
)
from libcommon.dataset import DatasetNotFoundError
from libcommon.simple_cache import (
    DoesNotExist,
    SplitFullName,
    get_response,
    get_response_without_content,
)

from worker.job_runner import CompleteJobResult, JobRunnerError
from worker.job_runners._datasets_based_job_runner import DatasetsBasedJobRunner
from worker.utils import SplitItem, SplitsList

SplitNamesFromDatasetInfoJobRunnerErrorCode = Literal[
    "PreviousStepStatusError",
    "PreviousStepFormatError",
    "ResponseAlreadyComputedError",
]


class SplitNamesFromDatasetInfoJobRunnerError(JobRunnerError):
    """Base class for split names job runner exceptions."""

    def __init__(
        self,
        message: str,
        status_code: HTTPStatus,
        code: SplitNamesFromDatasetInfoJobRunnerErrorCode,
        cause: Optional[BaseException] = None,
        disclose_cause: bool = False,
    ):
        super().__init__(
            message=message, status_code=status_code, code=code, cause=cause, disclose_cause=disclose_cause
        )


class PreviousStepStatusError(SplitNamesFromDatasetInfoJobRunnerError):
    """Raised when the previous step gave an error. The job should not have been created."""

    def __init__(self, message: str, cause: Optional[BaseException] = None):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR, "PreviousStepStatusError", cause, False)


class PreviousStepFormatError(SplitNamesFromDatasetInfoJobRunnerError):
    """Raised when the content of the previous step has not the expected format."""

    def __init__(self, message: str, cause: Optional[BaseException] = None):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR, "PreviousStepFormatError", cause, False)


class ResponseAlreadyComputedError(SplitNamesFromDatasetInfoJobRunnerError):
    """Raised when reponse has been already computed by /split-names-from-streaming job runner."""

    def __init__(self, message: str, cause: Optional[BaseException] = None):
        super().__init__(message, HTTPStatus.INTERNAL_SERVER_ERROR, "ResponseAlreadyComputedError", cause, True)


def compute_split_names_from_dataset_info_response(
    dataset: str, config: str, dataset_git_revision: Optional[str]
) -> SplitsList:
    """
    Get the response of /split-names-from-dataset-info for one specific dataset and config on huggingface.co
    computed from cached response in dataset-info step.

    The /split-names-from-dataset-info response generated by this function does not include stats about the split,
    like the size or number of samples. See dataset-info or dataset-size for that.

    Args:
        dataset (`str`):
            A namespace (user or an organization) and a repo name separated
            by a `/`.
        config (`str`):
            A configuration name.
    Returns:
        `SplitsList`: An object with the list of split names for the dataset and config.
    <Tip>
    Raises the following errors:
        - [`~job_runners.split_names_from_dataset_info.PreviousStepStatusError`]
          If the the previous step gave an error.
        - [`~job_runners.split_names_from_dataset_info.PreviousStepFormatError`]
            If the content of the previous step has not the expected format
        - [`~libcommon.dataset.DatasetNotFoundError`]
            If previous step content was not found for the dataset
        - [`~job_runners.split_names_from_dataset_info.ResponseAlreadyComputedError`]
          If reponse has been already computed by /split-names-from-streaming job runner.
    </Tip>
    """
    logging.info(f"get split names from dataset info for dataset={dataset}, config={config}")
    try:
        streaming_response = get_response_without_content(
            kind="/split-names-from-streaming", dataset=dataset, config=config
        )
        if (
            streaming_response["http_status"] == HTTPStatus.OK
            and streaming_response["job_runner_version"] == PROCESSING_STEP_SPLIT_NAMES_FROM_STREAMING_VERSION
            and streaming_response["progress"] == 1.0  # completed response
            and dataset_git_revision is not None
            and streaming_response["dataset_git_revision"] == dataset_git_revision
        ):
            raise ResponseAlreadyComputedError(
                "Response has already been computed by /split-names-from-streaming. Compute will be skipped."
            )
    except DoesNotExist:
        logging.debug("no cache found for /split-names-from-streaming, will proceed to compute from config-info")
    try:
        response = get_response(kind="config-info", dataset=dataset)
    except DoesNotExist as e:
        raise DatasetNotFoundError("No response found in previous step for this dataset: 'config-info'.", e) from e
    if response["http_status"] != HTTPStatus.OK:
        raise PreviousStepStatusError(
            f"Previous step gave an error: {response['http_status']}. This job should not have been created."
        )

    try:
        splits_content = response["content"]["dataset_info"]["splits"]
    except Exception as e:
        raise PreviousStepFormatError("Previous step 'config-info' did not return the expected content.") from e

    split_name_items: List[SplitItem] = [
        {"dataset": dataset, "config": config, "split": str(split)} for split in splits_content
    ]

    return SplitsList(splits=split_name_items)


class SplitNamesFromDatasetInfoJobRunner(DatasetsBasedJobRunner):
    @staticmethod
    def get_job_type() -> str:
        return "/split-names-from-dataset-info"

    @staticmethod
    def get_job_runner_version() -> int:
        return PROCESSING_STEP_SPLIT_NAMES_FROM_DATASET_INFO_VERSION

    def compute(self) -> CompleteJobResult:
        if self.dataset is None:
            raise ValueError("dataset is required")
        if self.config is None:
            raise ValueError("config is required")
        dataset_git_revision = self.get_dataset_git_revision()
        return CompleteJobResult(
            compute_split_names_from_dataset_info_response(
                dataset=self.dataset, config=self.config, dataset_git_revision=dataset_git_revision
            )
        )

    def get_new_splits(self, content: Mapping[str, Any]) -> set[SplitFullName]:
        """Get the set of new splits, from the content created by the compute."""
        return {SplitFullName(dataset=s["dataset"], config=s["config"], split=s["split"]) for s in content["splits"]}
