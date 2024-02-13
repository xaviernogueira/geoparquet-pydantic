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
from pathlib import Path
from typing import Optional


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


def geojson_to_arrow(
    geojson: FeatureCollection,
    primary_column: Optional[str] = None,
    column_schema: Optional[pyarrow.Schema] = None,
    **kwargs,
) -> str:
    """Writes the FeatureCollection to a GeoParquet file.

    Args:
        path (str): The path to the output file.
        version (str, optional): The GeoParquet version. Defaults to '1.0'.
    Returns:
        The path of the saved GeoParquet.

    """

    if not primary_column:
        primary_column = "geometry"

    if not column_schema:
        column_schema = pyarrow.Schema(
            [
                (primary_column, pyarrow.binary()),
                ("properties", pyarrow.string()),
            ]
        )
    elif (
        isinstance(column_schema, pyarrow.Schema)
        and primary_column not in column_schema.names
    ):
        column_schema.append(primary_column, pyarrow.binary())
    else:
        raise ValueError("Optional arg:column_schema must be a pyarrow.Schema object")

    # write table
    table = pyarrow.Table.from_pydict(
        {
            primary_column: [_to_wkb(f.geometry) for f in geojson.features],
        }
    )


    """Converts a GeoJSON Pydantic FeatureCollection to an Arrow table.

    Returns:
        The Arrow table.
    """
    ...

def geojson_to_geoparquet(
    table: pyarrow.Table,
    path: str | Path,
    version: Optional[str] = None,
) -> Path:
    # update metadata
    geo_metadata = {
        "version": version,
        "primary_column": "geometry",
        "columns": {
            "geometry": {
                "encoding": "WKB",
                "geometry_types": _get_geom_types(geojson.features),
            },
        },
    }
    metadata = {"geo": geo_metadata}
    table: pyarrow.Table = _update_metadata(table, metadata)
    parquet.write_table(table, path, **kwargs)
    return str(path)
