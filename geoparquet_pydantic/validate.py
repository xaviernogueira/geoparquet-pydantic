"""For validating an existing GeoParquet file or Arrow table.

Note that validating GeoParquet metadata can be handles with the 
`.schemas` module pydantic classes.
"""

import pyarrow
from geoparquet_pydantic.schemas import GeoColumnMetadata, GeoParquet


def validate_geoparquet_table(
    table: pyarrow.Table,
) -> None:
    """Validates a GeoParquet schema pyarrow.Table."""
    pass


def validate_geoparquet_file():
    """Validates a GeoParquet file."""
    # TODO: use pyarrow.parquet.read_metadata to validate the file
    pass
