import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from channels.cli import get_client_key


class TestGetClientKey(unittest.TestCase):

    def test_generates_and_persists_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".tabris_client_id")
            key = get_client_key(path)
            self.assertTrue(key)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                self.assertEqual(f.read().strip(), key)

    def test_returns_same_key_on_second_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".tabris_client_id")
            first = get_client_key(path)
            second = get_client_key(path)
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
