import pytest
from pyproj import CRS
from geoparquet_pydantic.schemas import (
    GeometryColumnMetadata,
    GeoParquetMetadata,
)


@pytest.fixture
def good_geo_column_metadata():
    return {
        "encoding": "WKB",
        "geometry_types": ["Point"],
        "crs": "OGC:CRS84",
        "edges": "planar",
        "bbox": [0, 0, 25, 25],
        "epoch": None,
        "orientation": "counterclockwise",
    }


def test_good_geo_column_metadata(good_geo_column_metadata):
    metadata = GeometryColumnMetadata(**good_geo_column_metadata)
    assert metadata.encoding == good_geo_column_metadata["encoding"]
    assert metadata.geometry_types == good_geo_column_metadata["geometry_types"]
    assert metadata.crs != good_geo_column_metadata["crs"]
    assert CRS.from_json(metadata.crs).to_string() == good_geo_column_metadata["crs"]
    assert metadata.edges == good_geo_column_metadata["edges"]
    assert metadata.bbox == good_geo_column_metadata["bbox"]
    assert metadata.epoch == None
    assert metadata.orientation == good_geo_column_metadata["orientation"]


def test_bad_geo_column_metadata(good_geo_column_metadata):
    """Test that the GeoColumnMetadata raises an error when given bad data."""

    # Test bad encoding
    bad_encoding = good_geo_column_metadata.copy()
    bad_encoding["encoding"] = "WKT"
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_encoding)

    # Test bad geometry types
    bad_geometry_types = good_geo_column_metadata.copy()
    bad_geometry_types["geometry_types"] = ["NOT_A_REAL_TIME"]
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_geometry_types)

    # Test bad CRS
    bad_crs = good_geo_column_metadata.copy()
    bad_crs["crs"] = "NOT_A_REAL_CRS"
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_crs)

    # Test bad edges
    bad_edges = good_geo_column_metadata.copy()
    bad_edges["edges"] = "NOT_A_REAL_EDGE"
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_edges)

    # Test bad bbox
    bad_bbox = good_geo_column_metadata.copy()
    bad_bbox["bbox"] = [0, 0, 25]
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_bbox)

    # Test bad epoch
    bad_epoch = good_geo_column_metadata.copy()
    bad_epoch["epoch"] = "NOT_A_REAL_EPOCH"
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_epoch)

    # Test bad orientation
    bad_orientation = good_geo_column_metadata.copy()
    bad_orientation["orientation"] = "NOT_A_REAL_ORIENTATION"
    with pytest.raises(ValueError):
        GeometryColumnMetadata(**bad_orientation)


def test_good_geoparquet(good_geo_column_metadata):

    # minimum inputs
    geo_parquet = GeoParquetMetadata(
        columns={"geometry": GeometryColumnMetadata(**good_geo_column_metadata)},
    )
    assert geo_parquet.version == "1.1.0-dev"
    assert geo_parquet.primary_column == "geometry"
    assert isinstance(geo_parquet.columns, dict)
    assert len(geo_parquet.columns) == 1
    assert "geometry" in geo_parquet.columns
    assert isinstance(geo_parquet.columns["geometry"], GeometryColumnMetadata)

    # maximum inputs
    geo_parquet = GeoParquetMetadata(
        version="1.0.0",
        primary_column="geom",
        columns={"geom": GeometryColumnMetadata(**good_geo_column_metadata)},
    )
    assert geo_parquet.version == "1.0.0"
    assert geo_parquet.primary_column == "geom"
    assert isinstance(geo_parquet.columns, dict)
    assert len(geo_parquet.columns) == 1
    assert "geom" in geo_parquet.columns
    assert isinstance(geo_parquet.columns["geom"], GeometryColumnMetadata)


def test_bad_geoparquet(good_geo_column_metadata):

    # Test bad version
    with pytest.raises(ValueError):
        GeoParquetMetadata(
            version=1.431243,
            columns={"geometry": GeometryColumnMetadata(**good_geo_column_metadata)},
        )

    # Test bad primary_column
    with pytest.raises(ValueError):
        GeoParquetMetadata(
            primary_column=1.431243,
            columns={"geometry": GeometryColumnMetadata(**good_geo_column_metadata)},
        )

    # Test bad columns
    with pytest.raises(ValueError):
        GeoParquetMetadata(
            columns={"geometry": "NOT_A_REAL_METADATA"},
        )
    with pytest.raises(ValueError):
        GeoParquetMetadata(
            columns="NOT_EVEN_A_DICT",
        )
    with pytest.raises(ValueError):
        GeoParquetMetadata(
            columns={"geometry": {"A_DICT": "BUT_NOT_VALID"}},
        )

    # Test missing primary_column
    with pytest.raises(ValueError):
        GeoParquetMetadata(
            primary_column="NOT_A_REAL_COLUMN",
            columns={"geometry": GeometryColumnMetadata(**good_geo_column_metadata)},
        )
