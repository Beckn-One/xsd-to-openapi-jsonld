#!/bin/bash

# Script to run converter examples
# Usage: ./run.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
INPUT_DIR="test_inputs"
OUTPUT_DIR="test_outputs"

echo -e "${BLUE}=== IEEE 2030.5 Schema Converters ===${NC}\n"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Example 1: Generate JSON-LD Context
echo -e "${GREEN}Example 1: Generating JSON-LD Context${NC}"
python3 cli.py jsonld-context \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_context.jsonld"

# Example 2: Generate JSON-LD Schema
echo -e "\n${GREEN}Example 2: Generating JSON-LD Schema (RDF/OWL)${NC}"
python3 cli.py jsonld-schema \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_schema.jsonld"

# Example 3: Generate SHACL Shapes
echo -e "\n${GREEN}Example 3: Generating SHACL Shapes${NC}"
python3 cli.py shacl \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_shacl.jsonld"

# Example 4: Generate OpenAPI from XSD only (no paths)
echo -e "\n${GREEN}Example 4: Generating OpenAPI Spec (XSD only - schemas only)${NC}"
python3 cli.py openapi \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_openapi_xsd_only.yaml" \
    --api-title "IEEE 2030.5 API" \
    --api-version "1.0.0"

# Example 5: Generate OpenAPI from XSD + WADL (with paths)
echo -e "\n${GREEN}Example 5: Generating OpenAPI Spec (XSD + WADL - with paths)${NC}"
python3 cli.py openapi \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_openapi_complete.yaml" \
    --wadl-file "$INPUT_DIR/sep_wadl.xml" \
    --api-title "IEEE 2030.5 API" \
    --api-version "1.0.0"

# Example 6: Generate OpenAPI as JSON
echo -e "\n${GREEN}Example 6: Generating OpenAPI Spec as JSON${NC}"
python3 cli.py openapi \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_openapi_complete.json" \
    --wadl-file "$INPUT_DIR/sep_wadl.xml" \
    --api-title "IEEE 2030.5 API" \
    --api-version "1.0.0"

# Example 7: Generate Context with SHACL link, so that shacl grammer can be used to validate the data
echo -e "\n${GREEN}Example 7: Generating JSON-LD Context with SHACL link${NC}"
python3 cli.py jsonld-context \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_context_with_shacl.jsonld" \
    --shacl-file-url "https://example.com/sep_shacl.jsonld"

# Example 8: Generate OpenAPI with embedded JSON-LD context
echo -e "\n${GREEN}Example 8: Generating OpenAPI with embedded JSON-LD context${NC}"
python3 cli.py openapi \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_openapi_with_embedded_context.yaml" \
    --wadl-file "$INPUT_DIR/sep_wadl.xml" \
    --api-title "IEEE 2030.5 API" \
    --api-version "1.0.0"

# Example 9: Generate OpenAPI with context embedded AND saved separately
echo -e "\n${GREEN}Example 9: Generating OpenAPI with context (embedded + separate file)${NC}"
python3 cli.py openapi \
    "$INPUT_DIR/sep.xsd" \
    "$OUTPUT_DIR/sep_openapi_with_linked_context.yaml" \
    --wadl-file "$INPUT_DIR/sep_wadl.xml" \
    --api-title "IEEE 2030.5 API" \
    --api-version "1.0.0" \
    --context-output-file "$OUTPUT_DIR/sep_context_linked_to_openapi.jsonld"

echo -e "\n${BLUE}=== All conversions complete! ===${NC}"
echo -e "${YELLOW}Output files are in: $OUTPUT_DIR${NC}\n"

# List generated files
echo -e "${GREEN}Generated files:${NC}"
ls -lh "$OUTPUT_DIR" | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'

