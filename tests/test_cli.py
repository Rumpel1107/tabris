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

    def test_creates_the_identity_file_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".tabris_client_id")
            get_client_key(path)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
