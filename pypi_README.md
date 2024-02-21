# GeoParquet-Pydantic

**Motivation:** This project started at the 2024 San Fransisco GeoParquet Community hackathon, and arose out of a simple observation:
why must Python users install the *massive* GDAL dependency (typically via GeoPandas) to do simple GeoJSON<>GeoParquet conversions.

**Is this library the right choice for you?:**
* Do you need to use a wide variety of Geospatial functions? If so, you will likely have to add GDAL/GeoPandas as a dependency anyways,
making this ibrary's conversion functions *probably* redundant.
* Is your workflow command line centric? If so you may want to consider Planet Lab's simular CLI tool [`gpq`](https://github.com/planetlabs/gpq),
which is written in Go and substantially faster.
* Otherwise, if you are using Python and want to avoid unnecessary bulky dependencies, this library will be a great choice!

**Note:** All user-exposed functions and schema classes are available at the top level (i.e., `geoparquet_pydantic.validate_geoparquet_table(...)`) of this library.

# Documentation is on GitHub [here](https://github.com/xaviernogueira/geoparquet-pydantic/blob/main/README.md)

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
from geoparquet_pydantic import GeometryColumnMetadata
from geoparquet_pydantic import GeoParquetMetadata
from geoparquet_pydantic import validate_geoparquet_table
from geoparquet_pydantic import validate_geoparquet_file
from geoparquet_pydantic import geojson_to_geoparquet
from geoparquet_pydantic import geoparquet_to_geojson
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
