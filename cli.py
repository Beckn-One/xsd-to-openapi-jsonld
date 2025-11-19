#!/usr/bin/env python3
"""
CLI helper functions for XSD to OpenAPI/JSON-LD converters.
These functions accept command line arguments and execute converter operations.
"""

import argparse
import sys
import os
from pathlib import Path
from converters import (
    generate_jsonld_context,
    generate_jsonld_schema,
    generate_shacl_shapes,
    generate_openapi_spec
)


def cli_generate_jsonld_context(args):
    """CLI wrapper for generate_jsonld_context."""
    generate_jsonld_context(
        xsd_file=args.xsd_file,
        output_file=args.output_file,
        include_docs=args.include_docs,
        include_enums=args.include_enums,
        include_schema=args.include_schema,
        shacl_file_url=getattr(args, 'shacl_file_url', None)
    )
    if args.output_file:
        print(f'✓ Generated: {args.output_file}')


def cli_generate_jsonld_schema(args):
    """CLI wrapper for generate_jsonld_schema."""
    generate_jsonld_schema(
        xsd_file=args.xsd_file,
        output_file=args.output_file,
        include_docs=args.include_docs,
        include_enums=args.include_enums
    )
    if args.output_file:
        print(f'✓ Generated: {args.output_file}')


def cli_generate_shacl_shapes(args):
    """CLI wrapper for generate_shacl_shapes."""
    generate_shacl_shapes(
        xsd_file=args.xsd_file,
        output_file=args.output_file,
        include_docs=args.include_docs
    )
    if args.output_file:
        print(f'✓ Generated: {args.output_file}')


def cli_generate_openapi_spec(args):
    """CLI wrapper for generate_openapi_spec."""
    generate_openapi_spec(
        xsd_file=args.xsd_file,
        wadl_file=getattr(args, 'wadl_file', None),
        output_file=args.output_file,
        api_title=getattr(args, 'api_title', 'IEEE 2030.5 API'),
        api_version=getattr(args, 'api_version', '1.0.0'),
        include_docs=args.include_docs,
        include_enums=args.include_enums,
        include_context=args.include_context,
        context_output_file=getattr(args, 'context_output_file', None)
    )
    if args.output_file:
        if args.include_context and getattr(args, 'context_output_file', None):
            print(f'✓ Generated: {args.output_file}')
            print(f'✓ Generated: {args.context_output_file}')
        elif args.include_context:
            print(f'✓ Generated: {args.output_file} (with embedded context)')
        else:
            print(f'✓ Generated: {args.output_file}')


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='IEEE 2030.5 Schema Converters - CLI Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Command: jsonld-context
    parser_context = subparsers.add_parser(
        'jsonld-context',
        help='Generate JSON-LD Context'
    )
    parser_context.add_argument('xsd_file', help='Path to XSD file')
    parser_context.add_argument('output_file', help='Output file path')
    parser_context.add_argument('--exclude-docs', dest='include_docs', action='store_false',
                               help='Exclude documentation/descriptions (default: included)')
    parser_context.add_argument('--exclude-enums', dest='include_enums', action='store_false',
                               help='Exclude enum values (default: included)')
    parser_context.add_argument('--exclude-schema', dest='include_schema', action='store_false',
                               help='Exclude schema relationships (default: included)')
    parser_context.add_argument('--shacl-file-url', type=str, default=None,
                               help='Optional URL to SHACL shapes file')
    parser_context.set_defaults(
        include_docs=True,
        include_enums=True,
        include_schema=True,
        func=cli_generate_jsonld_context
    )
    
    # Command: jsonld-schema
    parser_schema = subparsers.add_parser(
        'jsonld-schema',
        help='Generate JSON-LD Schema (RDF/OWL)'
    )
    parser_schema.add_argument('xsd_file', help='Path to XSD file')
    parser_schema.add_argument('output_file', help='Output file path')
    parser_schema.add_argument('--exclude-docs', dest='include_docs', action='store_false',
                              help='Exclude documentation/descriptions (default: included)')
    parser_schema.add_argument('--exclude-enums', dest='include_enums', action='store_false',
                              help='Exclude enum values (default: included)')
    parser_schema.set_defaults(
        include_docs=True,
        include_enums=True,
        func=cli_generate_jsonld_schema
    )
    
    # Command: shacl
    parser_shacl = subparsers.add_parser(
        'shacl',
        help='Generate SHACL Shapes'
    )
    parser_shacl.add_argument('xsd_file', help='Path to XSD file')
    parser_shacl.add_argument('output_file', help='Output file path')
    parser_shacl.add_argument('--exclude-docs', dest='include_docs', action='store_false',
                             help='Exclude documentation/descriptions (default: included)')
    parser_shacl.set_defaults(
        include_docs=True,
        func=cli_generate_shacl_shapes
    )
    
    # Command: openapi
    parser_openapi = subparsers.add_parser(
        'openapi',
        help='Generate OpenAPI Specification'
    )
    parser_openapi.add_argument('xsd_file', help='Path to XSD file')
    parser_openapi.add_argument('output_file', help='Output file path')
    parser_openapi.add_argument('--wadl-file', type=str, default=None,
                               help='Path to WADL file (optional, adds paths if provided)')
    parser_openapi.add_argument('--api-title', type=str, default='IEEE 2030.5 API',
                               help='API title (default: IEEE 2030.5 API)')
    parser_openapi.add_argument('--api-version', type=str, default='1.0.0',
                               help='API version (default: 1.0.0)')
    parser_openapi.add_argument('--exclude-docs', dest='include_docs', action='store_false',
                               help='Exclude documentation/descriptions (default: included)')
    parser_openapi.add_argument('--exclude-enums', dest='include_enums', action='store_false',
                               help='Exclude enum values (default: included)')
    parser_openapi.add_argument('--exclude-context', dest='include_context', action='store_false',
                               help='Exclude JSON-LD context from OpenAPI spec (default: included)')
    parser_openapi.add_argument('--context-output-file', type=str, default=None,
                               help='Optional path to save context separately')
    parser_openapi.set_defaults(
        include_docs=True,
        include_enums=True,
        include_context=True,
        func=cli_generate_openapi_spec
    )
    
    return parser


def main():
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the command
    args.func(args)


if __name__ == '__main__':
    main()

