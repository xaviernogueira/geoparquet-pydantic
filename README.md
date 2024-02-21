# GeoParquet-Pydantic

<p align="center">
  <img src="https://github.com/xaviernogueira/geoparquet-pydantic/blob/main/imgs/repo_logo.png" alt="Logo">
</p>
<p align="center">
  <em> A lightweight, <a href="https://docs.pydantic.dev/latest/" target="_blank">pydantic</a> centric library for validating GeoParquet files (or PyArrow Tables) and converting between GeoJSON and GeoParquet...without GDAL!</em>
</p>
<p align="center">
  <a href="https://github.com/xaviernogueira/geoparquet-pydantic/actions/workflows/pre-commit.yml" target="_blank">
      <img src="https://github.com/xaviernogueira/geoparquet-pydantic/workflows/pre-commit/badge.svg" alt="Pre-Commit">
  </a>
  <a href="https://github.com/xaviernogueira/geoparquet-pydantic/actions/workflows/tests.yml" target="_blank">
      <img src="https://github.com/xaviernogueira/geoparquet-pydantic/workflows/tests/badge.svg" alt="Tests">
  </a>
  <a href="https://codecov.io/gh/xaviernogueira/geoparquet-pydantic" target="_blank">
      <img src="https://codecov.io/gh/xaviernogueira/geoparquet-pydantic/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/geoparquet-pydantic" target="_blank">
      <img src="https://img.shields.io/pypi/v/geoparquet-pydantic?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/geoparquet-pydantic" target="_blank">
      <img src="https://img.shields.io/pypi/dm/geoparquet-pydantic.svg" alt="Downloads">
  </a>
  <a href="https://github.com/xaviernogueira/geoparquet-pydantic/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/xaviernogueira/geoparquet-pydantic.svg" alt="License">
  </a>
</p>

---
**Motivation:** This project started at the 2024 San Fransisco GeoParquet Community hackathon, and arose out of a simple observation:
why must Python users install the *massive* GDAL dependency (typically via GeoPandas) to do simple GeoJSON<>GeoParquet conversions.

**Is this library the right choice for you?:**
* Do you need to use a wide variety of Geospatial functions? If so, you will likely have to add GDAL/GeoPandas as a dependency anyways,
making this ibrary's conversion functions *probably* redundant.
* Is your workflow command line centric? If so you may want to consider Planet Lab's simular CLI tool [`gpq`](https://github.com/planetlabs/gpq),
which is written in Go and substantially faster.
* Otherwise, if you are using Python and want to avoid unnecessary bulky dependencies, this library will be a great choice!

**Note:** All user-exposed functions and schema classes are available at the top level (i.e., `geoparquet_pydantic.validate_geoparquet_table(...)`) of this library.

# Features

## `pydantic` Schemas

