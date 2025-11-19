"""
OpenAPI generator: combines XSD (schemas) and WADL (paths) to generate OpenAPI spec.
"""

from converters.core import XSDParser, WADLParser
from converters.generators import XSDGenerator

# Try to import ruamel.yaml first (preserves comments), fallback to pyyaml
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
    HAS_RUAMEL_YAML = True
    HAS_YAML = True
except ImportError:
    HAS_RUAMEL_YAML = False
    try:
        import yaml
        HAS_YAML = True
    except ImportError:
        HAS_YAML = False


def _enrich_schemas_with_context(schemas, context):
    """Enrich OpenAPI schemas with enum information from JSON-LD context.
    
    This adds enum descriptions to schema properties, making it easier
    for developers to understand what enum values mean.
    """
    def enrich_property(prop_schema, prop_name):
        """Enrich a single property schema with context information."""
        if not isinstance(prop_schema, dict):
            return
        
        # Check if this property has enum values in context
        if prop_name in context:
            prop_context = context[prop_name]
            
            # If context has @enum, add it to the property description
            if isinstance(prop_context, dict) and "@enum" in prop_context:
                enum_info = prop_context["@enum"]
                if isinstance(enum_info, dict):
                    # Build enum description
                    enum_desc = []
                    for key, desc in enum_info.items():
                        enum_desc.append(f"  - {key}: {desc}")
                    
                    if enum_desc:
                        existing_desc = prop_schema.get("description", "")
                        enum_text = "\nEnum values:\n" + "\n".join(enum_desc)
                        prop_schema["description"] = existing_desc + enum_text if existing_desc else enum_text.strip()
        
        # Recursively process nested objects
        if "properties" in prop_schema:
            for nested_name, nested_prop in prop_schema["properties"].items():
                enrich_property(nested_prop, nested_name)
        
        # Process array items
        if "items" in prop_schema:
            enrich_property(prop_schema["items"], None)
    
    # Process all schemas
    for schema_name, schema in schemas.items():
        if isinstance(schema, dict) and "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                enrich_property(prop_schema, prop_name)


