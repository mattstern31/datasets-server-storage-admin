from dataclasses import asdict
from typing import Any, Dict, List, Optional, TypedDict

from datasets import load_dataset_builder

from datasets_preview_backend.cache import cache, memoize  # type: ignore
from datasets_preview_backend.constants import DATASETS_BLOCKLIST
from datasets_preview_backend.exceptions import Status400Error, Status404Error
from datasets_preview_backend.queries.configs import get_configs


class InfoItem(TypedDict):
    dataset: str
    config: str
    info: Dict[str, Any]


class InfosContent(TypedDict):
    infos: List[InfoItem]


def get_info_items(dataset: str, config: str) -> List[InfoItem]:
    try:
        # TODO: use get_dataset_infos if https://github.com/huggingface/datasets/issues/3013 is fixed
        builder = load_dataset_builder(dataset, name=config)
        info = asdict(builder.info)
        if "splits" in info and info["splits"] is not None:
            info["splits"] = {split_name: split_info for split_name, split_info in info["splits"].items()}
    except FileNotFoundError as err:
        raise Status404Error("The config info could not be found.", err)
    except Exception as err:
        raise Status400Error("The config info could not be parsed from the dataset.", err)
    return [{"dataset": dataset, "config": config, "info": info}]


@memoize(cache)  # type:ignore
def get_infos(*, dataset: str, config: Optional[str] = None) -> InfosContent:
    if not isinstance(dataset, str) and dataset is not None:
        raise TypeError("dataset argument should be a string")
    if dataset is None:
        raise Status400Error("'dataset' is a required query parameter.")
    if dataset in DATASETS_BLOCKLIST:
        raise Status400Error("this dataset is not supported for now.")
    if config is not None and not isinstance(config, str):
        raise TypeError("config argument should be a string")

    if config is None:
        # recurse to get cached entries
        info_items = [
            info_item
            for config_item in get_configs(dataset=dataset)["configs"]
            for info_item in get_infos(dataset=dataset, config=config_item["config"])["infos"]
        ]
    else:
        info_items = get_info_items(dataset, config)

    return {"infos": info_items}
