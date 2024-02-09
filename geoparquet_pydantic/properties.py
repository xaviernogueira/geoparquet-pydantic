"""Logic to handle Feature properties as column.

To avoid recreating pandas, we require specification of a pyarrow.schema as 
documented in https://arrow.apache.org/docs/python/generated/pyarrow.schema.html#pyarrow.schema.

If not. All properties are serialized, and a properties column of type string is made.
"""
