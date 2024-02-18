# geoparquet-pydantic

A lightweight library for validating GeoParquet files and converting between GeoJSON and GeoParquet...without GDAL! 
This library also includes `pydantic` Schema for GeoParquet metadata and builds off Development Seed's 
[`geojson-pydantic`](https://github.com/developmentseed/geojson-pydantic) library.

# Features

## Schemas

* `geoparquet_pydantic.GeometryColumnMetadata`: A `pydantic` model that validates a
geometry column's (aka `primary_column`) metadata. This is nested within the following schema.
* `geoparquet_pydantic.GeoParquetMetadata`: A `pydantic` model for the metadata assigned to the "geo" key in a `pyarrow.Table`
that allows it to be read by GeoParquet readers once saved.

## Conversion functions

* `geoparquet_pydantic.geojson_to_geoparquet`: 
* `geoparquet_pydantic.geoparquet_to_geojson`: 

## Validation functions

* `geoparquet_pydantic.validate_geoparquet_table`: A convenience function that simply uses `GeoParquetMetadata` to validate
the metadata in a `pyarrow.Table`, and verifies that the expected geometry/primary column is present.
* `geoparquet_pydantic.validate_geoparquet_file`: Uses `pyarrow.parquet.read_metadata()` and `GeoParquetMetadata` to validate a `.parquet` file
without opening it.

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


