#!/usr/bin/env python3
"""
Test runner for Luna Voice Assistant.
"""
import unittest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

if __name__ == '__main__':
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(not result.wasSuccessful())