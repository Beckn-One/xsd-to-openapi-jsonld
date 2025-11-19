# IEEE 2030.5 Schema Converters

Python functions to convert XSD and WADL files to various output formats.

## Features

### a) XSD to JSON-LD/SHACL
- **JSON-LD Context**: Maps XSD types/elements to semantic URIs
- **JSON-LD Schema**: Full RDF/OWL schema definitions
- **SHACL Shapes**: Validation shapes for JSON-LD data

### b) XSD + WADL to OpenAPI
- **OpenAPI 3.0 Spec**: Complete API specification with:
  - Schemas from XSD (184 types)
  - Paths from WADL (121 endpoints)
  - Request/response definitions
  - Query and path parameters

## Quick Start

### Run all examples:
```bash
./run.sh
```

### Python usage:

```python
from converters import (
    generate_jsonld_context,
    generate_jsonld_schema,
    generate_shacl_shapes,
    generate_openapi_spec
)

# Generate JSON-LD Context
generate_jsonld_context(
    xsd_file='test_inputs/sep.xsd',
    output_file='test_outputs/sep_context.jsonld',
    include_docs=True,
    include_enums=True,
    include_schema=True
)

# Generate SHACL Shapes
generate_shacl_shapes(
    xsd_file='test_inputs/sep.xsd',
    output_file='test_outputs/sep_shacl.jsonld',
    include_docs=True
)

# Generate OpenAPI from XSD only (schemas, no paths)
generate_openapi_spec(
    xsd_file='test_inputs/sep.xsd',
    output_file='test_outputs/sep_openapi_xsd_only.yaml'
)

# Generate OpenAPI from XSD + WADL (complete with paths)
generate_openapi_spec(
    xsd_file='test_inputs/sep.xsd',
    wadl_file='test_inputs/sep_wadl.xml',
    output_file='test_outputs/sep_openapi_complete.yaml',
    api_title='IEEE 2030.5 API',
    api_version='1.0.0'
)
```

## Functions

### `generate_jsonld_context(xsd_file, output_file=None, ...)`
Generates JSON-LD context file mapping XSD types to semantic URIs.

**Parameters:**
- `xsd_file`: Path to XSD file (required)
- `output_file`: Output file path (optional, returns dict if None)
- `include_docs`: Include documentation/descriptions (default: True)
- `include_enums`: Include enum values (default: True)
- `include_schema`: Include schema relationships (default: True)
- `shacl_file_url`: Optional URL to SHACL shapes file

**Returns:** dict or None (if output_file provided)

### `generate_jsonld_schema(xsd_file, output_file=None, ...)`
Generates full JSON-LD schema (RDF/OWL) with class hierarchies and properties.

**Parameters:**
- `xsd_file`: Path to XSD file (required)
- `output_file`: Output file path (optional)
- `include_docs`: Include documentation (default: True)
- `include_enums`: Include enum values (default: True)

**Returns:** dict or None (if output_file provided)

### `generate_shacl_shapes(xsd_file, output_file=None, ...)`
Generates SHACL shapes for validating JSON-LD data.

**Parameters:**
- `xsd_file`: Path to XSD file (required)
- `output_file`: Output file path (optional)
- `include_docs`: Include documentation (default: True)

**Returns:** dict or None (if output_file provided)

### `generate_openapi_spec(xsd_file, wadl_file=None, output_file=None, ...)`
Generates OpenAPI 3.0 specification.

**Parameters:**
- `xsd_file`: Path to XSD file (required)
- `wadl_file`: Path to WADL file (optional, adds paths if provided)
- `output_file`: Output file path (optional, auto-detects YAML/JSON from extension)
- `api_title`: API title (default: "IEEE 2030.5 API")
- `api_version`: API version (default: "1.0.0")
- `include_docs`: Include documentation (default: True)
- `include_enums`: Include enum values (default: True)

**Returns:** dict or None (if output_file provided)

**Note:** If `wadl_file` is provided, the OpenAPI spec will include:
- All API paths from WADL (e.g., `/edev/{id1}/dstat`)
- HTTP methods (GET, POST, PUT, DELETE, etc.)
- Request/response schemas
- Query and path parameters
- Server URL from WADL

## Output Files

Generated files are saved to `test_outputs/`:

- `sep_context.jsonld` - JSON-LD context (748 terms)
- `sep_schema.jsonld` - JSON-LD schema (RDF/OWL)
- `sep_shacl.jsonld` - SHACL validation shapes
- `sep_openapi_xsd_only.yaml` - OpenAPI with schemas only (no paths)
- `sep_openapi_complete.yaml` - OpenAPI with schemas + paths (184 schemas, 121 paths)
- `sep_openapi_complete.json` - Same as above in JSON format

## Requirements

- Python 3.6+
- PyYAML (optional, for YAML output): `pip install pyyaml`
- ruamel.yaml (optional, for YAML with comment support): `pip install ruamel.yaml`

**Note:** If `ruamel.yaml` is installed, generated YAML files will include helpful comments. If not, the converter falls back to `pyyaml` (which doesn't preserve comments).

## Structure

```
converters/
├── __init__.py              # Main entry points
├── core/                    # Core parsers
│   ├── xsd_parser.py        # XSD parser
│   └── wadl_parser.py       # WADL parser
├── jsonld/                  # JSON-LD generators
│   └── __init__.py
├── openapi/                 # OpenAPI generator
│   └── __init__.py
├── test_inputs/            # Input files
│   ├── sep.xsd
│   └── sep_wadl.xml
└── test_outputs/           # Generated files
```

