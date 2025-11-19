"""
Core XSD parser - extracts schema information without generating output.
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict

ns_xs = 'http://www.w3.org/2001/XMLSchema'
ns = {'xs': ns_xs}


class XSDParser:
    """Parse XSD schema files and extract structured information."""
    
    def __init__(self, base_uri=None):
        self.base_uri = base_uri or "https://schemas.ieee.org/2030.5/"
        self.types = {}
        self.elements = {}
        self.attributes = defaultdict(list)
        self.namespace = None
        self.target_namespace = None
        
    def parse(self, xsd_file):
        """Parse the XSD file and extract schema information.
        
        Args:
            xsd_file: Path to XSD file
            
        Returns:
            self (for method chaining)
        """
        tree = ET.parse(xsd_file)
        root = tree.getroot()
        
        # Extract namespace information
        self.namespace = root.get('targetNamespace')
        if self.namespace:
            self.target_namespace = self.namespace
            # Use namespace as base URI if not provided
            if not self.base_uri.startswith('http'):
                self.base_uri = self.namespace.replace('urn:', 'https://').replace(':', '/')
        
        # Extract all complex types
        for complex_type in root.findall('.//{%s}complexType' % ns_xs, ns):
            name = complex_type.get('name')
            if name:
                self.types[name] = self._extract_type_info(complex_type)
        
        # Extract all simple types
        for simple_type in root.findall('.//{%s}simpleType' % ns_xs, ns):
            name = simple_type.get('name')
            if name:
                self.types[name] = self._extract_type_info(simple_type)
        
        # Extract root elements
        for element in root.findall('.//{%s}element' % ns_xs, ns):
            name = element.get('name')
            etype = element.get('type')
            if name:
                self.elements[name] = {
                    'type': etype,
                    'minOccurs': element.get('minOccurs', '1'),
                    'maxOccurs': element.get('maxOccurs', '1')
                }
        
        return self
    
    def _parse_enum_values(self, doc_text):
        """Parse enum values from documentation text.
        
        Looks for patterns like:
        - "0 = Value" or "0 - Value" or "0: Value"
        - "1 = Value" or "1 - Value" or "1: Value"
        etc.
        
        Also extracts ranges like "3 - 64: Reserved" or "65 - 191: User-defined"
        Returns tuple: (enum_values_dict, range_info_list)
        """
        if not doc_text:
            return None, None
        
        enum_values = {}
        range_info = []
        
        # Pattern to match: number = value, number - value, or number: value
        pattern = r'^(\d+)\s*([=\-:])\s*(.+?)(?:\n|$)'
        
        # Pattern to match ranges: number - number: description
        range_pattern = r'^(\d+)\s*-\s*(\d+)\s*:\s*(.+?)(?:\n|$)'
        
        for line in doc_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # First check if it's a range
            range_match = re.match(range_pattern, line)
            if range_match:
                start = range_match.group(1)
                end = range_match.group(2)
                desc = range_match.group(3).strip()
                # Clean up description
                desc = desc.rstrip('.,;')
                desc = re.sub(r'\s*\([^)]*default[^)]*\)', '', desc, flags=re.IGNORECASE)
                desc = desc.strip()
                range_info.append({
                    'start': int(start),
                    'end': int(end),
                    'description': desc
                })
                continue
            
            # Skip lines that just say "reserved" without a number
            if 'reserved' in line.lower() and not re.search(r'\d', line):
                continue
            
            # Check for single enum values
            match = re.match(pattern, line)
            if match:
                enum_key = match.group(1)
                separator = match.group(2)
                enum_value = match.group(3).strip()
                
                # Clean up enum value (remove trailing periods, etc.)
                enum_value = enum_value.rstrip('.,;')
                # Remove "(default, if not specified)" or similar from value
                enum_value = re.sub(r'\s*\([^)]*default[^)]*\)', '', enum_value, flags=re.IGNORECASE)
                enum_value = enum_value.strip()
                enum_values[enum_key] = enum_value
        
        return (enum_values if enum_values else None, 
                range_info if range_info else None)
    
    def _extract_documentation(self, elem):
        """Extract documentation from an element.
        
        Returns:
            tuple: (documentation_text, (enum_values_dict, range_info_list))
        """
        annotation = elem.find('.//{%s}annotation' % ns_xs, ns)
        if annotation is None:
            return None, None
        
        doc_elem = annotation.find('.//{%s}documentation' % ns_xs, ns)
        if doc_elem is None:
            return None, None
        
        doc_text = doc_elem.text if doc_elem.text else ''
        # Also get tail text if any
        if doc_elem.tail:
            doc_text += doc_elem.tail
        
        # Try to parse enum values and ranges from documentation
        enum_values, range_info = self._parse_enum_values(doc_text)
        
        # Return tuple if we have either enum_values or range_info
        if enum_values or range_info:
            return doc_text.strip() if doc_text.strip() else None, (enum_values, range_info)
        else:
            return doc_text.strip() if doc_text.strip() else None, None
    
    def _extract_type_info(self, type_elem):
        """Extract information from a type element.
        
        Returns:
            dict: Type information with elements, attributes, base, documentation, etc.
        """
        info = {
            'elements': [],
            'attributes': [],
            'base': None,
            'restriction': None,
            'documentation': None,
            'enum_values': None,
            'enum_ranges': None
        }
        
        # Extract documentation and enum values
        doc_text, enum_data = self._extract_documentation(type_elem)
        info['documentation'] = doc_text
        if isinstance(enum_data, tuple):
            # New format: (enum_values, range_info)
            info['enum_values'] = enum_data[0]
            info['enum_ranges'] = enum_data[1]
        else:
            # Old format: just enum_values (for backward compatibility)
            info['enum_values'] = enum_data
        
        # Check for extension or restriction
        extension = type_elem.find('.//{%s}extension' % ns_xs, ns)
        if extension is not None:
            info['base'] = extension.get('base')
            # Extract elements from extension
            for elem in extension.findall('.//{%s}element' % ns_xs, ns):
                elem_info = {
                    'name': elem.get('name'),
                    'type': elem.get('type'),
                    'minOccurs': elem.get('minOccurs', '1'),
                    'maxOccurs': elem.get('maxOccurs', '1')
                }
                # Extract element documentation and enum values
                elem_doc, elem_enum_data = self._extract_documentation(elem)
                if elem_doc:
                    elem_info['documentation'] = elem_doc
                if elem_enum_data:
                    if isinstance(elem_enum_data, tuple):
                        elem_info['enum_values'] = elem_enum_data[0]
                        elem_info['enum_ranges'] = elem_enum_data[1]
                    else:
                        elem_info['enum_values'] = elem_enum_data
                info['elements'].append(elem_info)
        
        restriction = type_elem.find('.//{%s}restriction' % ns_xs, ns)
        if restriction is not None:
            info['restriction'] = restriction.get('base')
            # Check for enumeration in restriction
            for enum in restriction.findall('.//{%s}enumeration' % ns_xs, ns):
                if info['enum_values'] is None:
                    info['enum_values'] = {}
                value = enum.get('value')
                if value:
                    # Try to get enum documentation
                    enum_doc, _ = self._extract_documentation(enum)
                    info['enum_values'][value] = enum_doc if enum_doc else value
        
        # Extract attributes
        for attr in type_elem.findall('.//{%s}attribute' % ns_xs, ns):
            attr_info = {
                'name': attr.get('name'),
                'type': attr.get('type'),
                'use': attr.get('use', 'optional'),
                'default': attr.get('default')
            }
            # Extract attribute documentation
            attr_doc, _ = self._extract_documentation(attr)
            if attr_doc:
                attr_info['documentation'] = attr_doc
            info['attributes'].append(attr_info)
        
        # Extract elements (if not in extension)
        if extension is None:
            for elem in type_elem.findall('.//{%s}element' % ns_xs, ns):
                elem_info = {
                    'name': elem.get('name'),
                    'type': elem.get('type'),
                    'minOccurs': elem.get('minOccurs', '1'),
                    'maxOccurs': elem.get('maxOccurs', '1')
                }
                # Extract element documentation and enum values
                elem_doc, elem_enum_data = self._extract_documentation(elem)
                if elem_doc:
                    elem_info['documentation'] = elem_doc
                if elem_enum_data:
                    if isinstance(elem_enum_data, tuple):
                        elem_info['enum_values'] = elem_enum_data[0]
                        elem_info['enum_ranges'] = elem_enum_data[1]
                    else:
                        elem_info['enum_values'] = elem_enum_data
                info['elements'].append(elem_info)
        
        return info

