"""
JSON-LD generators: context, schema, and SHACL shapes.
"""

from converters.core import XSDParser
from converters.generators import XSDGenerator


def generate_jsonld_context(xsd_file, output_file=None, include_docs=True, 
                           include_enums=True, include_schema=True, shacl_file_url=None):
    """Generate JSON-LD context from XSD file.
    
    Args:
        xsd_file: Path to XSD file
        output_file: Optional output file path (if None, returns dict)
        include_docs: Include documentation/descriptions
        include_enums: Include enum values
        include_schema: Include schema relationships
        shacl_file_url: Optional URL to SHACL shapes file
        
    Returns:
        dict: JSON-LD context or None if output_file is provided
    """
    parser = XSDParser()
    parser.parse(xsd_file)
    generator = XSDGenerator(parser)
    context = generator.generate_jsonld_context(
        include_docs=include_docs,
        include_enums=include_enums,
        include_schema=include_schema,
        shacl_file_url=shacl_file_url
    )
    
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(context, f, separators=(',', ':'))
        return None
    
    return context


def generate_jsonld_schema(xsd_file, output_file=None, include_docs=True, include_enums=True):
    """Generate JSON-LD schema (RDF/OWL) from XSD file.
    
    Args:
        xsd_file: Path to XSD file
        output_file: Optional output file path (if None, returns dict)
        include_docs: Include documentation/descriptions
        include_enums: Include enum values
        
    Returns:
        dict: JSON-LD schema or None if output_file is provided
    """
    parser = XSDParser()
    parser.parse(xsd_file)
    generator = XSDGenerator(parser)
    schema = generator.generate_jsonld_schema(
        include_docs=include_docs,
        include_enums=include_enums
    )
    
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(schema, f, separators=(',', ':'))
        return None
    
    return schema


def generate_shacl_shapes(xsd_file, output_file=None, include_docs=True, include_enums=True):
    """Generate SHACL shapes from XSD file with RDF ontology information.
    
    Args:
        xsd_file: Path to XSD file
        output_file: Optional output file path (if None, returns dict)
        include_docs: Include documentation/descriptions
        include_enums: Include enum values in RDF ontology
        
    Returns:
        dict: SHACL shapes with RDF ontology or None if output_file is provided
    """
    parser = XSDParser()
    parser.parse(xsd_file)
    generator = XSDGenerator(parser)
    shacl = generator.generate_shacl_shapes(include_docs=include_docs, include_enums=include_enums)
    
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(shacl, f, separators=(',', ':'))
        return None
    
    return shacl

