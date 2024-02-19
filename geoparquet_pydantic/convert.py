import ast
import functools
import geojson_pydantic
from geojson_pydantic.types import BBox
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
    GeometryColumnMetadata,
    GeoParquetMetadata,
    GeometryTypes,
)
from pathlib import Path
from typing import Any, Optional, Iterable


def _to_wkb(geometry: _GeometryBase) -> bytes:
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(shapely.wkt.loads(geometry.wkt))


def _get_geom_types(features: list[Feature]) -> list[str]:
    return list(set([feature.geometry.type for feature in features]))


def _get_default_geo_metadata(
    feature_collection: FeatureCollection,
) -> GeoParquetMetadata:
    return GeoParquetMetadata(
        primary_column="geometry",
        columns={
            "geometry": GeometryColumnMetadata(
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
    add_none_values: bool,
) -> None:
    names = [i for i in column_schema.names if i != primary_column]
    for feature in geojson.features:
        if not add_none_values:
            all_present = all([name in feature.properties.keys() for name in names])
            if not all_present:
                raise ValueError(
                    f"Feature {feature} does not contain all the columns in the schema: {column_schema.names}",
                )

        else:
            for name in names:
                if not feature.properties.get(name):
                    feature.properties[name] = None


def geojson_to_geoparquet(
    geojson: FeatureCollection | Path,
    primary_column: Optional[str] = None,
    column_schema: Optional[pyarrow.Schema] = None,
    add_none_values: Optional[bool] = False,
    geo_metadata: GeoParquetMetadata | dict | None = None,
    **kwargs,
) -> pyarrow.Table:
    """Converts a GeoJSON Pydantic FeatureCollection to an Arrow table with geoparquet metadata.

    To save to a file, simply use pyarrow.parquet.write_table() on the returned table.

    Args:
        geojson (FeatureCollection): The GeoJSON Pydantic FeatureCollection.
        primary_column (str, optional): The name of the primary column. Defaults to None.
        column_schema (pyarrow.Schema, optional): The Arrow schema for the table. Defaults to None.
        add_none_values (bool, default=False): Whether to fill missing column values
            specified in param:column_schema with 'None' (converts to pyarrow.null()).
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
        geo_metadata = GeoParquetMetadata(**geo_metadata)
    if not isinstance(geo_metadata, GeoParquetMetadata):
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
        _validate_column_schema(column_schema, primary_column, geojson, add_none_values)

        for col in column_schema.names:
            columns.append(map(lambda f: f.properties.get(col), geojson.features))

    # write table
    table = pyarrow.Table.from_pydict(
        {**dict(zip(column_schema.names, columns))},
        schema=column_schema,
        **kwargs,
    )
    return _update_metadata(table, {"geo": geo_metadata.model_dump()})


def _find_bbox(geoparquet: pyarrow.Table) -> BBox | None:
    decoded_metadata: dict[str, Any] = ast.literal_eval(
        geoparquet.schema.metadata[b"geo"].decode("utf-8"),
    )
    bbox = decoded_metadata["columns"]["geometry"].get("bbox", None)
    if isinstance(bbox, list):
        bbox = tuple(bbox)
    return bbox


def _get_prop_records(name_value_tuple: tuple[str, list[Any]]) -> list[tuple[str, Any]]:
    name, values = name_value_tuple
    return list(zip([name] * len(values), values))


def _shapely_to_feature(
    geometry: shapely.geometry.base.BaseGeometry,
    properties: list[tuple[str, Any]],
) -> Feature:
    geom_class: type[GeometryTypes] = getattr(geojson_pydantic, type(geometry).__name__)
    return Feature(
        type="Feature",
        geometry=geom_class(**json.loads(shapely.to_geojson(geometry))),
        bbox=list(geometry.bounds),
        properties=dict([*properties]),
    )


def geoparquet_to_geojson(
    geoparquet: pyarrow.Table | str | Path,
    primary_column: Optional[str] = None,
    max_chunksize: Optional[int] = 1000,
) -> FeatureCollection:
    """Converts an Arrow table with GeoParquet metadata to a GeoJSON Pydantic FeatureCollection.

    Args:
        geoparquet (pyarrow.Table): Either an Arrow.Table or parquet with GeoParquet metadata.
        primary_column (str, optional): The name of the primary column. Defaults to None.
        max_chunksize (int, optional): The maximum chunksize to read from the parquet file. Defaults to 1000.
    Returns:
        FeatureCollection: The GeoJSON Pydantic FeatureCollection.
    """
    if not primary_column:
        primary_column = "geometry"
    if not max_chunksize:
        max_chunksize = 1000
    if isinstance(geoparquet, (str, Path)):
        geoparquet = pyarrow.parquet.read_table(geoparquet)
    if not isinstance(geoparquet, pyarrow.Table):
        raise ValueError(
            "param:geoparquet must be a valid pyarrow.Table or parquet file"
        )

    if primary_column not in geoparquet.column_names:
        raise ValueError(f"Primary column {primary_column} not found in the table.")

    # attempt to get the bbox from metadata
    bbox: BBox | None = _find_bbox(geoparquet)

    # TODO: parallelize this (optionally)
    feature_lists: list[list[Feature]] = []
    for chunk in geoparquet.to_batches(max_chunksize):
        chunk_dict = chunk.to_pydict()
        geoms: list[bytes] = chunk_dict.pop(primary_column)
        properties: Iterable[list[tuple[str, Any]]] = map(
            _get_prop_records,
            chunk_dict.items(),
        )
        feature_props: Iterable[list[tuple[str, Any]]] = map(
            lambda i: [p[i] for p in properties],
            range(len(geoms)),
        )

        chunk_features: Iterable[Feature] = map(
            lambda gp: _shapely_to_feature(shapely.from_wkb(gp[0]), gp[1]),
            zip(geoms, feature_props),
        )
        feature_lists.append(list(chunk_features))
    features: list[Feature] = list(functools.reduce(lambda a, b: a + b, feature_lists))

    return FeatureCollection(
        type="FeatureCollection",
        features=features,
        bbox=bbox,
    )
