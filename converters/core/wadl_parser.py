"""
WADL parser - extracts API resource and method definitions.
"""

import xml.etree.ElementTree as ET

ns_wadl = 'http://wadl.dev.java.net/2009/02'
ns_wx = 'http://zigbee.org/wadlExt'
ns_sep = 'http://ieee.org/2030.5'
ns_xsd = 'http://www.w3.org/2001/XMLSchema'

namespaces = {
    'wadl': ns_wadl,
    'wx': ns_wx,
    'sep': ns_sep,
    'xsd': ns_xsd
}


class WADLParser:
    """Parse WADL files and extract API resource definitions."""
    
    def __init__(self):
        self.resources = []
        self.base_url = None
        
    def parse(self, wadl_file):
        """Parse the WADL file and extract resource information.
        
        Args:
            wadl_file: Path to WADL file
            
        Returns:
            self (for method chaining)
        """
        tree = ET.parse(wadl_file)
        root = tree.getroot()
        
        # Extract base URL from resources element
        resources_elem = root.find('.//{%s}resources' % ns_wadl, namespaces)
        if resources_elem is not None:
            self.base_url = resources_elem.get('{%s}sampleBase' % ns_wx) or 'http://localhost/sep/'
        
        # Extract all resources
        for resource in root.findall('.//{%s}resource' % ns_wadl, namespaces):
            resource_info = self._extract_resource_info(resource)
            if resource_info:
                self.resources.append(resource_info)
        
        return self
    
    def _extract_resource_info(self, resource_elem):
        """Extract information from a resource element.
        
        Returns:
            dict: Resource information with path, methods, etc.
        """
        resource_id = resource_elem.get('id')
        sample_path = resource_elem.get('{%s}samplePath' % ns_wx, '')
        
        # Extract documentation
        doc_elem = resource_elem.find('.//{%s}doc' % ns_wadl, namespaces)
        doc_title = doc_elem.get('title') if doc_elem is not None else None
        doc_text = doc_elem.text if doc_elem is not None else None
        
        # Extract methods
        methods = []
        for method in resource_elem.findall('.//{%s}method' % ns_wadl, namespaces):
            method_info = self._extract_method_info(method)
            if method_info:
                methods.append(method_info)
        
        # Extract template parameters
        params = []
        for param in resource_elem.findall('.//{%s}sampleParam' % ns_wx, namespaces):
            param_info = {
                'name': param.get('name'),
                'style': param.get('style'),
                'type': param.get('type')
            }
            params.append(param_info)
        
        return {
            'id': resource_id,
            'path': sample_path,
            'title': doc_title,
            'description': doc_text,
            'methods': methods,
            'parameters': params
        }
    
    def _extract_method_info(self, method_elem):
        """Extract information from a method element.
        
        Returns:
            dict: Method information with HTTP method, request/response, etc.
        """
        method_name = method_elem.get('name')
        method_id = method_elem.get('id')
        mode = method_elem.get('{%s}mode' % ns_wx)
        
        # Extract request
        request_elem = method_elem.find('.//{%s}request' % ns_wadl, namespaces)
        request = None
        if request_elem is not None:
            request = self._extract_request_response(request_elem, is_request=True)
        
        # Extract responses
        responses = []
        for response_elem in method_elem.findall('.//{%s}response' % ns_wadl, namespaces):
            response = self._extract_request_response(response_elem, is_request=False)
            response['status'] = response_elem.get('status', '200')
            responses.append(response)
        
        return {
            'id': method_id,
            'name': method_name,
            'mode': mode,
            'request': request,
            'responses': responses
        }
    
    def _extract_request_response(self, elem, is_request=False):
        """Extract request or response information.
        
        Returns:
            dict: Request/response information with representations, parameters, etc.
        """
        result = {
            'representations': [],
            'parameters': []
        }
        
        # Extract representations
        for repr_elem in elem.findall('.//{%s}representation' % ns_wadl, namespaces):
            repr_info = {
                'mediaType': repr_elem.get('mediaType'),
                'element': repr_elem.get('element')
            }
            result['representations'].append(repr_info)
        
        # Extract parameters (for requests)
        if is_request:
            for param_elem in elem.findall('.//{%s}param' % ns_wadl, namespaces):
                param_info = {
                    'name': param_elem.get('name'),
                    'style': param_elem.get('style'),
                    'type': param_elem.get('type'),
                    'required': param_elem.get('required', 'false') == 'true'
                }
                # Extract parameter documentation
                doc_elem = param_elem.find('.//{%s}doc' % ns_wadl, namespaces)
                if doc_elem is not None:
                    param_info['description'] = doc_elem.text
                result['parameters'].append(param_info)
        
        return result

