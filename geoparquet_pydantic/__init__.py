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


def to_wkb(self: _GeometryBase) -> bytes:
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(shapely.wkt.loads(self.wkt))


_GeometryBase.wkb = property(to_wkb)


def _get_geom_types(features: list[Feature]) -> list[str]:
    return list(set([feature.geometry.type for feature in features]))


def _update_metadata(table: pyarrow.Table, metadata: dict) -> pyarrow.Table:
    new_metadata = table.schema.metadata
    if not new_metadata:
        new_metadata = {}
    for k, v in metadata.items():
        new_metadata[k] = json.dumps(v).encode("utf-8")
    return table.replace_schema_metadata(new_metadata)


def to_geoparquet(
    self: FeatureCollection,
    path: str | Path,
    version: str = "1.0",
    **kwargs,
) -> str:
    """Writes the FeatureCollection to a GeoParquet file.

    Args:
        path (str): The path to the output file.
        version (str, optional): The GeoParquet version. Defaults to '1.0'.
    Returns:
        The path of the saved GeoParquet.

    """

    # write table
    table = pyarrow.Table.from_pydict(
        {
            "geometry": [feature.geometry.wkb for feature in self.features],
        },
    )

    # update metadata
    metadata = {
        "version": version,
        "primary_column": "geometry",
        "columns": {
            "geometry": {
                "encoding": "WKB",
                "geometry_types": _get_geom_types(self.features),
            },
        },
    }
    table: pyarrow.Table = _update_metadata(table, metadata)
    parquet.write_table(table, path, **kwargs)
    return str(path)


FeatureCollection.to_geoparquet = to_geoparquet
