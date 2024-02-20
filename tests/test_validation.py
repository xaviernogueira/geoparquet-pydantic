import pyarrow
import pytest
from pathlib import Path
from geoparquet_pydantic.validate import (
    validate_geoparquet_table,
    validate_geoparquet_file,
)


@pytest.fixture
def no_geo_metadata_table() -> pyarrow.Table:
    return pyarrow.Table.from_pydict(
        {
            "geometry": [None],
            "id": [1],
        },
        metadata={"NOTGEO": "metadata"},
    )


@pytest.fixture
def bad_geo_metadata_table() -> pyarrow.Table:
    return pyarrow.Table.from_pydict(
        {
            "geometry": [None],
            "id": [1],
        },
        metadata={
            b"geo": b"{'version': '1.1.0-dev', 'primary_column': 'geometry', 'columns': {'geometry': 'not-a-geometry'}}"
        },
    )


def test_valididate_geoparquet_table(valid_geoparquet_table):
    """Test the validation of a valid GeoParquet table."""
    assert validate_geoparquet_table(valid_geoparquet_table)


def test_invalid_geoparquet_table(no_geo_metadata_table, bad_geo_metadata_table):
    """Test the validation of an invalid GeoParquet table."""
    assert validate_geoparquet_table(no_geo_metadata_table) == False
    assert validate_geoparquet_table(bad_geo_metadata_table) == False


def test_valid_geoparquet_file(valid_geoparquet_file: Path):
    """Test the validation of a valid GeoParquet file."""
    assert validate_geoparquet_file(valid_geoparquet_file)
    assert validate_geoparquet_file(str(valid_geoparquet_file))
    assert validate_geoparquet_file(
        pyarrow.parquet.ParquetFile(valid_geoparquet_file),
    )


def test_invalid_geoparquet_file(no_geo_metadata_table, bad_geo_metadata_table):
    """Test the validation of an invalid GeoParquet file."""
    pyarrow.parquet.write_table(no_geo_metadata_table, "test1.parquet")
    assert validate_geoparquet_file("test1.parquet") == False
    Path("test1.parquet").unlink()

    pyarrow.parquet.write_table(no_geo_metadata_table, "test2.parquet")
    assert validate_geoparquet_file("test2.parquet") == False
    Path("test2.parquet").unlink()
