import pytest

from datasets_preview_backend.constants import DEFAULT_CONFIG_NAME
from datasets_preview_backend.queries.info import (
    Status400Error,
    Status404Error,
    get_info,
)


def test_get_info():
    dataset = "glue"
    response = get_info(dataset)
    assert "dataset" in response
    assert response["dataset"] == dataset
    assert "info" in response
    info = response["info"]
    assert len(list(info.keys())) == 12
    assert "cola" in info


def test_default_config():
    dataset = "acronym_identification"
    response = get_info(dataset)
    assert DEFAULT_CONFIG_NAME in response["info"]
    assert response["info"][DEFAULT_CONFIG_NAME]["config_name"] == DEFAULT_CONFIG_NAME


def test_missing_argument():
    with pytest.raises(Status400Error):
        get_info(None)


def test_bad_type_argument():
    with pytest.raises(TypeError):
        get_info()
    with pytest.raises(TypeError):
        get_info(1)


def test_script_error():
    # raises "ModuleNotFoundError: No module named 'datasets_modules.datasets.br-quad-2'", which should be caught and raised as DatasetBuilderScriptError
    with pytest.raises(Status400Error):
        get_info("piEsposito/br-quad-2.0")


def test_no_dataset():
    # the dataset does not exist
    with pytest.raises(Status404Error):
        get_info("doesnotexist")


def test_no_dataset_no_script():
    # the dataset does not contain a script
    with pytest.raises(Status404Error):
        get_info("AConsApart/anime_subtitles_DialoGPT")
    # raises "ModuleNotFoundError: No module named 'datasets_modules.datasets.Test'", which should be caught and raised as DatasetBuilderScriptError
    with pytest.raises(Status404Error):
        get_info("TimTreasure4/Test")


def test_no_dataset_bad_script_name():
    # the dataset script name is incorrect
    with pytest.raises(Status404Error):
        get_info("Cropinky/rap_lyrics_english")
