import pytest
import pathlib
import json
import geopandas as gpd
from geojson_pydantic.geometries import (
    LineString,
    Point,
    Polygon,
)
from geojson_pydantic.features import (
    FeatureCollection,
)
import geoparquet_pydantic as _


@pytest.fixture
def feature_collection() -> FeatureCollection:
    raw_json = '{"type": "FeatureCollection", "features": [{"id": "0", "type": "Feature", "properties": {"id": "0", "code": "T1", "Geodetic_CRS": "WGS 84 / UTM zone 10N"}, "geometry": {"type": "Polygon", "coordinates": [[[747807.6773986425, 3838312.768530584], [747792.9615659006, 3838318.724312481], [747790.0180619457, 3838338.7734970096], [747796.2338329138, 3838345.1385048716], [747804.1622209096, 3838352.098842616], [747812.651667356, 3838359.3527284637], [747820.8417072668, 3838365.252664663], [747833.2962426465, 3838374.509828232], [747837.2500161389, 3838377.181150481], [747840.9908188957, 3838379.4710375364], [747844.7861816538, 3838381.954865413], [747846.7463328483, 3838381.9505483047], [747847.8225725183, 3838380.5861214693], [747877.0975608453, 3838173.3175020264], [747873.5795755642, 3838173.22367381], [747851.5592983699, 3838183.0937871556], [747834.9243247212, 3838190.728815091], [747820.6384537308, 3838196.997568446], [747805.2162329722, 3838201.919581854], [747799.8149567994, 3838204.4499806226], [747798.6966831052, 3838207.9615626303], [747794.3950431754, 3838234.546422815], [747811.9289362319, 3838236.4644265906], [747812.7720371028, 3838243.7393500623], [747810.5224205869, 3838259.41643434], [747806.0448247854, 3838258.9768281984], [747801.0192470239, 3838294.6899427576], [747810.2585740455, 3838296.0725790625], [747807.6773986425, 3838312.768530584]], [[747819.6981835028, 3838262.0759523967], [747830.892433195, 3838263.3909400785], [747827.5164084632, 3838285.322452647], [747816.5891007249, 3838284.0517059457], [747819.6981835028, 3838262.0759523967]]]}}]}'
    return FeatureCollection(**json.loads(raw_json))


def test_wkb_point() -> None:
    p = Point(type="Point", coordinates=(37.792317, -122.4102644))
    assert p.wkb.hex() == "01010000004c88b9a46ae54240a32d9dc5419a5ec0"


def test_wkb_line() -> None:
    p = LineString(
        type="LineString",
        coordinates=[
            (37.792317, -122.4102644),
            (37.8, -122.5),
        ],
    )
    assert (
        p.wkb.hex()
        == "0102000000020000004c88b9a46ae54240a32d9dc5419a5ec06666666666e642400000000000a05ec0"
    )


def test_wkb_poly() -> None:
    p = Polygon(
        type="Polygon",
        coordinates=[
            [
                (37.792317, -122.4102644),
                (37.792317, -121),
                (37, -121),
                (37, -122.4102644),
                (37.792317, -122.4102644),
            ]
        ],
    )
    assert (
        p.wkb.hex()
        == "010300000001000000050000004c88b9a46ae54240a32d9dc5419a5ec04c88b9a46ae542400000000000405ec000000000008042400000000000405ec00000000000804240a32d9dc5419a5ec04c88b9a46ae54240a32d9dc5419a5ec0"
    )


def test_to_geoparquet(
    feature_collection: FeatureCollection,
    tmp_path: pathlib.Path,
) -> None:
    path = tmp_path / "test.parquet"
    out_path = feature_collection.to_geoparquet(path)
    assert str(path) == out_path
    assert pathlib.Path(path).exists()

    df = gpd.read_parquet(path)
    assert isinstance(df, gpd.GeoDataFrame)
    assert len(df) == 1
    assert df.geometry[0].wkt == feature_collection.features[0].geometry.wkt
