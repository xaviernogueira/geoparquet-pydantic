# GeoParquet-Pydantic 


<p align="center">
  <img src="https://github.com/xaviernogueira/geoparquet-pydantic/blob/main/imgs/repo_logo.png" alt="Logo">
</p>

</p>
<p align="center">
  <em> A lightweight, <a href="https://docs.pydantic.dev/latest/" target=<"_blank">pydantic</a> centric library for validating GeoParquet files (or PyArrow Tables) and converting between GeoJSON and GeoParquet...without GDAL!</em>
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
In the age of cloud-native tech, size limits on popular services such as AWS Lambda make large dependencies more

**Is this library the right choice for you?:**
* Do you need to use a wide variety of Geospatial functions? If so, you will likely have to add GDAL/GeoPandas as a dependency anyways,
making this ibrary's conversion functions *probably* redundant.
* Is your workflow command line centric? If so you may want to consider Planet Lab's simular CLI tool [`gpq`](https://github.com/planetlabs/gpq),
which is written in Go and substantially faster than our CLI tool.
* Otherwise, if you are using Python and want to avoid unnecessary bulky dependencies, this library will be a great choice!

# Installation

```bash
pip install geoparquet-pydantic
```

And then import with an underscore:
```python
import geoparquet_pydantic
```

# Features

## `pydantic` Schemas

* `geoparquet_pydantic.GeometryColumnMetadata`: A `pydantic` model that validates a
geometry column's (aka `primary_column`) metadata. This is nested within the following schema.
* `geoparquet_pydantic.GeoParquetMetadata`: A `pydantic` model for the metadata assigned to the "geo" key in a `pyarrow.Table`
that allows it to be read by GeoParquet readers once saved.

For an explanation of these schemas, please refence the [geoparquet repository](https://github.com/opengeospatial/geoparquet/blob/main/format-specs/geoparquet.md).

## Conversion functions

### `geoparquet_pydantic.geojson_to_geoparquet()`

Converts a GeoJSON feature collection (validated by `geojson_pydantic.features.FeatureCollection`) into a GeoParquet.

### `geoparquet_pydantic.geoparquet_to_geojson()`: WIP.

## Validation functions

### `geoparquet_pydantic.validate_geoparquet_table`
A convenience function that simply uses `GeoParquetMetadata` to validate the metadata in a `pyarrow.Table`,
and verifies that the expected geometry/primary column is present.

### `geoparquet_pydantic.validate_geoparquet_file`
Uses `pyarrow.parquet.read_metadata()` and `GeoParquetMetadata` to validate a `.parquet` file without opening it.


## CLI Tool

WORK IN PROGRESS.

This CLI tool is provided for file to file conversions/validations. It is included for convenience,
but if one's workflow is CLI centric, I must recomend to Planet's [`gpq`](https://github.com/planetlabs/gpq) library which is written in Go and much faster.

### Set Up

To see available commands:
```bash
geoparquet_pydantic --help
```

We recomend adding an alias to avoid having to write the verbose project name over and over again.

# Contribute

We encourage contributions, feature requests, and bug reports!

Use `dev-requirements.txt` to install our development dependencies, and be sure to use `pre-commit run --all-file` before commiting your work. If you add a new feature, we request that you add test coverage for it. Happy coding.
