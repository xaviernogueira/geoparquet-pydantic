import pytest
from pathlib import Path

# get the path to the data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def valid_geojson() -> Path:
    return TEST_DATA_DIR / "valid.geojson"


@pytest.fixture
def valid_geoparquet() -> Path:
    return TEST_DATA_DIR / "valid_geojson.parquet"
