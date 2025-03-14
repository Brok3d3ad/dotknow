#!/usr/bin/env python3
"""
Test runner for SVG Processor unit tests.
This script runs all tests in the tests directory.
"""

import unittest
import sys
import os

# Add parent directory to path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Discover and run all tests in the tests directory."""
    # Start at the directory containing this file
    start_dir = os.path.dirname(os.path.abspath(__file__))
    test_suite = unittest.defaultTestLoader.discover(start_dir, pattern="test_*.py")
    
    # Create test runner
    test_runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = test_runner.run(test_suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests()) 