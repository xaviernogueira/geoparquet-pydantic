"""Converts a GeoJSON Pydantic FeatureCollection to an Arrow table or GeoParquet."""

import shapely.wkb
import shapely.wkt
import pyarrow
import json
import pyarrow.parquet as parquet
from geojson_pydantic.geometries import (
    _GeometryBase,
)
from geojson_pydantic.features import (
    Feature,
    FeatureCollection,
)
from geoparquet_pydantic.schemas import (
    GeoParquet,
)
from pathlib import Path
from typing import Optional, Iterable


def _to_wkb(self: _GeometryBase) -> bytes:
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(shapely.wkt.loads(self.wkt))


def _get_geom_types(features: list[Feature]) -> list[str]:
    return list(set([feature.geometry.type for feature in features]))


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


def geojson_to_arrow(
    geojson: FeatureCollection,
    primary_column: Optional[str] = None,
    column_schema: Optional[pyarrow.Schema] = None,
    **kwargs,
) -> pyarrow.Table:
    """Converts a GeoJSON Pydantic FeatureCollection to an Arrow table.

    Args:
        geojson (FeatureCollection): The GeoJSON Pydantic FeatureCollection.
        primary_column (str, optional): The name of the primary column. Defaults to None.
        column_schema (pyarrow.Schema, optional): The Arrow schema for the table. Defaults to None.
        **kwargs: Additional keyword arguments for the Arrow table writer.

    Returns:
        The Arrow table.
    """

    if not primary_column:
        primary_column = "geometry"

    # get primary column as iterables
    columns: list[Iterable] = [map(lambda f: _to_wkb(f.geometry), geojson.features)]

    # get other columns as iterables and update schema
    if not column_schema:
        column_schema = pyarrow.Schema(
            [
                (primary_column, pyarrow.binary()),
                ("properties", pyarrow.string()),
            ]
        )
    else:
        if primary_column in column_schema.names:
            column_schema.remove(column_schema.get_field_index(primary_column))
        column_schema.inset(0, (primary_column, pyarrow.binary()))

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
    return pyarrow.Table.from_pydict(
        {**dict(zip(column_schema.names, columns))},
        schema=column_schema,
        **kwargs,
    )


def table_to_geoparquet(
    table: pyarrow.Table,
    path: str | Path,
    geo_metadata: GeoParquet | dict | None = None,
    primary_column: Optional[str] = None,
    **kwargs,
) -> Path:
    """Converts an Arrow table to a GeoParquet file.

    Args:
        table (pyarrow.Table): The Arrow table
        path (str | Path): The path to the GeoParquet file.
        geo_metadata (GeoParquet | dict | None, optional): The GeoParquet metadata.
           This can be either a validated GeoParquet class, or a dict to validate. Defaults to None.
        **kwargs: Additional keyword arguments for the Arrow parquet writer.

    Returns:
        Path: The path to the GeoParquet file.
    """
    if not primary_column:
        primary_column = "geometry"
    if not geo_metadata:
        geo_metdata = {
            "primary_column": "geometry",
            "columns": {
                "geometry": {
                    "encoding": "WKB",
                    "geometry_types": _get_geom_types(
                        table.column(primary_column).to_pylist()
                    ),
                },
            },
        }
    if isinstance(geo_metadata, dict):
        geo_metadata = GeoParquet(**geo_metadata)
    if not isinstance(geo_metadata, GeoParquet):
        raise ValueError("geo_metadata must be a valid GeoParquet class, dict, or None")

    table: pyarrow.Table = _update_metadata(
        table,
        {"geo": geo_metadata.model_dump()},
    )
    parquet.write_table(table, path, **kwargs)
