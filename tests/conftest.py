import pytest
import json
import pyarrow
from pathlib import Path
from geojson_pydantic.features import FeatureCollection

# get the path to the data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def valid_geojson_file() -> Path:
    valid_geojson = TEST_DATA_DIR / "valid.geojson"
    assert valid_geojson.exists()
    return valid_geojson


@pytest.fixture
def valid_geojson_obj(valid_geojson_file) -> FeatureCollection:
    return FeatureCollection(**json.load(open(valid_geojson_file, "r")))


@pytest.fixture
def valid_geoparquet_file() -> Path:
    valid_geoparquet = TEST_DATA_DIR / "valid_geojson.parquet"
    assert valid_geoparquet.exists()
    return valid_geoparquet


@pytest.fixture
def valid_geoparquet_table(valid_geoparquet_file) -> pyarrow.Table:
    return pyarrow.parquet.read_table(valid_geoparquet_file)
