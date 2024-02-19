import pytest
import json
import pyarrow
from pathlib import Path
import geojson_pydantic
import geopandas as gpd
import pyarrow.parquet
from geojson_pydantic.features import FeatureCollection

from geoparquet_pydantic.schemas import (
    GeoParquetMetadata,
)
from geoparquet_pydantic.convert import (
    _to_wkb,
    _get_geom_types,
    _get_default_geo_metadata,
    _update_metadata,
    _validate_column_schema,
    geojson_to_geoparquet,
    geoparquet_to_geojson,
)
import shapely

from geoparquet_pydantic.validate import validate_geoparquet_file


@pytest.fixture
def geometry_type_examples(
    valid_geojson_obj: FeatureCollection,
) -> dict[str, geojson_pydantic.geometries._GeometryBase]:
    geometry_types = {}
    for feature in valid_geojson_obj.features:
        if feature.geometry.type not in geometry_types:
            geometry_types[feature.geometry.type] = feature.geometry
    assert len(geometry_types) == 7
    for k, v in geometry_types.items():
        assert isinstance(v, getattr(geojson_pydantic.geometries, k))

    return geometry_types


@pytest.fixture
def mock_table() -> pyarrow.Table:
    table_dict = {
        "col1": [1, 2, 3],
        "col2": [4, 5, 6],
    }
    metadata = {b"key": b"value"}
    table = pyarrow.Table.from_pydict(table_dict, metadata=metadata)
    assert isinstance(table, pyarrow.Table)
    assert table.schema.metadata == metadata
    return table


def test_to_wkb(
    geometry_type_examples: dict[str, geojson_pydantic.geometries._GeometryBase]
):
    """Test the conversion of a GeoJSON object to WKB format."""
    for k, v in geometry_type_examples.items():
        wkb = _to_wkb(v)
        assert isinstance(wkb, bytes)
        assert len(wkb) > 0
        back_in = shapely.wkb.loads(wkb)
        assert isinstance(back_in, getattr(shapely.geometry, k))


def test_get_geom_types(
    valid_geojson_obj: FeatureCollection,
):
    """Test the extraction of unique geometry types from a GeoJSON object."""
    geom_types = _get_geom_types(valid_geojson_obj.features)
    assert isinstance(geom_types, list)
    assert len(geom_types) == 7
    assert set(geom_types) == {
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    }


def test_get_default_geo_metadata(
    valid_geojson_obj: FeatureCollection,
):
    default_metadata = _get_default_geo_metadata(valid_geojson_obj)
    assert isinstance(default_metadata, GeoParquetMetadata)
    assert default_metadata.columns["geometry"].geometry_types == _get_geom_types(
        valid_geojson_obj.features
    )


def test_update_metadata(
    mock_table: pyarrow.Table,
):
    new_metadata = {"new_key": "new_value"}
    new_table = _update_metadata(mock_table, new_metadata)
    assert isinstance(new_table, pyarrow.Table)
    assert b"new_key" in new_table.schema.metadata
    assert b"key" in new_table.schema.metadata


def test_validate_column_schema(
    valid_geojson_obj: FeatureCollection,
):
    # make updated FeatureCollection properties
    for i, feature in enumerate(valid_geojson_obj.features):
        feature.properties["number"] = i
    mock_schema = pyarrow.schema(
        [
            ("geometry", pyarrow.binary()),
            ("name", pyarrow.string()),
            ("number", pyarrow.int64()),
        ]
    )
    # test with valid schema
    _validate_column_schema(
        mock_schema,
        primary_column="geometry",
        geojson=valid_geojson_obj,
        add_none_values=False,
    )
    _validate_column_schema(
        mock_schema,
        primary_column="geometry",
        geojson=valid_geojson_obj,
        add_none_values=True,
    )

    # test with invalid schema
    for i, feature in enumerate(valid_geojson_obj.features):
        if i % 2 == 0:
            feature.properties = {}
            assert not feature.properties
    with pytest.raises(ValueError):
        _validate_column_schema(
            mock_schema,
            "geometry",
            valid_geojson_obj,
            False,
        )

    # now test that it can add Nones
    _validate_column_schema(
        mock_schema,
        "geometry",
        valid_geojson_obj,
        True,
    )


