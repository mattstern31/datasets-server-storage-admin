from dataclasses import asdict
from typing import Optional

from datasets import get_dataset_infos

from datasets_preview_backend.exceptions import Status400Error, Status404Error


def get_info(dataset: str, use_auth_token: Optional[str] = None):
    if not isinstance(dataset, str) and dataset is not None:
        raise TypeError("dataset argument should be a string")
    if dataset is None:
        raise Status400Error("'dataset' is a required query parameter.")
    try:
        total_dataset_infos = get_dataset_infos(dataset, use_auth_token=use_auth_token)
        info = {config_name: asdict(config_info) for config_name, config_info in total_dataset_infos.items()}
    except FileNotFoundError as err:
        raise Status404Error("The dataset info could not be found.") from err
    except Exception as err:
        raise Status400Error("The dataset info could not be parsed from the dataset.") from err

    return {"dataset": dataset, "info": info}
