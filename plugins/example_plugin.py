#!/usr/bin/env python3

"""
Example plugin for Katoolin.
This plugin demonstrates how to add custom tool categories and repositories.
"""

from core.plugins import PluginInterface
from typing import Dict, List, Any

class ExamplePlugin(PluginInterface):
    """
    Example plugin that adds a custom tool category and repository.
    """
    
    def get_name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: Name of the plugin
        """
        return "Example Plugin"
    
    def get_categories(self) -> Dict[int, List[Any]]:
        """
        Get the categories provided by this plugin.
        
        Returns:
            Dict[int, List[Any]]: Dictionary of category IDs and their data
        """
        # Use a high category ID to avoid conflicts with built-in categories
        # The format is the same as in core/categories.py:
        # {category_id: [category_name, [tool1, tool2, ...]]}
        return {
            100: ['custom_tools', 
                 ['nmap', 'wireshark', 'metasploit-framework', 'burpsuite', 'sqlmap',
                  'custom-tool-1', 'custom-tool-2', 'custom-tool-3']
                 ]
        }
    
    def get_repositories(self) -> List[Dict[str, str]]:
        """
        Get the repositories provided by this plugin.
        
        Returns:
            List[Dict[str, str]]: List of repository information dictionaries
        """
        return [
            {
                'name': 'Example Repository',
                'url': 'http://example.com/repo',
                'components': 'main',
                'key_url': 'http://example.com/repo/key.asc'
            },
            {
                'name': 'Another Example Repository',
                'url': 'http://another-example.com/repo',
                'components': 'main contrib',
                'key_id': '1234ABCD',
                'keyserver': 'keyserver.ubuntu.com'
            }
        ]