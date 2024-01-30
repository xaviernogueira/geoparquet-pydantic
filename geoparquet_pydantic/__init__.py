import shapely
import pyarrow.parquet as parquet
from geojson_pydantic.geometries import (
    _GeometryBase,
)
from geojson_pydantic.features import (
    FeatureCollection,
)


def to_wkb(self: _GeometryBase) -> bytes:
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(self.model_dump())

_GeometryBase.wkb = property(to_wkb)


def to_geoparquet(self: FeatureCollection) -> None:
    ...

FeatureCollection.to_geoparquet = to_geoparquet



