#!/usr/bin/env python

import unittest
import sys
import os

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.gear import format

class TestGear(unittest.TestCase):
    """Test cases for functions in core/gear.py"""

    def test_format(self):
        """Test that the format function correctly formats category names"""
        # Test basic formatting
        self.assertEqual(format("test_string"), "Test String")
        self.assertEqual(format("another_test"), "Another Test")

        # Test with actual category names from the project
        self.assertEqual(format("information_gathering"), "Information Gathering")
        self.assertEqual(format("vulnerability_analysis"), "Vulnerability Analysis")
        self.assertEqual(format("wireless_attacks"), "Wireless Attacks")
        self.assertEqual(format("web_applications"), "Web Applications")

if __name__ == '__main__':
    unittest.main()
