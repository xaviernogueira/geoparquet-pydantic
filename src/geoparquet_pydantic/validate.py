"""For validating an existing GeoParquet file or Arrow table.

Note that validating GeoParquet metadata can be handles with the
`.schemas` module pydantic classes.
"""

import ast
import pyarrow
from geoparquet_pydantic.schemas import (
    GeoParquetMetadata,
)
from typing import Optional
from pathlib import Path


def _validate_geo_metadata(metadata: dict[bytes, bytes]) -> bool:
    try:
        geo_metadata = ast.literal_eval(metadata[b"geo"].decode("utf-8"))
        GeoParquetMetadata(**geo_metadata)
        print("Valid GeoParquet metadata!")
        return True
    except KeyError as e:
        print(f"Invalid GeoParquet metadata, could not find b'geo' key: {e}")
    except ValueError as e:
        print(f"Invalid GeoParquet metadata: {e}")
    return False


def validate_geoparquet_table(
    table: pyarrow.Table,
    primary_column: Optional[str] = None,
) -> bool:
    """Validates a the GeoParquet metadata of a pyarrow.Table.

    See: https://github.com/opengeospatial/geoparquet/blob/main/format-specs/geoparquet.md

    Args:
        table (pyarrow.Table): The table to validate.
        primary_column (Optional[str], optional): The name of the primary geometry column.
            Defaults to None.

    Returns:
        bool: True if the metadata is valid, False otherwise.
    """
    if not primary_column:
        primary_column = "geometry"
    return _validate_geo_metadata(table.schema.metadata)


def validate_geoparquet_file(
    geoparquet_file: str | Path | pyarrow.parquet.ParquetFile,
    primary_column: Optional[str] = None,
    read_file_kwargs: Optional[dict] = None,
) -> bool:
    """Validates that a parquet file has correct GeoParquet metadata without opening it.

    See: https://github.com/opengeospatial/geoparquet/blob/main/format-specs/geoparquet.md

    Args:
        geoparquet_file (str | Path | ParquetFile): The file to validate.
        primary_column (str, optional): The primary column name. Defaults to 'geometry'.
        read_file_kwargs (dict, optional): Kwargs to be passed into pyarrow.parquet.ParquetFile().
            See: https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html#pyarrow-parquet-parquetfile

    Returns:
        bool: True if the metadata is valid, False otherwise.
    """
    if not primary_column:
        primary_column = "geometry"
    default_read_file_kwargs = {
        "memory_map": True,
    }
    if read_file_kwargs is None:
        read_file_kwargs = default_read_file_kwargs
    elif isinstance(read_file_kwargs, dict):
        for k, v in default_read_file_kwargs.items():
            if k not in read_file_kwargs:
                read_file_kwargs[k] = v
    else:
        raise TypeError(f"Optional param:read_file_kwargs must be a dict or None!")

    if isinstance(geoparquet_file, (str, Path)):
        geoparquet_file = pyarrow.parquet.ParquetFile(
            geoparquet_file,
            **read_file_kwargs,
        )
    if not isinstance(geoparquet_file, pyarrow.parquet.ParquetFile):
        raise TypeError(
            "Input must be a file path (str | Path) or a ParquetFile object!"
        )
    return _validate_geo_metadata(geoparquet_file.schema_arrow.metadata)
