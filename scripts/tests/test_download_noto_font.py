"""Tests for scripts/download_noto_font.py helpers."""

from __future__ import annotations

import unittest

from download_noto_font import (
    build_single_file_css,
    chunk_text_for_font_api,
    collect_site_characters,
    preload_faces,
)


class DownloadNotoFontTests(unittest.TestCase):
    def test_chunk_text_splits_long_input(self) -> None:
        text = "a" * 1000
        chunks = chunk_text_for_font_api(text, max_chars=400)
        self.assertEqual(len(chunks), 3)
        self.assertEqual("".join(chunks), text)

    def test_chunk_text_keeps_short_input(self) -> None:
        text = "abc"
        self.assertEqual(chunk_text_for_font_api(text), [text])

    def test_build_single_file_css_references_one_woff2(self) -> None:
        css = build_single_file_css("Noto Sans KR", "noto-sans-kr.woff2")
        self.assertIn("font-family: 'Noto Sans KR'", css)
        self.assertIn("font-weight: 400;", css)
        self.assertIn("font-display: optional", css)
        self.assertIn("url(noto-sans-kr.woff2)", css)
        self.assertEqual(css.count("@font-face"), 1)

    def test_preload_faces_prefers_weight_400(self) -> None:
        css = (
            "@font-face { font-weight: 700; src: url(bold.woff2); }\n"
            "@font-face { font-weight: 400; src: url(regular.woff2); }\n"
        )
        self.assertEqual(preload_faces(css), ["regular.woff2"])

    def test_collect_site_characters_includes_hangul(self) -> None:
        chars = collect_site_characters()
        self.assertIn("가", chars)


if __name__ == "__main__":
    unittest.main()