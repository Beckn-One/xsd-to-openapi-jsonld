"""
Generation logic for JSON-LD, SHACL, and JSON Schema from parsed XSD.
This module is self-contained and uses the XSDParser from converters.core.
"""

from converters.core import XSDParser


class XSDGenerator:
    """Generate various output formats from parsed XSD data."""
    
    def __init__(self, parser):
        """Initialize with an XSDParser instance.
        
        Args:
            parser: XSDParser instance with parsed XSD data
        """
        self.parser = parser
        self.base_uri = parser.base_uri
        self.types = parser.types
        self.elements = parser.elements
    
    def generate_jsonld_context(self, include_docs=True, include_enums=True, 
                               include_schema=True, shacl_file_url=None):
        """Generate a JSON-LD context from the parsed XSD.
        
        Args:
            include_docs: If True, documentation is included (note: rdfs:comment is not valid in context, so this parameter is kept for API compatibility but doesn't affect context)
            include_enums: If True, enum values are included (note: @enum is not valid in context, so this parameter is kept for API compatibility but doesn't affect context)
            include_schema: If True, include properties in the context (RDF relationships are not included in context)
            shacl_file_url: Optional URL to SHACL shapes file (for validator discovery)
        """
        context = {
            "@context": {
                "@vocab": self.base_uri,
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#"
            }
        }
        
        # Add SHACL shapes link if provided
        if shacl_file_url:
            context["@shacl"] = shacl_file_url
        
        # Track properties by their owning type
        properties_by_type = {}
        
        # Add all types to context
        # Use relative IRIs since @vocab is set - just "@id" string instead of full object
        for type_name, type_info in self.types.items():
            # Note: RDF relationships (rdfs:subClassOf, rdfs:comment, @enum, etc.) are not valid in JSON-LD context
            # They belong in the JSON-LD schema file instead
            # Using relative IRI shorthand: "@id" since term is in @vocab namespace
            context["@context"][type_name] = "@id"
            
            # Track properties for this type
            if include_schema:
                properties_by_type[type_name] = []
                # Add elements as properties
                for elem in type_info.get('elements', []):
                    properties_by_type[type_name].append({
                        'name': elem['name'],
                        'type': elem.get('type'),
                        'documentation': elem.get('documentation')
                    })
                # Add attributes as properties
                for attr in type_info.get('attributes', []):
                    properties_by_type[type_name].append({
                        'name': attr['name'],
                        'type': attr.get('type'),
                        'default': attr.get('default'),
                        'documentation': attr.get('documentation')
                    })
        
        # Add properties (without RDF relationships - those belong in schema, not context)
        if include_schema:
            for type_name, properties in properties_by_type.items():
                for prop in properties:
                    prop_name = prop['name']
                    if prop_name not in context["@context"]:
                        # Note: RDF relationships (rdfs:domain, rdfs:range, rdfs:comment, OWL cardinality, @default)
                        # are not valid in JSON-LD context - they belong in the JSON-LD schema file
                        # Using relative IRI shorthand: "@id" since term is in @vocab namespace
                        context["@context"][prop_name] = "@id"
        
        # Add all elements to context
        for elem_name, elem_info in self.elements.items():
            if elem_name not in context["@context"]:
                # Note: rdfs:comment is not valid in JSON-LD context term definitions
                # Documentation belongs in the JSON-LD schema file instead
                # Using relative IRI shorthand: "@id" since term is in @vocab namespace
                context["@context"][elem_name] = "@id"
        
        # Add common XSD types
        xsd_types = {
            "string": "xsd:string",
            "int": "xsd:int",
            "long": "xsd:long",
            "boolean": "xsd:boolean",
            "unsignedByte": "xsd:unsignedByte",
            "unsignedShort": "xsd:unsignedShort",
            "unsignedInt": "xsd:unsignedInt",
            "unsignedLong": "xsd:unsignedLong",
            "byte": "xsd:byte",
            "short": "xsd:short",
            "anyURI": "xsd:anyURI",
            "hexBinary": "xsd:hexBinary"
        }
        
        for xsd_type, xsd_uri in xsd_types.items():
            if xsd_type not in context["@context"]:
                context["@context"][xsd_type] = xsd_uri
        
        return context
    
    def generate_jsonld_schema(self, include_docs=True, include_enums=True):
        """Generate JSON-LD schema definitions (RDF/OWL style)."""
        schema = {
            "@context": {
                "@vocab": self.base_uri,
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "owl": "http://www.w3.org/2002/07/owl#"
            },
            "@graph": []
        }
        
        # Generate schema for each type
        for type_name, type_info in self.types.items():
            type_node = {
                "@id": f"{self.base_uri}{type_name}",
                "@type": "rdfs:Class"
            }
            
            # Add documentation
            if include_docs and type_info.get('documentation'):
                type_node["rdfs:comment"] = type_info['documentation']
            
            # Add inheritance
            if type_info.get('base'):
                base_type = type_info['base'].replace('xs:', '')
                if base_type in self.types:
                    type_node["rdfs:subClassOf"] = {
                        "@id": f"{self.base_uri}{base_type}"
                    }
            
            # Add enum values
            if include_enums and type_info.get('enum_values'):
                type_node["@enum"] = type_info['enum_values']
            
            schema["@graph"].append(type_node)
        
        return schema
    
    def generate_shacl_shapes(self, include_docs=True, include_enums=True):
        """Generate SHACL shapes for validation with RDF ontology information."""
        shacl = {
            "@context": {
                "@vocab": self.base_uri,
                "sh": "http://www.w3.org/ns/shacl#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "owl": "http://www.w3.org/2002/07/owl#"
            },
            "@graph": []
        }
        
        # Track properties by their owning type for domain information
        properties_by_type = {}
        
        # Generate shapes for each type
        for type_name, type_info in self.types.items():
            if not type_info.get('elements') and not type_info.get('attributes'):
                continue
            
            # Use relative IRIs since @vocab is set
            shape = {
                "@id": f"{type_name}Shape",
                "@type": "sh:NodeShape",
                "sh:targetClass": {
                    "@id": type_name
                }
            }
            
            if include_docs and type_info.get('documentation'):
                shape["rdfs:comment"] = type_info['documentation']
            
            properties = []
            properties_by_type[type_name] = []
            
            # Add element properties
            for elem in type_info.get('elements', []):
                elem_type = elem.get('type', '').replace('xs:', '')
                enum_values = None
                enum_ranges = None
                if elem_type in self.types:
                    type_info_elem = self.types[elem_type]
                    enum_values = type_info_elem.get('enum_values')
                    enum_ranges = type_info_elem.get('enum_ranges')
                elif elem.get('enum_values'):
                    enum_values = elem.get('enum_values')
                    enum_ranges = elem.get('enum_ranges')
                
                prop_shape = self._create_property_shape(
                    elem['name'],
                    elem.get('type'),
                    elem.get('minOccurs', '1'),
                    elem.get('maxOccurs', '1'),
                    elem.get('documentation') if include_docs else None,
                    None,
                    enum_values,
                    enum_ranges
                )
                if prop_shape:
                    properties.append(prop_shape)
                    properties_by_type[type_name].append({
                        'name': elem['name'],
                        'type': elem.get('type'),
                        'minOccurs': elem.get('minOccurs', '1'),
                        'maxOccurs': elem.get('maxOccurs', '1'),
                        'documentation': elem.get('documentation')
                    })
            
            # Add attribute properties
            for attr in type_info.get('attributes', []):
                min_occurs = '1' if attr.get('use') == 'required' else '0'
                attr_type = attr.get('type', '').replace('xs:', '')
                enum_values = None
                enum_ranges = None
                if attr_type in self.types:
                    type_info_attr = self.types[attr_type]
                    enum_values = type_info_attr.get('enum_values')
                    enum_ranges = type_info_attr.get('enum_ranges')
                
                prop_shape = self._create_property_shape(
                    attr['name'],
                    attr.get('type'),
                    min_occurs,
                    '1',
                    attr.get('documentation') if include_docs else None,
                    attr.get('default'),
                    enum_values,
                    enum_ranges
                )
                if prop_shape:
                    properties.append(prop_shape)
                    properties_by_type[type_name].append({
                        'name': attr['name'],
                        'type': attr.get('type'),
                        'minOccurs': min_occurs,
                        'maxOccurs': '1',
                        'default': attr.get('default'),
                        'documentation': attr.get('documentation')
                    })
            
            if properties:
                shape["sh:property"] = properties
            
            shacl["@graph"].append(shape)
        
        # Add RDF ontology information (classes and properties)
        # This is valid in SHACL files since they use @graph
        
        # Add class definitions with inheritance
        # Use relative IRIs since @vocab is set
        for type_name, type_info in self.types.items():
            class_node = {
                "@id": type_name,
                "@type": "rdfs:Class"
            }
            
            # Add documentation
            if include_docs and type_info.get('documentation'):
                class_node["rdfs:comment"] = type_info['documentation']
            
            # Add inheritance (rdfs:subClassOf)
            if type_info.get('base'):
                base_type = type_info['base'].replace('xs:', '')
                if base_type in self.types:
                    class_node["rdfs:subClassOf"] = {
                        "@id": base_type
                    }
            
            # Add enum values
            if include_enums and type_info.get('enum_values'):
                class_node["@enum"] = type_info['enum_values']
            
            shacl["@graph"].append(class_node)
        
        # Add property definitions with domain and range
        # Use relative IRIs since @vocab is set
        for type_name, properties in properties_by_type.items():
            for prop in properties:
                prop_name = prop['name']
                prop_node = {
                    "@id": prop_name,
                    "@type": "rdf:Property"
                }
                
                # Add domain (which type this property belongs to)
                prop_node["rdfs:domain"] = {
                    "@id": type_name
                }
                
                # Add range (what type the property value is)
                prop_type = prop.get('type', '').replace('xs:', '')
                if prop_type:
                    if prop_type in self.types:
                        prop_node["rdfs:range"] = {
                            "@id": prop_type
                        }
                    elif prop_type in ['string', 'int', 'long', 'boolean', 'unsignedByte', 
                                      'unsignedShort', 'unsignedInt', 'unsignedLong', 
                                      'byte', 'short', 'anyURI', 'hexBinary']:
                        prop_node["rdfs:range"] = f"xsd:{prop_type}"
                
                # Add documentation
                if include_docs and prop.get('documentation'):
                    prop_node["rdfs:comment"] = prop['documentation']
                
                # Add cardinality constraints using OWL properties
                min_occurs = prop.get('minOccurs', '1')
                max_occurs = prop.get('maxOccurs', '1')
                
                min_val = int(min_occurs) if min_occurs.isdigit() else 0
                if min_val == 0:
                    prop_node["owl:minCardinality"] = 0
                elif min_val > 1:
                    prop_node["owl:minCardinality"] = min_val
                
                if max_occurs != '1':
                    if max_occurs != 'unbounded':
                        max_val = int(max_occurs) if max_occurs.isdigit() else 1
                        if max_val > 1:
                            prop_node["owl:maxCardinality"] = max_val
                
                shacl["@graph"].append(prop_node)
        
        return shacl
    
    def _create_property_shape(self, prop_name, prop_type, min_occurs, max_occurs, 
                              documentation=None, default_value=None, enum_values=None, enum_ranges=None):
        """Create a SHACL property shape."""
        # Use relative IRI since @vocab is set
        prop_shape = {
            "sh:path": {
                "@id": prop_name
            }
        }
        
        # Determine if this is a numeric type for min/max constraints
        is_numeric = False
        prop_type_clean = prop_type.replace('xs:', '') if prop_type else ''
        numeric_types = ['Int8', 'Int16', 'Int32', 'Int48', 'Int64', 
                       'UInt8', 'UInt16', 'UInt32', 'UInt40', 'UInt48', 'UInt64',
                       'int', 'long', 'unsignedByte', 'unsignedShort', 
                       'unsignedInt', 'unsignedLong', 'byte', 'short']
        
        if prop_type_clean in numeric_types:
            is_numeric = True
        elif prop_type_clean in self.types:
            type_info = self.types[prop_type_clean]
            base_type = type_info.get('base') or type_info.get('restriction')
            if base_type:
                base_clean = base_type.replace('xs:', '')
                if base_clean in numeric_types:
                    is_numeric = True
        
        # Only add enum constraint (sh:in) if there are NO ranges
        # If there are ranges, the type allows any value in the range, so we shouldn't restrict with sh:in
        if enum_values and not enum_ranges:
            enum_list = []
            for key, desc in enum_values.items():
                if is_numeric:
                    try:
                        enum_list.append(int(key))
                    except:
                        enum_list.append(key)
                else:
                    enum_list.append(key)
            
            if enum_list:
                prop_shape["sh:in"] = enum_list
        
        # Add cardinality
        min_val = int(min_occurs) if min_occurs.isdigit() else 0
        if min_val > 0:
            prop_shape["sh:minCount"] = min_val
        
        if max_occurs != 'unbounded':
            max_val = int(max_occurs) if max_occurs.isdigit() else 1
            if max_val > 0:
                prop_shape["sh:maxCount"] = max_val
        
        # Add min/max constraints for integer types (when there are ranges or no enum constraint)
        if is_numeric:
            # Check base type if prop_type_clean is a complex type
            base_type_for_constraints = prop_type_clean
            if prop_type_clean in self.types:
                type_info = self.types[prop_type_clean]
                base_type = type_info.get('base') or type_info.get('restriction')
                if base_type:
                    base_type_for_constraints = base_type.replace('xs:', '')
            
            if 'UInt8' in base_type_for_constraints or base_type_for_constraints == 'unsignedByte':
                prop_shape["sh:minInclusive"] = 0
                prop_shape["sh:maxInclusive"] = 255
            elif 'UInt16' in base_type_for_constraints or base_type_for_constraints == 'unsignedShort':
                prop_shape["sh:minInclusive"] = 0
                prop_shape["sh:maxInclusive"] = 65535
            elif 'UInt32' in base_type_for_constraints or base_type_for_constraints == 'unsignedInt':
                prop_shape["sh:minInclusive"] = 0
                prop_shape["sh:maxInclusive"] = 4294967295
        
        # Add datatype or node
        if prop_type:
            prop_type_clean = prop_type.replace('xs:', '')
            xsd_type_map = {
                'string': 'xsd:string',
                'int': 'xsd:integer',
                'long': 'xsd:long',
                'boolean': 'xsd:boolean',
                'unsignedByte': 'xsd:unsignedByte',
                'unsignedShort': 'xsd:unsignedShort',
                'unsignedInt': 'xsd:unsignedInt',
                'unsignedLong': 'xsd:unsignedLong',
                'byte': 'xsd:byte',
                'short': 'xsd:short',
                'anyURI': 'xsd:anyURI',
                'hexBinary': 'xsd:hexBinary'
            }
            
            if prop_type_clean in xsd_type_map:
                prop_shape["sh:datatype"] = xsd_type_map[prop_type_clean]
            elif prop_type_clean in self.types:
                type_info = self.types[prop_type_clean]
                has_elements = bool(type_info.get('elements'))
                has_attributes = bool(type_info.get('attributes'))
                
                if has_elements or has_attributes:
                    # Use relative IRI since @vocab is set
                    prop_shape["sh:node"] = {
                        "@id": f"{prop_type_clean}Shape"
                    }
                else:
                    base_type = type_info.get('base') or type_info.get('restriction')
                    if base_type:
                        base_clean = base_type.replace('xs:', '')
                        if base_clean in xsd_type_map:
                            prop_shape["sh:datatype"] = xsd_type_map[base_clean]
                        elif 'Int' in base_clean or 'UInt' in base_clean:
                            prop_shape["sh:datatype"] = "xsd:integer"
                        elif 'String' in base_clean:
                            prop_shape["sh:datatype"] = "xsd:string"
                        else:
                            prop_shape["sh:datatype"] = "xsd:string"
            else:
                if 'Int' in prop_type_clean or 'UInt' in prop_type_clean:
                    prop_shape["sh:datatype"] = "xsd:integer"
                elif 'String' in prop_type_clean:
                    prop_shape["sh:datatype"] = "xsd:string"
        
        if documentation:
            prop_shape["rdfs:comment"] = documentation
        
        if default_value:
            prop_shape["sh:defaultValue"] = default_value
        
        return prop_shape
    
    def generate_json_schema(self, include_docs=True, include_enums=True):
        """Generate JSON Schema (for OpenAPI/JSON validation)."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": f"{self.base_uri}schema.json",
            "title": "IEEE 2030.5 Schema",
            "description": "JSON Schema generated from IEEE 2030.5 XSD",
            "definitions": {}
        }
        
        # Generate schemas for each type
        for type_name, type_info in self.types.items():
            if not type_info.get('elements') and not type_info.get('attributes'):
                continue
            
            type_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            if include_docs and type_info.get('documentation'):
                type_schema["description"] = type_info['documentation']
            
            # Add properties from elements
            for elem in type_info.get('elements', []):
                enum_values = elem.get('enum_values')
                enum_ranges = elem.get('enum_ranges')
                if enum_values is None or enum_ranges is None:
                    elem_type = elem.get('type', '').replace('xs:', '')
                    if include_enums and elem_type in self.types:
                        type_info_elem = self.types[elem_type]
                        if enum_values is None:
                            enum_values = type_info_elem.get('enum_values')
                        if enum_ranges is None:
                            enum_ranges = type_info_elem.get('enum_ranges')
                
                # Get type documentation for bitmask detection
                elem_type = elem.get('type', '').replace('xs:', '')
                type_doc = None
                if elem_type in self.types:
                    type_doc = self.types[elem_type].get('documentation', '')
                
                prop_schema = self._create_json_schema_property(
                    elem.get('type'),
                    elem.get('minOccurs', '1'),
                    elem.get('maxOccurs', '1'),
                    elem.get('documentation') if include_docs else None,
                    include_enums,
                    None,
                    enum_values,
                    type_documentation=type_doc,
                    enum_ranges=enum_ranges
                )
                if prop_schema:
                    type_schema["properties"][elem['name']] = prop_schema
                    if elem.get('minOccurs', '1') == '1':
                        type_schema["required"].append(elem['name'])
            
            # Add properties from attributes
            for attr in type_info.get('attributes', []):
                min_occurs = '1' if attr.get('use') == 'required' else '0'
                attr_type = attr.get('type', '').replace('xs:', '')
                enum_values = None
                enum_ranges = None
                if include_enums and attr_type in self.types:
                    type_info_attr = self.types[attr_type]
                    enum_values = type_info_attr.get('enum_values')
                    enum_ranges = type_info_attr.get('enum_ranges')
                
                # Get type documentation for bitmask detection
                type_doc = None
                if attr_type in self.types:
                    type_doc = self.types[attr_type].get('documentation', '')
                
                prop_schema = self._create_json_schema_property(
                    attr.get('type'),
                    min_occurs,
                    '1',
                    attr.get('documentation') if include_docs else None,
                    include_enums,
                    attr.get('default'),
                    enum_values,
                    type_documentation=type_doc,
                    enum_ranges=enum_ranges
                )
                if prop_schema:
                    type_schema["properties"][attr['name']] = prop_schema
                    if min_occurs == '1':
                        type_schema["required"].append(attr['name'])
            
            schema["definitions"][type_name] = type_schema
        
        return schema
    
    def _create_json_schema_property(self, prop_type, min_occurs, max_occurs, 
                                     documentation=None, include_enums=True, 
                                     default_value=None, enum_values=None,
                                     type_documentation=None, enum_ranges=None):
        """Create a JSON Schema property definition."""
        if not prop_type:
            return None
        
        prop_type_clean = prop_type.replace('xs:', '')
        prop_schema = {}
        
        xsd_to_json_type = {
            'string': 'string',
            'int': 'integer',
            'long': 'integer',
            'boolean': 'boolean',
            'unsignedByte': 'integer',
            'unsignedShort': 'integer',
            'unsignedInt': 'integer',
            'unsignedLong': 'integer',
            'byte': 'integer',
            'short': 'integer',
            'anyURI': 'string',
            'hexBinary': 'string'
        }
        
        json_type = None
        if prop_type_clean in xsd_to_json_type:
            json_type = xsd_to_json_type[prop_type_clean]
        elif prop_type_clean in self.types:
            type_info = self.types[prop_type_clean]
            has_elements = bool(type_info.get('elements'))
            has_attributes = bool(type_info.get('attributes'))
            
            if has_elements or has_attributes:
                prop_schema["$ref"] = f"#/definitions/{prop_type_clean}"
                if documentation:
                    prop_schema["description"] = documentation
                if default_value:
                    prop_schema["default"] = default_value
                return prop_schema
            else:
                base_type = type_info.get('base') or type_info.get('restriction')
                if base_type:
                    base_clean = base_type.replace('xs:', '')
                    if base_clean in xsd_to_json_type:
                        json_type = xsd_to_json_type[base_clean]
                        # Check for hexBinary format
                        if base_clean == 'hexBinary' or 'HexBinary' in base_clean:
                            prop_schema["format"] = "hexBinary"
                    elif 'Int' in base_clean or 'UInt' in base_clean:
                        json_type = 'integer'
                        # Add format based on integer type
                        format_value = self._get_integer_format(base_clean)
                        if format_value:
                            prop_schema["format"] = format_value
                    elif 'String' in base_clean:
                        json_type = 'string'
                    elif 'HexBinary' in base_clean:
                        json_type = 'string'
                        prop_schema["format"] = "hexBinary"
        elif 'Int' in prop_type_clean or 'UInt' in prop_type_clean:
            json_type = 'integer'
            # Add format based on integer type
            format_value = self._get_integer_format(prop_type_clean)
            if format_value:
                prop_schema["format"] = format_value
        elif 'String' in prop_type_clean:
            json_type = 'string'
        elif 'HexBinary' in prop_type_clean:
            json_type = 'string'
            prop_schema["format"] = "hexBinary"
        
        if json_type:
            prop_schema["type"] = json_type
        
        # Check if this is a bitmask (hexBinary with bit positions)
        is_bitmask = False
        if prop_schema.get("format") == "hexBinary" and enum_values:
            # Check if documentation mentions "bit" or "bitmap"
            doc_lower = (documentation or "").lower()
            type_doc_lower = (type_documentation or "").lower()
            
            if "bit" in doc_lower or "bitmap" in doc_lower or "bit position" in type_doc_lower or "bitmap" in type_doc_lower:
                is_bitmask = True
        
        # Add enum values with descriptions
        if enum_values:
            if is_bitmask:
                # This is a bitmask - don't use enum constraint, document bit positions instead
                bit_positions = {}
                for key, desc in enum_values.items():
                    try:
                        bit_pos = int(key)
                        bit_positions[bit_pos] = desc
                    except:
                        bit_positions[key] = desc
                
                # Add bit position documentation
                bit_desc_text = "\n\nBit positions (multiple bits can be set, value is hex-encoded):\n"
                for bit_pos in sorted(bit_positions.keys(), key=lambda x: int(x) if isinstance(x, str) and x.isdigit() else 999):
                    bit_desc_text += f"  - Bit {bit_pos}: {bit_positions[bit_pos]}\n"
                bit_desc_text += "\nExample: To set bits 0 and 1, use hex value \"00000003\" (0x00000001 | 0x00000002)"
                
                if documentation:
                    prop_schema["description"] = documentation + bit_desc_text
                else:
                    prop_schema["description"] = bit_desc_text.strip()
                
                # Add bit positions as x-bit-positions extension for programmatic use
                prop_schema["x-bit-positions"] = bit_positions
                
                # Add pattern for hexBinary validation based on base type
                hex_binary_size = None
                if prop_type_clean in self.types:
                    type_info = self.types[prop_type_clean]
                    base_type = type_info.get('base') or type_info.get('restriction')
                    if base_type:
                        base_clean = base_type.replace('xs:', '')
                        if 'HexBinary32' in base_clean:
                            hex_binary_size = 32
                        elif 'HexBinary16' in base_clean:
                            hex_binary_size = 16
                        elif 'HexBinary8' in base_clean:
                            hex_binary_size = 8
                        elif 'HexBinary64' in base_clean:
                            hex_binary_size = 64
                        elif 'HexBinary160' in base_clean:
                            hex_binary_size = 160
                        elif 'HexBinary48' in base_clean:
                            hex_binary_size = 48
                
                if hex_binary_size:
                    # Pattern: 1 to N/4 hex characters (since each hex char is 4 bits)
                    max_chars = hex_binary_size // 4
                    prop_schema["pattern"] = f"^[0-9A-Fa-f]{{1,{max_chars}}}$"
                    prop_schema["x-examples"] = [
                        "00000001",  # Only bit 0 set (for 32-bit)
                        "00000003",  # Bits 0 and 1 set
                        "FFFFFFFF" if hex_binary_size >= 32 else "FF"  # All bits set
                    ]
            else:
                # Regular enum (not a bitmask)
                enum_list = []
                enum_descriptions = {}  # Store descriptions for each enum value
                is_numeric = json_type == 'integer' if json_type else False
                if not is_numeric and prop_type_clean in self.types:
                    type_info = self.types[prop_type_clean]
                    base_type = type_info.get('base') or type_info.get('restriction')
                    if base_type:
                        base_clean = base_type.replace('xs:', '')
                        if base_clean in ['unsignedByte', 'unsignedShort', 'unsignedInt', 'unsignedLong',
                                         'byte', 'short', 'int', 'long'] or 'Int' in base_clean or 'UInt' in base_clean:
                            is_numeric = True
                    elif 'Int' in prop_type_clean or 'UInt' in prop_type_clean:
                        is_numeric = True
                
                for key, desc in enum_values.items():
                    enum_value = key
                    if is_numeric:
                        try:
                            enum_value = int(key)
                        except:
                            enum_value = key
                    enum_list.append(enum_value)
                    # Store description for this enum value
                    if desc:
                        enum_descriptions[str(enum_value)] = desc
                
                # Only add enum constraint if there are NO ranges
                # If there are ranges, the type allows any value in the range, so we shouldn't restrict with enum
                if enum_list and not enum_ranges:
                    prop_schema["enum"] = enum_list
                
                # Always add enum descriptions and ranges to x-enum-descriptions for documentation
                if enum_descriptions or enum_ranges:
                    if "x-enum-descriptions" not in prop_schema:
                        prop_schema["x-enum-descriptions"] = {}
                    
                    # Add specific enum value descriptions
                    if enum_descriptions:
                        prop_schema["x-enum-descriptions"].update(enum_descriptions)
                    
                    # Add range descriptions
                    if enum_ranges:
                        for range_info in enum_ranges:
                            range_key = f"{range_info['start']} - {range_info['end']}"
                            prop_schema["x-enum-descriptions"][range_key] = range_info['description']
                    
                    # Also add to description for better visibility
                    if enum_descriptions or enum_ranges:
                        enum_desc_lines = []
                        # Only show specific enum values (not ranges) in Enum values section
                        if enum_descriptions:
                            # Filter out range keys (those containing " - ")
                            specific_values = {k: v for k, v in enum_descriptions.items() if " - " not in k}
                            if specific_values:
                                enum_desc_lines.append("Enum values:")
                                for k, v in specific_values.items():
                                    enum_desc_lines.append(f"  - {k}: {v}")
                        if enum_ranges:
                            if enum_descriptions:
                                enum_desc_lines.append("")  # Add blank line between specific values and ranges
                            enum_desc_lines.append("Value ranges:")
                            for range_info in enum_ranges:
                                enum_desc_lines.append(f"  - {range_info['start']} - {range_info['end']}: {range_info['description']}")
                        
                        enum_desc_text = "\n" + "\n".join(enum_desc_lines) if enum_desc_lines else ""
                        if documentation:
                            prop_schema["description"] = documentation + enum_desc_text
                        else:
                            prop_schema["description"] = enum_desc_text.strip()
        
        # Add constraints
        if json_type == 'integer':
            # Check base type if prop_type_clean is a complex type
            base_type_for_constraints = prop_type_clean
            if prop_type_clean in self.types:
                type_info = self.types[prop_type_clean]
                base_type = type_info.get('base') or type_info.get('restriction')
                if base_type:
                    base_type_for_constraints = base_type.replace('xs:', '')
            
            if 'UInt8' in base_type_for_constraints or base_type_for_constraints == 'unsignedByte':
                prop_schema["minimum"] = 0
                prop_schema["maximum"] = 255
            elif 'UInt16' in base_type_for_constraints or base_type_for_constraints == 'unsignedShort':
                prop_schema["minimum"] = 0
                prop_schema["maximum"] = 65535
            elif 'UInt32' in base_type_for_constraints or base_type_for_constraints == 'unsignedInt':
                prop_schema["minimum"] = 0
                prop_schema["maximum"] = 4294967295
        
        # Handle arrays
        if max_occurs == 'unbounded' or (max_occurs.isdigit() and int(max_occurs) > 1):
            array_schema = {
                "type": "array",
                "items": prop_schema
            }
            min_items = int(min_occurs) if min_occurs.isdigit() else 0
            if min_items > 0:
                array_schema["minItems"] = min_items
            if max_occurs.isdigit():
                array_schema["maxItems"] = int(max_occurs)
            prop_schema = array_schema
        
        # Only set description if it hasn't been set already (e.g., by bitmask or enum handling)
        if documentation and "description" not in prop_schema:
            prop_schema["description"] = documentation
        
        if default_value:
            prop_schema["default"] = default_value
        
        return prop_schema if prop_schema else None
    
    def _get_integer_format(self, type_name):
        """Get OpenAPI format string for integer types.
        
        Returns format string (e.g., 'uint8', 'int16') based on XSD type name.
        Returns None for non-standard types (e.g., UInt40, UInt48, Int48).
        """
        type_lower = type_name.lower()
        
        # Standard OpenAPI integer formats (from OpenAPI Format Registry)
        if type_lower == 'uint8' or type_name == 'unsignedByte':
            return 'uint8'
        elif type_lower == 'uint16' or type_name == 'unsignedShort':
            return 'uint16'
        elif type_lower == 'uint32' or type_name == 'unsignedInt':
            return 'uint32'
        elif type_lower == 'uint64' or type_name == 'unsignedLong':
            return 'uint64'
        elif type_lower == 'int8' or type_name == 'byte':
            return 'int8'
        elif type_lower == 'int16' or type_name == 'short':
            return 'int16'
        elif type_lower == 'int32' or type_name == 'int':
            return 'int32'
        elif type_lower == 'int64' or type_name == 'long':
            return 'int64'
        
        # Non-standard types (UInt40, UInt48, Int48) don't have standard OpenAPI formats
        # They will use type: integer with min/max constraints instead
        return None

