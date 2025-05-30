#!/usr/bin/env python3

import unittest

class SimpleTest(unittest.TestCase):
    """A simple test case that doesn't rely on importing project code"""

    def test_addition(self):
        """Test that addition works correctly"""
        self.assertEqual(1 + 1, 2)
        self.assertEqual(2 + 2, 4)
        self.assertEqual(-1 + 1, 0)

    def test_string_methods(self):
        """Test that string methods work correctly"""
        self.assertEqual("hello".upper(), "HELLO")
        self.assertEqual("WORLD".lower(), "world")
        self.assertEqual("katoolin".replace("o", "a"), "kataalin")

if __name__ == '__main__':
    unittest.main()
