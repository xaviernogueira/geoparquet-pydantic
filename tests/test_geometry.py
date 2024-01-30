from geojson_pydantic.geometries import (
    LineString,
    Point,
    Polygon,
)
import geoparquet_pydantic as _


def test_wkb_point() -> None:
    p = Point(type='Point', coordinates=(37.792317, -122.4102644))
    assert p.wkb.hex() == '01010000004c88b9a46ae54240a32d9dc5419a5ec0'


def test_wkb_line() -> None:
    p = LineString(
        type='LineString',
        coordinates=[
            (37.792317, -122.4102644),
            (37.8, -122.5),
        ],
    )
    assert p.wkb.hex() == '0102000000020000004c88b9a46ae54240a32d9dc5419a5ec06666666666e642400000000000a05ec0'


def test_wkb_poly() -> None:
    p = Polygon(
        type='Polygon',
        coordinates=[[
            (37.792317, -122.4102644),
            (37.792317, -121),
            (37, -121),
            (37, -122.4102644),
            (37.792317, -122.4102644),
        ]],
    )
    assert p.wkb.hex() == '010300000001000000050000004c88b9a46ae54240a32d9dc5419a5ec04c88b9a46ae542400000000000405ec000000000008042400000000000405ec00000000000804240a32d9dc5419a5ec04c88b9a46ae54240a32d9dc5419a5ec0'