* [`GeometryColumnMetadata`](https://github.com/xaviernogueira/geoparquet-pydantic/blob/cec560451db01cd5c4a4b1fea6486c86975f7499/geoparquet_pydantic/schemas.py#L40): A `pydantic` model that validates a
geometry column's (aka `primary_column`) metadata. This is nested within the following schema.
* [`GeoParquetMetadata`](https://github.com/xaviernogueira/geoparquet-pydantic/blob/cec560451db01cd5c4a4b1fea6486c86975f7499/geoparquet_pydantic/schemas.py#L93): A `pydantic` model for the metadata assigned to the "geo" key in a `pyarrow.Table`
that allows it to be read by GeoParquet readers once saved.

For an explanation of these schemas, please refence the [geoparquet repository](https://github.com/opengeospatial/geoparquet/blob/main/format-specs/geoparquet.md).

## Validation functions

Convenience functions that simply uses `GeoParquetMetadata` to return a `bool` depending on whether the GeoParquet metadata obeys the [schema](https://github.com/opengeospatial/geoparquet/blob/main/format-specs/geoparquet.md).

### Validate a `pyarrow.Table`'s GeoParquet metadata:
```python
def validate_geoparquet_table(
    table: pyarrow.Table,
    primary_column: Optional[str] = None,
) -> bool:
  """Validates a the GeoParquet metadata of a pyarrow.Table.

    Args:
        table (pyarrow.Table): The table to validate.
        primary_column (Optional[str], optional): The name of the primary geometry column.
            Defaults to None.

    Returns:
        bool: True if the metadata is valid, False otherwise.
    """
    ...
```

### Validate a Parquet file's GeoParquet metadata:

```python
def validate_geoparquet_file(
    geoparquet_file: str | Path | pyarrow.parquet.ParquetFile,
    primary_column: Optional[str] = None,
    read_file_kwargs: Optional[dict] = None,
) -> bool:
    """Validates that a parquet file has correct GeoParquet metadata without opening it.

    Args:
        geoparquet_file (str | Path | ParquetFile): The file to validate.
        primary_column (str, optional): The primary column name. Defaults to 'geometry'.
        read_file_kwargs (dict, optional): Kwargs to be passed into pyarrow.parquet.ParquetFile().
            See: https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html#pyarrow-parquet-parquetfile

    Returns:
        bool: True if the metadata is valid, False otherwise.
    """
    ...
```

## Conversion functions

### Convert from `geojson_pydantic.FeatureCollection` to a GeoParquet `pyarrow.Table`

```python
def geojson_to_geoparquet(
    geojson: FeatureCollection | Path,
    primary_column: Optional[str] = None,
    column_schema: Optional[pyarrow.Schema] = None,
    add_none_values: Optional[bool] = False,
    geo_metadata: GeoParquetMetadata | dict | None = None,
    **kwargs,
) -> pyarrow.Table:
    """Converts a GeoJSON Pydantic FeatureCollection to an Arrow table with geoparquet
    metadata.

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
    ...
```

### Convert from a GeoParquet `pyarrow.Table` or file to a `geojson_pydantic.FeatureCollection`

```python
def geoparquet_to_geojson(
    geoparquet: pyarrow.Table | str | Path,
    primary_column: Optional[str] = None,
    max_chunksize: Optional[int] = None,
    max_workers: Optional[int] = None,
) -> FeatureCollection:
    """Converts an Arrow table with GeoParquet metadata to a GeoJSON Pydantic
    FeatureCollection.

    Args:
        geoparquet (pyarrow.Table): Either an Arrow.Table or parquet with GeoParquet metadata.
        primary_column (str, optional): The name of the primary column. Defaults to 'geometry'.
        max_chunksize (int, optional): The maximum chunksize to read from the parquet file. Defaults to 1000.
        max_workers (int, optional): The maximum number of workers to use for parallel processing.
            Defaults to 0 (runs sequentially). Use -1 for all available cores.

    Returns:
        FeatureCollection: The GeoJSON Pydantic FeatureCollection.
    """
    ...
```

# Getting Started

Install from [PyPi](https://pypi.org/project/geoparquet-pydantic):
```bash
pip install geoparquet-pydantic
```

Or from source:
```bash
$ git clone https://github.com/xaviernogueira/geoparquet-pydantic.git
$ cd geoparquet-pydantic
$ pip install .
```

Then import with an underscore:
```python
import geoparquet_pydantic
```

Or just import the functions/classes you need from the top-level:
```python
from geoparquet_pydantic import (
  GeometryColumnMetadata,
  GeoParquetMetadata,
  validate_geoparquet_table,
  validate_geoparquet_file,
  geojson_to_geoparquet,
  geoparquet_to_geojson,
)
```

# Roadmap

- [ ] Make CLI file<>file functions w/ `click`.
- [ ] Add parrallelized Parquet read for `geoparquet_pydantic.geoparquet_to_geojson()`.

# Contribute

We encourage contributions, feature requests, and bug reports!

Here is our recomended workflow:

* Use `dev-requirements.txt` to install our development dependencies.
* Make your edits using `pyright` as a linter.
* Use `pre-commit run --all-file` before commiting your work.
* If you add a new feature, we request that you add test coverage for it.

Happy coding!
