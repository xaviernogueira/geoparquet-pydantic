import shapely.wkb
import shapely.wkt
import pyarrow
import pyarrow.parquet as parquet
from geojson_pydantic.geometries import (
    _GeometryBase,
)
from geojson_pydantic.features import (
    Feature,
    FeatureCollection,
)


def to_wkb(self: _GeometryBase) -> bytes:
    """Converts the GeoJSON object to WKB format."""
    return shapely.wkb.dumps(shapely.wkt.loads(self.wkt))

_GeometryBase.wkb = property(to_wkb)


def _get_geom_types(features: list[Feature]) -> list[str]:
    return list(set([feature.geometry.type for feature in features]))

def to_geoparquet(
    self: FeatureCollection,
    version: str = '1.0',
    **kwargs,
) -> None:
    """Writes the FeatureCollection to a GeoParquet file."""

    # write table
    table = pyarrow.Table.from_pydict(
       {
            'geometry': [feature.geometry.wkb for feature in self.features],
       },
    )
    parquet.write_table()

    # update metadata
    metadata = {
        'version': '1.0',
        'primary_column': 'geometry',
        'columns': {
            'geometry': {
                'encoding': 'WKB',
                'geometry_types': _get_geom_types(self.features),
            },
        },
    }


FeatureCollection.to_geoparquet = to_geoparquet