def test_geojson_to_geoparquet(
    valid_geojson_obj: FeatureCollection,
):
    """Test the conversion of a valid GeoJSON file and pydantic object to a valid GeoParquet table."""

    # convert the GeoJSON object to a GeoParquet table with minimal optional
    table = geojson_to_geoparquet(valid_geojson_obj)
    assert isinstance(table, pyarrow.Table)
    table.validate(full=True)
    table_dict = table.to_pydict()
    assert "geometry" in table_dict
    assert len(table_dict["geometry"]) == len(valid_geojson_obj.features)
    assert "properties" in table_dict
    assert (
        json.loads(table_dict["properties"][0])
        == valid_geojson_obj.features[0].properties
    )

    parquet_path = Path("test.parquet")
    pyarrow.parquet.write_table(table, parquet_path)
    assert parquet_path.exists()
    gdf = gpd.read_parquet(parquet_path)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs.to_string() == "OGC:CRS84"
    assert len(gdf) == len(valid_geojson_obj.features)
    parquet_path.unlink()

    # try again with more arguments
    metadata = _get_default_geo_metadata(valid_geojson_obj)
    table = geojson_to_geoparquet(
        valid_geojson_obj,
        geo_metadata=metadata,
        column_schema=pyarrow.schema(
            [
                ("geometry", pyarrow.binary()),
                ("name", pyarrow.string()),
            ]
        ),
    )
    assert isinstance(table, pyarrow.Table)
    table.validate(full=True)
    table_dict = table.to_pydict()
    assert "geometry" in table_dict
    assert len(table_dict["geometry"]) == len(valid_geojson_obj.features)
    assert "name" in table_dict

    parquet_path = Path("test.parquet")
    pyarrow.parquet.write_table(table, parquet_path)
    assert parquet_path.exists()
    gdf = gpd.read_parquet(parquet_path)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs.to_string() == "OGC:CRS84"
    assert len(gdf) == len(valid_geojson_obj.features)
    parquet_path.unlink()


def test_bad_geojson_to_geoparquet(
    valid_geojson_obj: FeatureCollection,
):
    """Test the error handling of bad inputs."""
    # test bad geo_metadata
    with pytest.raises(ValueError):
        geojson_to_geoparquet(
            valid_geojson_obj,
            geo_metadata={"NOT": "VALID"},
        )

    # test bad column_schema
    with pytest.raises(ValueError):
        geojson_to_geoparquet(
            valid_geojson_obj,
            column_schema={"NOT": "VALID"},
        )

    # cant have properties as a column with other columns
    with pytest.raises(ValueError):
        geojson_to_geoparquet(
            valid_geojson_obj,
            column_schema=pyarrow.schema(
                [
                    ("geometry", pyarrow.binary()),
                    ("properties", pyarrow.string()),
                    ("name", pyarrow.string()),
                ]
            ),
        )


def test_valid_geoparquet_to_geojson(
    valid_geoparquet_file: Path,
):
    """Test the conversion of a valid GeoParquet file to a valid GeoJSON object."""
    geojson = geoparquet_to_geojson(valid_geoparquet_file)
    assert isinstance(geojson, FeatureCollection)
    assert len(geojson.features) == 7
    for feature in geojson.features:
        assert isinstance(feature, geojson_pydantic.features.Feature)
        assert isinstance(
            feature.geometry, geojson_pydantic.geometries._GeometryBase
        ) or isinstance(feature.geometry, geojson_pydantic.base._GeoJsonBase)
        assert isinstance(feature.properties, dict)
        assert isinstance(feature.bbox, tuple)
        assert len(feature.bbox) == 4
