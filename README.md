# XSD to OpenAPI & JSON-LD Converter

**Transform legacy XML schemas into modern API specifications and semantic web formats.**

Have XML Schema (XSD) and WADL files from legacy systems? This tool automatically converts them into:
- **OpenAPI 3.0** specifications for modern REST APIs
- **JSON-LD** contexts for semantic web integration
- **SHACL** shapes for data validation

Perfect for modernizing IEEE 2030.5, OASIS, or any XML-based standards.

## Why This Exists

Legacy systems often define APIs using XML Schema (XSD) and WADL. Modern development requires:
- **OpenAPI specs** for API documentation, code generation, and tooling
- **JSON-LD** for semantic understanding and linked data
- **SHACL** for validation beyond basic JSON Schema

Manually converting 184+ types and 121+ endpoints is error-prone and time-consuming. This tool does it automatically, preserving documentation, enums, relationships, and validation rules.

## Quick Start

```bash
# Install dependencies (optional, for YAML support)
pip install pyyaml ruamel.yaml

# Run all examples
./test_run.sh
```

## Example Outputs

See `test_outputs/` for complete examples generated from IEEE 2030.5:

- **[`sep_openapi_complete.yaml`](/test_outputs/sep_openapi_complete.yaml)** - Full OpenAPI 3.0 spec with 184 schemas + 121 API paths
- **[`sep_context.jsonld`](/test_outputs/sep_context.jsonld)** - JSON-LD context mapping 748+ terms to semantic URIs
- **[`sep_shacl.jsonld`](/test_outputs/sep_shacl.jsonld)** - SHACL validation shapes for all types
- **[`sep_openapi_with_context.yaml`](/test_outputs/sep_openapi_with_context.yaml)** - OpenAPI with embedded JSON-LD context

## Usage

### Command Line

```bash
# Generate OpenAPI from XSD + WADL
python3 cli.py openapi input.xsd output.yaml --wadl-file input.wadl

# Generate JSON-LD context
python3 cli.py jsonld-context input.xsd output.jsonld

# Generate SHACL shapes
python3 cli.py shacl input.xsd output.jsonld
```

### Python API

```python
from converters import generate_openapi_spec, generate_jsonld_context

# Generate OpenAPI with embedded JSON-LD context
generate_openapi_spec(
    xsd_file='schema.xsd',
    wadl_file='api.wadl',
    output_file='api.yaml'
)

# Generate JSON-LD context
generate_jsonld_context(
    xsd_file='schema.xsd',
    output_file='context.jsonld'
)
```

## Features

✅ **Complete conversion** - All types, elements, attributes, and relationships  
✅ **Preserves documentation** - XSD annotations become OpenAPI descriptions  
✅ **Enum handling** - Enum values with descriptions and bitmask support  
✅ **Semantic web ready** - JSON-LD with RDF/OWL relationships  
✅ **Validation** - SHACL shapes for data validation  
✅ **Modern defaults** - Docs, enums, and context included by default (use `--exclude-*` to disable)

## What Gets Converted

| Input | Output | Use Case |
|-------|--------|----------|
| XSD types → | OpenAPI schemas | API documentation, code generation |
| XSD types → | JSON-LD context | Semantic web, linked data |
| XSD types → | SHACL shapes | Data validation |
| WADL paths → | OpenAPI paths | REST API specification |
| XSD docs → | OpenAPI descriptions | Developer documentation |
| XSD enums → | OpenAPI enums | Type-safe APIs |

## Requirements

- Python 3.6+
- Optional: `pyyaml` or `ruamel.yaml` for YAML output (recommended)

## License

See [LICENSE](LICENSE) file.

