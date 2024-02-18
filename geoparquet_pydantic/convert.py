"""Converts a GeoJSON Pydantic FeatureCollection to an Arrow table or GeoParquet."""

import shapely.wkb
import shapely.wkt
import pyarrow
import json
from geojson_pydantic.geometries import (
    _GeometryBase,
)
from geojson_pydantic.features import (
    Feature,
    FeatureCollection,
)
from geoparquet_pydantic.schemas import (
    GeoColumnMetadata,
    GeoParquet,
)
from pathlib import Path
from typing import Optional, Iterable


def _to_wkb(geometry: _GeometryBase) -> bytes:
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(shapely.wkt.loads(geometry.wkt))


def _get_geom_types(features: list[Feature]) -> list[str]:
    return list(set([feature.geometry.type for feature in features]))


def _get_default_geo_metadata(feature_collection: FeatureCollection) -> GeoParquet:
    return GeoParquet(
        primary_column="geometry",
        columns={
            "geometry": GeoColumnMetadata(
                **{
                    "encoding": "WKB",
                    "geometry_types": _get_geom_types(feature_collection.features),
                }
            ),
        },
    )


def _update_metadata(table: pyarrow.Table, metadata: dict) -> pyarrow.Table:
    new_metadata = table.schema.metadata
    if not new_metadata:
        new_metadata = {}
    for k, v in metadata.items():
        new_metadata[k] = json.dumps(v).encode("utf-8")
    return table.replace_schema_metadata(new_metadata)


def _validate_column_schema(
    column_schema: pyarrow.Schema,
    primary_column: str,
    geojson: FeatureCollection,
) -> None:
    names = [i for i in column_schema.names if i != primary_column]
    for feature in geojson.features:
        assert all(
            [feature.properties.get(name) for name in names]
        ), f"Feature {feature} does not contain all the columns in the schema: {column_schema.names}"


def geojson_to_geoparquet(
    geojson: FeatureCollection | Path,
    primary_column: Optional[str] = None,
    column_schema: Optional[pyarrow.Schema] = None,
    geo_metadata: GeoParquet | dict | None = None,
    **kwargs,
) -> pyarrow.Table:
    """Converts a GeoJSON Pydantic FeatureCollection to an Arrow table with geoparquet metadata.

    To save to a file, simply use pyarrow.parquet.write_table() on the returned table.

    Args:
        geojson (FeatureCollection): The GeoJSON Pydantic FeatureCollection.
        primary_column (str, optional): The name of the primary column. Defaults to None.
        column_schema (pyarrow.Schema, optional): The Arrow schema for the table. Defaults to None.
        geo_metadata (GeoParquet | dict | None, optional): The GeoParquet metadata.
        **kwargs: Additional keyword arguments for the Arrow table writer.

    Returns:
        The Arrow table with GeoParquet metadata.
    """
    if not isinstance(geojson, FeatureCollection):
        geojson = FeatureCollection(**json.load(geojson.open("r")))
    if not primary_column:
        primary_column = "geometry"

    # get primary column as iterables
    columns: list[Iterable] = [map(lambda f: _to_wkb(f.geometry), geojson.features)]

    # get geo metadata
    if not geo_metadata:
        geo_metadata = _get_default_geo_metadata(geojson)
    if isinstance(geo_metadata, dict):
        geo_metadata = GeoParquet(**geo_metadata)
    if not isinstance(geo_metadata, GeoParquet):
        raise ValueError("geo_metadata must be a valid GeoParquet class, dict, or None")

    # get other columns as iterables and update schema
    if not column_schema:
        column_schema = pyarrow.schema(
            [
                (primary_column, pyarrow.binary()),
                ("properties", pyarrow.string()),
            ]
        )
    elif isinstance(column_schema, pyarrow.Schema):
        if primary_column in column_schema.names:
            column_schema.remove(column_schema.get_field_index(primary_column))
        column_schema.insert(0, pyarrow.field(primary_column, pyarrow.binary()))
    else:
        raise ValueError("column_schema must be a valid pyarrow.Schema or None")

    if "properties" in column_schema.names:
        if len(column_schema.names) > 2:
            raise ValueError(
                "Cannot have 'properties' as a column with other columns (which are pulled from GeoJSON propreties)."
            )
        columns.append(map(lambda f: json.dumps(f.properties), geojson.features))

    else:
        _validate_column_schema(column_schema, primary_column, geojson)

        for col in column_schema.names:
            columns.append(map(lambda f: f.properties.get(col), geojson.features))

    # write table
    table = pyarrow.Table.from_pydict(
        {**dict(zip(column_schema.names, columns))},
        schema=column_schema,
        **kwargs,
    )
    return _update_metadata(table, {"geo": geo_metadata.model_dump()})


def geoparquet_to_geojson(
    arrow_table: pyarrow.Table,
) -> FeatureCollection:
    """Converts an Arrow table with GeoParquet metadata to a GeoJSON Pydantic FeatureCollection.

    Args:
        arrow_table (pyarrow.Table): The Arrow table with GeoParquet metadata.

    Returns:
        FeatureCollection: The GeoJSON Pydantic FeatureCollection.
    """
    raise NotImplementedError("This function is not yet implemented.")
