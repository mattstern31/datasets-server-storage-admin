from typing import List, TypedDict

from datasets import get_dataset_config_names

from datasets_preview_backend.cache import cache, memoize  # type: ignore
from datasets_preview_backend.constants import DATASETS_BLOCKLIST, DEFAULT_CONFIG_NAME
from datasets_preview_backend.exceptions import Status400Error, Status404Error


class ConfigItem(TypedDict):
    dataset: str
    config: str


class ConfigsContent(TypedDict):
    configs: List[ConfigItem]


def get_config_items(dataset: str) -> List[ConfigItem]:
    try:
        configs = get_dataset_config_names(dataset)
        if len(configs) == 0:
            configs = [DEFAULT_CONFIG_NAME]
    except FileNotFoundError as err:
        raise Status404Error("The dataset could not be found.", err)
    except Exception as err:
        raise Status400Error("The config names could not be parsed from the dataset.", err)
    return [{"dataset": dataset, "config": d} for d in configs]


@memoize(cache)  # type:ignore
def get_configs(*, dataset: str) -> ConfigsContent:
    if not isinstance(dataset, str) and dataset is not None:
        raise TypeError("dataset argument should be a string")
    if dataset is None:
        raise Status400Error("'dataset' is a required query parameter.")
    if dataset in DATASETS_BLOCKLIST:
        raise Status400Error("this dataset is not supported for now.")

    config_items = get_config_items(dataset)

    return {"configs": config_items}
