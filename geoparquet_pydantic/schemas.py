"""Pydantic models for GeoParquet metadata."""
from pydantic import Field, BaseModel, field_validator, model_validator
from typing import Annotated, Optional, Literal, Union
from pyproj import CRS

EdgeType = Literal["planar", "spherical"]

GeometryTypes = Annotated[
    # TODO: support 3d geometries with Z suffix
    Literal[
        "Point",
        "MultiPoint",
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
        "GeometryCollection",
    ],
    Field(description="The geometry types supported by the column"),
]


class GeoColumnMetadata(BaseModel):
    encoding: Literal["WKB"]
    geometry_types: list[GeometryTypes]

    crs: Annotated[
        str, Field(description="The CRS of the geometry column in PROJJSON format")
    ] = "OGC:CRS84"

    edges: Annotated[
        EdgeType, Field(description="The type of edges of the geometries")
    ] = "planar"

    bbox: Optional[
        Annotated[list[float], Field(description="The bounding box of the geometries")]
    ] = None

    epoch: Optional[
        Annotated[
            Union[int, float],
            Field(description="Coordinate epoch in case of a dynamic CRS"),
        ]
    ] = None

    orientation: Literal["counterclockwise"]

    @field_validator("crs")
    @classmethod
    def convert_crs_to_projjson(cls, v) -> str:
        """Parse a CRS string and return a PROJJSON string"""
        try:
            crs = CRS.from_string(v)
            return crs.to_json()
        except Exception as e:
            raise ValueError(f"Invalid CRS string: {e}")

    @field_validator("geometry_types")
    @classmethod
    def only_unique_types(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("geometry_types items must be unique!")

    @field_validator("bbox")
    @classmethod
    def must_be_length_4(cls, v):
        if v is not None and len(v) != 4:
            raise ValueError("bbox must be a list of 4 floats!")


class GeoParquet(BaseModel):
    version: Annotated[
        str, Field(description="The version of the GeoParquet format")
    ] = "1.1.0-dev"
    primary_column: Annotated[
        str, Field(description="The name of the geometry primary column")
    ] = "geometry"
    columns: Annotated[
        dict[str, GeoColumnMetadata],
        Field(description="Metadata for each column (keys)"),
    ]

    @model_validator(mode="after")
    def contains_primary_col(self) -> "GeoParquet":
        if not self.primary_column in self.columns.keys():
            raise ValueError(
                f"primary column={self.primary_column} not in arg:columns={self.columns}"
            )
        return self
