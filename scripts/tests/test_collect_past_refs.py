import unittest
from pathlib import Path
from unittest import mock

import post_common as pc


class CollectPastReferenceUrlsTests(unittest.TestCase):
    def test_before_date_excludes_later_editions(self):
        fake = {
            "_posts/ko/2026/2026-06-25-ai-news-2026-06-25.md": (
                '### 참고문헌\n- [a](https://example.com/old){:target="_blank"}\n'
            ),
            "_posts/ko/2026/2026-07-10-ai-news-2026-07-10.md": (
                '### 참고문헌\n- [b](https://example.com/new){:target="_blank"}\n'
            ),
        }

        def fake_read(self, encoding="utf-8"):
            key = str(self).replace("\\", "/")
            return fake[key]

        with mock.patch.object(pc, "list_post_files", return_value=list(fake)):
            with mock.patch.object(pc, "detect_lang_from_path", return_value="ko"):
                with mock.patch.object(Path, "read_text", fake_read):
                    all_urls = pc.collect_past_reference_urls()
                    before = pc.collect_past_reference_urls(before_date="2026-07-03")

        self.assertIn("https://example.com/old", all_urls)
        self.assertIn("https://example.com/new", all_urls)
        self.assertIn("https://example.com/old", before)
        self.assertNotIn("https://example.com/new", before)


if __name__ == "__main__":
    unittest.main()
