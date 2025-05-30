#!/usr/bin/env python3

import sys
import os
import unittest

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.categories import categories

class TestCategories(unittest.TestCase):
    """Test cases for the categories dictionary in core/categories.py"""

    def test_categories_structure(self):
        """Test that the categories dictionary has the correct structure"""
        # Check that categories is a dictionary
        self.assertIsInstance(categories, dict)
        
        # Check that each key is an integer
        for key in categories.keys():
            self.assertIsInstance(key, int)
        
        # Check that each value is a list with two elements
        for value in categories.values():
            self.assertIsInstance(value, list)
            self.assertEqual(len(value), 2)
            
            # Check that the first element is a string (category name)
            self.assertIsInstance(value[0], str)
            
            # Check that the second element is a list (tools)
            self.assertIsInstance(value[1], list)
            
            # Check that each tool is a string
            for tool in value[1]:
                self.assertIsInstance(tool, str)
    
    def test_categories_content(self):
        """Test that the categories dictionary has the expected content"""
        # Check that there are 14 categories
        self.assertEqual(len(categories), 14)
        
        # Check that the category names are as expected
        expected_categories = [
            'information_gathering',
            'vulnerability_analysis',
            'wireless_attacks',
            'web_applications',
            'sniffing_spoofing',
            'maintaining_access',
            'reporting_tools',
            'exploitation_tools',
            'forensics_tools',
            'stress_testing',
            'password_attacks',
            'reverse_engineering',
            'hardware_hacking',
            'extra'
        ]
        
        for i, category in enumerate(expected_categories, 1):
            self.assertEqual(categories[i][0], category)

if __name__ == '__main__':
    unittest.main()