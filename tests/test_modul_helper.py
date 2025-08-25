"""
Unit tests for the modul_helper module.
"""
import unittest
import sys
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

# Add src to path so we can import modul_helper
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import the functions directly to avoid relative import issues
import modul_helper

class TestModulHelper(unittest.TestCase):
    """Test cases for the modul_helper module."""

    def test_is_command_safe_with_safe_commands(self):
        """Test that safe commands are correctly identified."""
        safe_commands: List[List[str]] = [
            ['xdg-open', 'https://example.com'],
            ['firefox', 'https://example.com'],
            ['code', '/path/to/file'],
            ['gedit', 'file.txt']
        ]
        
        for cmd in safe_commands:
            with self.subTest(cmd=cmd):
                self.assertTrue(modul_helper._is_command_safe(cmd))

    def test_is_command_safe_with_dangerous_commands(self):
        """Test that dangerous commands are correctly identified."""
        dangerous_commands: List[List[str]] = [
            ['rm', '-rf', '/'],
            ['sudo', 'rm', '-rf', '/'],
            ['shutdown', 'now'],
            ['chmod', '777', '/etc/passwd']
        ]
        
        for cmd in dangerous_commands:
            with self.subTest(cmd=cmd):
                self.assertFalse(modul_helper._is_command_safe(cmd))

    def test_is_command_safe_with_empty_command(self):
        """Test that empty commands are correctly identified as unsafe."""
        self.assertFalse(modul_helper._is_command_safe([]))
        # Test with None by casting to avoid type checker issues
        from typing import cast
        # We're testing the runtime behavior, but we need to satisfy the type checker
        # In practice, we'd never pass None, but the function should handle it gracefully
        self.assertFalse(modul_helper._is_command_safe(cast(List[str], None)))

    @patch('modul_helper.PERSONAL_SHORTCUTS', {
        'test: safe': 'firefox https://example.com',
        'test: param': 'firefox https://example.com/search?q={query}'
    })
    @patch('modul_helper.subprocess.Popen')
    def test_run_shortcut_with_safe_command(self, mock_popen):
        """Test that safe shortcuts can be executed."""
        mock_popen.return_value = MagicMock()
        
        result = modul_helper.run_shortcut('test: safe')
        self.assertEqual(result, 'firefox https://example.com')
        mock_popen.assert_called_once()

    @patch('modul_helper.PERSONAL_SHORTCUTS', {
        'test: dangerous': 'rm -rf /'
    })
    def test_run_shortcut_with_dangerous_command(self):
        """Test that dangerous shortcuts raise Exception with PermissionError as cause."""
        with self.assertRaises(Exception) as context:
            modul_helper.run_shortcut('test: dangerous')
        self.assertIn("not allowed for security reasons", str(context.exception))

    @patch('modul_helper.PERSONAL_SHORTCUTS', {
        'test: param': 'firefox https://example.com/search?q={query}'
    })
    @patch('modul_helper.subprocess.Popen')
    def test_run_shortcut_with_parameters(self, mock_popen):
        """Test that shortcuts with parameters work correctly."""
        mock_popen.return_value = MagicMock()
        
        result = modul_helper.run_shortcut('test: param', query='python')
        self.assertEqual(result, 'firefox https://example.com/search?q=python')
        mock_popen.assert_called_once()

    def test_run_shortcut_with_nonexistent_key(self):
        """Test that non-existent shortcuts raise ValueError."""
        with self.assertRaises(ValueError):
            modul_helper.run_shortcut('nonexistent: key')

if __name__ == '__main__':
    unittest.main()