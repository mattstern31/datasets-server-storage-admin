from typing import Any, List

import numpy  # type: ignore
from PIL import Image  # type: ignore

from datasets_preview_backend.io.asset import create_image_file
from datasets_preview_backend.models.column.default import (
    Cell,
    CellTypeError,
    Column,
    ColumnInferenceError,
    ColumnType,
    ColumnTypeError,
    check_feature_type,
)

COLUMN_NAMES = ["image"]


def check_value(value: Any) -> None:
    if value is not None and (
        not isinstance(value, list)
        or len(value) == 0
        or not isinstance(value[0], list)
        or len(value[0]) == 0
        or type(value[0][0]) != int
    ):
        raise CellTypeError("value must contain 2D array of integers")


def check_values(values: List[Any]) -> None:
    for value in values:
        check_value(value)
    if values and all(value is None for value in values):
        raise ColumnInferenceError("all the values are None, cannot infer column type")


class ImageArray2DColumn(Column):
    def __init__(self, name: str, feature: Any, values: List[Any]):
        if name not in COLUMN_NAMES:
            raise ColumnTypeError("feature name mismatch")
        if feature:
            try:
                check_feature_type(feature, "Array2D", ["uint8"])
            except Exception:
                raise ColumnTypeError("feature type mismatch")
        # else: we can infer from values
        check_values(values)
        # we also have shape in the feature: shape: [28, 28] for MNIST
        self.name = name
        self.type = ColumnType.RELATIVE_IMAGE_URL

    def get_cell_value(self, dataset_name: str, config_name: str, split_name: str, row_idx: int, value: Any) -> Cell:
        check_value(value)
        array = 255 - numpy.asarray(value, dtype=numpy.uint8)  # TODO: OK for MNIST, but for the rest?
        mode = "L"
        image = Image.fromarray(array, mode)
        filename = "image.jpg"

        return create_image_file(dataset_name, config_name, split_name, row_idx, self.name, filename, image)
