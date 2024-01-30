import geojson_pydantic
import shapely
import multiprocessing
from geojson_pydantic.geometries import (
    _GeometryBase,
)


def to_wkb(self: _GeometryBase):
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(self.model_dump())

_GeometryBase.wkb = property(to_wkb)

