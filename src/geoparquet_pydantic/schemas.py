"""Pydantic models for GeoParquet metadata."""

import ast
from pydantic import BeforeValidator, Field, BaseModel, field_validator, model_validator
from typing import Annotated, Optional, Literal, Union
from pyproj import CRS

EdgeType = Literal["planar", "spherical"]

FlatGeometryTypes = Annotated[
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

ZGeometryTypes = Annotated[
    Literal[
        "PointZ",
        "MultiPointZ",
        "LineStringZ",
        "MultiLineStringZ",
        "PolygonZ",
        "MultiPolygonZ",
        "GeometryCollectionZ",
    ],
    Field(description="3D geometry types supported by the column"),
]

GeometryTypes = Union[FlatGeometryTypes, ZGeometryTypes]


class GeometryColumnMetadata(BaseModel):
    encoding: Literal["WKB"]
    geometry_types: list[GeometryTypes]

    crs: Annotated[
        str,
        Field(
            description="The CRS of the geometry column in a string format readable by pyproj. Is the converted to PROJJSON format"
        ),
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

    orientation: Literal["counterclockwise"] = "counterclockwise"

    @field_validator("crs")
    @classmethod
    def convert_crs_to_projjson(cls, v) -> str:
        """Parse a CRS string and return a PROJJSON string."""
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
        return v

    @field_validator("bbox")
    @classmethod
    def must_be_length_4(cls, v):
        if v is not None and len(v) != 4:
            raise ValueError("bbox must be a list of 4 floats!")
        return v


class GeoParquetMetadata(BaseModel):
    version: Annotated[
        str, Field(description="The version of the GeoParquet format")
    ] = "1.1.0-dev"
    primary_column: Annotated[
        str, Field(description="The name of the geometry primary column")
    ] = "geometry"
    columns: Annotated[
        dict[str, GeometryColumnMetadata | dict | str],
        Field(description="Metadata for each column (keys)"),
    ]

    @model_validator(mode="after")
    def contains_primary_col(self) -> "GeoParquetMetadata":
        if not self.primary_column in self.columns.keys():
            raise ValueError(
                f"primary column={self.primary_column} not in arg:columns={self.columns}"
            )
        return self

    @model_validator(mode="after")
    def convert_geo_to_class(self) -> "GeoParquetMetadata":
        if not isinstance(self.columns[self.primary_column], GeometryColumnMetadata):
            if isinstance(self.columns[self.primary_column], str):
                self.columns[self.primary_column] = ast.literal_eval(
                    self.columns[self.primary_column]
                )
            if isinstance(self.columns[self.primary_column], dict):
                self.columns[self.primary_column] = GeometryColumnMetadata(
                    **self.columns[self.primary_column]
                )
            else:
                raise ValueError(
                    f"Invalid primary column metadata: {self.columns[self.primary_column]}"
                )
        return self
