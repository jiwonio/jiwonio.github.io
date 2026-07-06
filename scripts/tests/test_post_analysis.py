import tempfile
import unittest
from pathlib import Path
from unittest import mock

from post_analysis import (
    count_markdown_h2,
    extract_reference_entries,
    extract_reference_urls,
    find_informal_ko_lines,
    rebuild_references_section,
    title_similarity,
    tokenize,
)


class PostAnalysisTests(unittest.TestCase):
    def test_count_markdown_h2_ignores_code_blocks(self):
        content = """---
title: t
---
Intro

<!--more-->

## Section A

```md
## not counted
```

## Section B
"""
        self.assertEqual(count_markdown_h2(content), 2)

    def test_extract_reference_urls_supports_english_heading(self):
        content = """---
title: t
---
Body

## References
- [Example](https://example.com/docs)
- https://example.com/plain
"""
        self.assertEqual(
            extract_reference_urls(content),
            ["https://example.com/docs", "https://example.com/plain"],
        )

    def test_extract_reference_urls_strips_markdown_title_attribute(self):
        content = """---
title: t
---
Body

## References
- [Ollama Official Website](https://ollama.com "Ollama"){:target="_blank"}
- [GitHub](https://github.com/ollama/ollama-python "ollama-python on GitHub")
"""
        self.assertEqual(
            extract_reference_urls(content),
            [
                "https://ollama.com",
                "https://github.com/ollama/ollama-python",
            ],
        )

    def test_title_similarity_detects_overlap(self):
        score = title_similarity(
            "Cursor IDE real world review",
            "Real world Cursor IDE adaptation",
        )
        self.assertGreaterEqual(score, 0.4)

    def test_tokenize_removes_stop_words(self):
        tokens = tokenize("Building production guide with docker")
        self.assertNotIn("with", tokens)
        self.assertIn("docker", tokens)

    def test_extract_reference_entries_preserves_titles(self):
        content = """---
title: t
---
### 참고문헌
- [GitHub Blog](https://github.blog/post){:target="_blank"}
"""
        self.assertEqual(
            extract_reference_entries(content),
            [("GitHub Blog", "https://github.blog/post")],
        )

    def test_extract_reference_urls_supports_spaced_and_asterisk_bullets(self):
        content = """---
title: t
---
## 参考资料

-   [Daybreak](https://openai.com/index/daybreak-securing-the-world)
*   [CCCL](https://developer.nvidia.com/blog/cccl-runtime/)
"""
        self.assertEqual(
            extract_reference_urls(content),
            [
                "https://openai.com/index/daybreak-securing-the-world",
                "https://developer.nvidia.com/blog/cccl-runtime/",
            ],
        )

    def test_rebuild_references_section_uses_source_urls_for_ja(self):
        source = """---
title: t
---
### 참고문헌
- [원문](https://example.com/source){:target="_blank"}
"""
        translated = """---
title: t
---
### 参考文献
- [誤ったURL](https://example.com/wrong){:target="_blank"}
"""
        rebuilt = rebuild_references_section(translated, source, "ja")
        self.assertIn("https://example.com/source", rebuilt)
        self.assertNotIn("https://example.com/wrong", rebuilt)

    def test_find_informal_ko_lines(self):
        content = """---
title: t
---
정상적인 문장입니다.

<!--more-->

이건 해요. 그리고 또 하나예요.
"""
        hits = find_informal_ko_lines(content)
        self.assertTrue(any("해요" in line for line in hits))

    def test_get_changed_post_paths_uses_git(self):
        from post_analysis import get_changed_post_paths

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            posts = root / "_posts" / "ko" / "2026"
            posts.mkdir(parents=True)
            changed = posts / "2026-06-01-demo.md"
            changed.write_text("---\nlayout: post\n---\n", encoding="utf-8")

            with mock.patch("post_analysis.subprocess.run") as run_mock:
                run_mock.return_value = mock.Mock(
                    returncode=0,
                    stdout=f"_posts/ko/2026/{changed.name}\n",
                )
                paths = get_changed_post_paths(root / "_posts")
            self.assertEqual(len(paths), 1)
            self.assertTrue(str(paths[0]).endswith("2026-06-01-demo.md"))


if __name__ == "__main__":
    unittest.main()