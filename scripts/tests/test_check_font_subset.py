"""Tests for scripts/check_font_subset.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from check_font_subset import FINGERPRINT_NAME, fingerprint, is_stale, vendor_dir
from download_noto_font import FAMILIES


class CheckFontSubsetTests(unittest.TestCase):
    def test_fingerprint_is_stable(self) -> None:
        self.assertEqual(fingerprint("abc"), fingerprint("abc"))
        self.assertNotEqual(fingerprint("abc"), fingerprint("abcd"))

    def test_is_stale_when_font_missing(self) -> None:
        with mock.patch("check_font_subset.vendor_dir") as vendor_mock:
            out_dir = Path("/tmp/missing-font")
            vendor_mock.return_value = out_dir
            self.assertTrue(is_stale("Noto+Sans+KR", "가"))

    def test_is_stale_when_fingerprint_differs(self) -> None:
        family = "Noto+Sans+KR"
        fake_dir = Path("/tmp/fake-noto-kr")
        woff2_name = FAMILIES[family]["woff2_name"]
        fake_dir.mkdir(parents=True, exist_ok=True)
        (fake_dir / woff2_name).write_bytes(b"font")
        (fake_dir / FINGERPRINT_NAME).write_text("old\n", encoding="utf-8")
        with mock.patch("check_font_subset.vendor_dir", return_value=fake_dir):
            self.assertTrue(is_stale(family, "새글자"))
        (fake_dir / woff2_name).unlink(missing_ok=True)
        (fake_dir / FINGERPRINT_NAME).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()