def generate_openapi_spec(xsd_file, wadl_file=None, output_file=None, 
                         api_title="IEEE 2030.5 API", api_version="1.0.0",
                         include_docs=True, include_enums=True,
                         include_context=False, context_output_file=None):
    """Generate OpenAPI 3.0 specification from XSD and optionally WADL files.
    
    Args:
        xsd_file: Path to XSD file (required)
        wadl_file: Path to WADL file (optional, adds paths if provided)
        output_file: Optional output file path (if None, returns dict)
        api_title: API title
        api_version: API version
        include_docs: Include documentation/descriptions
        include_enums: Include enum values
        include_context: If True, embed JSON-LD context in OpenAPI spec as x-jsonld-context
        context_output_file: Optional path to save context separately (if provided)
        
    Returns:
        dict: OpenAPI specification or None if output_file is provided
    """
    # Parse XSD and generate JSON Schema
    parser = XSDParser()
    parser.parse(xsd_file)
    generator = XSDGenerator(parser)
    
    json_schema = generator.generate_json_schema(
        include_docs=include_docs,
        include_enums=include_enums
    )
    
    # Generate JSON-LD context if requested
    jsonld_context = None
    if include_context or context_output_file:
        jsonld_context = generator.generate_jsonld_context(
            include_docs=include_docs,
            include_enums=include_enums,
            include_schema=True
        )
        
        # Save context to separate file if requested
        if context_output_file:
            import json
            import os
            with open(context_output_file, 'w') as f:
                json.dump(jsonld_context, f, indent=2)
            
            # If context_output_file is provided, we'll reference it instead of embedding
            # Store the relative path for reference
            if output_file:
                # Calculate relative path from output_file to context_output_file
                output_dir = os.path.dirname(os.path.abspath(output_file))
                context_path = os.path.abspath(context_output_file)
                try:
                    rel_path = os.path.relpath(context_path, output_dir)
                except ValueError:
                    # If paths are on different drives (Windows), use absolute path
                    rel_path = context_output_file
            else:
                rel_path = context_output_file
    
    # Convert definitions to components/schemas and fix $ref paths
    schemas = json_schema.get("definitions", {})
    
    # Fix $ref paths from #/definitions/ to #/components/schemas/
    def fix_refs(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/definitions/"):
                    obj["$ref"] = ref.replace("#/definitions/", "#/components/schemas/")
            for value in obj.values():
                fix_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                fix_refs(item)
    
    fix_refs(schemas)
    
    # Build OpenAPI spec
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": api_title,
            "version": api_version,
            "description": "API specification generated from IEEE 2030.5 XSD schema" + 
                          (" and WADL" if wadl_file else "") +
                          ". This OpenAPI spec validates JSON structure. For JSON-LD semantic validation, use SHACL shapes.",
            "contact": {
                "name": "IEEE 2030.5",
                "url": "https://standards.ieee.org/ieee/2030.5/"
            }
        },
        "servers": [
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ],
        "paths": {},
        "components": {
            "schemas": schemas
        }
    }
    
    # Handle JSON-LD context: embed or reference
    # Following IETF draft: https://datatracker.ietf.org/doc/draft-polli-restapi-ld-keywords/
    # x-jsonld-context can be either:
    #   1. An object (the context itself) - when embedding
    #   2. A URL/string (reference to external file) - when referencing
    if include_context and jsonld_context:
        if context_output_file:
            # Reference external context file (x-jsonld-context can be a URL/string)
            import os
            if output_file:
                output_dir = os.path.dirname(os.path.abspath(output_file))
                context_path = os.path.abspath(context_output_file)
                try:
                    rel_path = os.path.relpath(context_path, output_dir)
                    # Use relative path as URL reference
                    openapi["x-jsonld-context"] = rel_path
                except ValueError:
                    # If paths are on different drives (Windows), use absolute path
                    openapi["x-jsonld-context"] = context_output_file
            else:
                openapi["x-jsonld-context"] = context_output_file
        else:
            # Embed context directly in OpenAPI spec (x-jsonld-context as object)
            # This follows the IETF standard where x-jsonld-context can be a JSON object
            openapi["x-jsonld-context"] = jsonld_context.get("@context", {})
        
        # Add enum information to schema descriptions where helpful
        # This makes enums self-serve in the OpenAPI docs (works for both embedded and referenced)
        if include_enums:
            _enrich_schemas_with_context(schemas, jsonld_context.get("@context", {}))
    
    # Add paths from WADL if provided
    if wadl_file:
        wadl_parser = WADLParser()
        wadl_parser.parse(wadl_file)
        
        # Update server URL from WADL
        if wadl_parser.base_url:
            openapi["servers"] = [{
                "url": wadl_parser.base_url.rstrip('/'),
                "description": "IEEE 2030.5 API Server"
            }]
        
        # Convert WADL resources to OpenAPI paths
        for resource in wadl_parser.resources:
            path = resource['path']
            if not path.startswith('/'):
                path = '/' + path
            
            # Initialize path if not exists
            if path not in openapi["paths"]:
                openapi["paths"][path] = {}
            
            # Convert methods to operations
            for method in resource['methods']:
                method_name = method['name'].lower()
                if method_name not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    continue
                
                operation = {
                    "operationId": method['id'],
                    "summary": f"{method_name.upper()} {resource['id']}",
                    "tags": [resource['id']]
                }
                
                # Add description if available
                if resource.get('description'):
                    operation["description"] = resource['description']
                
                # Add request body for POST, PUT, PATCH
                if method_name in ['post', 'put', 'patch'] and method.get('request'):
                    request = method['request']
                    if request.get('representations'):
                        operation["requestBody"] = {
                            "required": True,
                            "content": {}
                        }
                        for repr_info in request['representations']:
                            media_type = repr_info.get('mediaType', 'application/json')
                            element = repr_info.get('element', '').replace('sep:', '')
                            
                            content_schema = {}
                            if element and element in schemas:
                                content_schema = {"$ref": f"#/components/schemas/{element}"}
                            else:
                                content_schema = {"type": "object"}
                            
                            operation["requestBody"]["content"][media_type] = {
                                "schema": content_schema
                            }
                
                # Add responses
                operation["responses"] = {}
                if method.get('responses'):
                    for response in method['responses']:
                        status = response.get('status', '200')
                        response_def = {
                            "description": f"{status} response"
                        }
                        
                        # Add response content if available
                        if response.get('representations'):
                            response_def["content"] = {}
                            for repr_info in response['representations']:
                                media_type = repr_info.get('mediaType', 'application/json')
                                element = repr_info.get('element', '').replace('sep:', '')
                                
                                content_schema = {}
                                if element and element in schemas:
                                    content_schema = {"$ref": f"#/components/schemas/{element}"}
                                else:
                                    content_schema = {"type": "object"}
                                
                                response_def["content"][media_type] = {
                                    "schema": content_schema
                                }
                        
                        operation["responses"][status] = response_def
                else:
                    # Default response
                    operation["responses"]["200"] = {
                        "description": "Success"
                    }
                
                # Add query parameters if GET request
                if method_name == 'get' and method.get('request'):
                    params = method['request'].get('parameters', [])
                    if params:
                        operation["parameters"] = []
                        for param in params:
                            param_def = {
                                "name": param['name'],
                                "in": param.get('style', 'query'),
                                "required": param.get('required', False),
                                "schema": {"type": "integer" if 'int' in param.get('type', '') else "string"}
                            }
                            if param.get('description'):
                                param_def["description"] = param['description']
                            operation["parameters"].append(param_def)
                
                # Add path parameters from resource path
                path_params = []
                import re
                path_param_matches = re.findall(r'\{(\w+)\}', path)
                if path_param_matches:
                    if "parameters" not in operation:
                        operation["parameters"] = []
                    for param_name in path_param_matches:
                        operation["parameters"].append({
                            "name": param_name,
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        })
                
                openapi["paths"][path][method_name] = operation
    
    # Write or return
    if output_file:
        output_format = 'yaml' if output_file.endswith(('.yaml', '.yml')) else 'json'
        
        if output_format == 'yaml' and HAS_YAML:
            if HAS_RUAMEL_YAML:
                # Use ruamel.yaml to preserve comments and add helpful ones
                yaml_writer = YAML()
                yaml_writer.preserve_quotes = True
                yaml_writer.width = 4096  # Prevent line wrapping
                yaml_writer.default_flow_style = False
                
                # Add helpful comments to the OpenAPI spec
                openapi_with_comments = _add_yaml_comments(openapi, jsonld_context, include_context, context_output_file)
                
                with open(output_file, 'w') as f:
                    yaml_writer.dump(openapi_with_comments, f)
            else:
                # Fallback to pyyaml (no comment support)
                with open(output_file, 'w') as f:
                    yaml.dump(openapi, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        else:
            import json
            with open(output_file, 'w') as f:
                json.dump(openapi, f, indent=2)
        
        # Print summary
        if include_context:
            if context_output_file:
                print(f"✓ Referenced JSON-LD context file in OpenAPI spec: {context_output_file}")
            else:
                print(f"✓ Embedded JSON-LD context in OpenAPI spec")
        elif context_output_file:
            print(f"✓ Saved JSON-LD context to: {context_output_file}")
        
        return None
    
    return openapi


def _add_yaml_comments(openapi, jsonld_context, include_context, context_output_file):
    """Add helpful comments to OpenAPI YAML structure using ruamel.yaml."""
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    
    # Convert dict to CommentedMap to allow comments
    def add_comments_recursive(obj, path="", parent_dict=None):
        if isinstance(obj, dict):
            commented = CommentedMap()
            # First pass: add all keys and values
            for key, value in obj.items():
                commented[key] = add_comments_recursive(value, f"{path}.{key}", obj)
                
                # Add comments based on key
                if key == "openapi":
                    commented.yaml_set_comment_before_after_key(key, before="OpenAPI Specification Version")
                elif key == "info":
                    commented.yaml_set_comment_before_after_key(key, before="API Information")
                elif key == "servers":
                    commented.yaml_set_comment_before_after_key(key, before="API Server URLs")
                elif key == "paths":
                    commented.yaml_set_comment_before_after_key(key, before="API Endpoints (from WADL)")
                elif key == "components":
                    commented.yaml_set_comment_before_after_key(key, before="Reusable Components")
                elif key == "schemas":
                    commented.yaml_set_comment_before_after_key(key, before="JSON Schema Definitions (from XSD)")
                elif key == "x-jsonld-context":
                    if include_context:
                        if context_output_file:
                            commented.yaml_set_comment_before_after_key(
                                key, 
                                before="JSON-LD Context Reference (IETF draft: draft-polli-restapi-ld-keywords)\n"
                                       "This references an external context file for semantic understanding of API terms."
                            )
                        else:
                            commented.yaml_set_comment_before_after_key(
                                key,
                                before="JSON-LD Context (IETF draft: draft-polli-restapi-ld-keywords)\n"
                                       "Embedded context for semantic understanding of API terms, enum values, and type relationships."
                            )
                elif key == "x-enum-descriptions":
                    # Add comment explaining this extension
                    commented.yaml_set_comment_before_after_key(
                        key,
                        before="Enum value descriptions (bit positions and their meanings)"
                    )
            
            # Second pass: add enum comments if x-enum-descriptions exists
            if "enum" in commented and "x-enum-descriptions" in commented:
                enum_value = commented["enum"]
                enum_descriptions = commented["x-enum-descriptions"]
                if isinstance(enum_value, list):
                    commented_seq = CommentedSeq()
                    for item in enum_value:
                        commented_seq.append(item)
                        # Add comment for this enum value
                        item_str = str(item)
                        if item_str in enum_descriptions:
                            desc = enum_descriptions[item_str]
                            idx = len(commented_seq) - 1
                            commented_seq.yaml_add_eol_comment(desc, idx)
                    commented["enum"] = commented_seq
            
            return commented
        elif isinstance(obj, list):
            commented_list = CommentedSeq()
            for item in obj:
                commented_list.append(add_comments_recursive(item, path, parent_dict))
            return commented_list
        else:
            return obj
    
    commented_openapi = add_comments_recursive(openapi)
    
    # Add top-level comment
    if isinstance(commented_openapi, CommentedMap):
        commented_openapi.yaml_set_start_comment(
            "IEEE 2030.5 OpenAPI Specification\n"
            "Generated from XSD schema and WADL definition\n"
            "This spec includes JSON-LD context for semantic understanding of API terms"
        )
    
    return commented_openapi

