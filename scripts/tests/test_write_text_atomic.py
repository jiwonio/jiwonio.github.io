import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from post_schema import write_bytes_atomic, write_text_atomic


class WriteTextAtomicTests(unittest.TestCase):
    def test_write_text_atomic_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "post.md"
            write_text_atomic(target, "hello world")
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_text(encoding="utf-8"), "hello world")
            self.assertFalse(target.with_suffix(target.suffix + ".tmp").exists())

    def test_write_bytes_atomic_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "image.webp"
            write_bytes_atomic(target, b"\x00\x01\x02")
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), b"\x00\x01\x02")


if __name__ == "__main__":
    unittest.main()