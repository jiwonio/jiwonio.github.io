import unittest
from unittest.mock import patch

from llm_client import TextGenerationResult
from post_common import generate_with_retry

class GenerateWithRetryTests(unittest.TestCase):
    @patch("post_common.llm_generate_text")
    @patch("api_monitor.notify_llm_usage")
    @patch("post_common.resolve_text_providers", return_value=["gemini"])
    @patch("post_common.pick_provider_for_attempt", return_value="gemini")
    @patch("post_common.get_text_model", return_value="gemini-2.5-pro")
    def test_appends_validation_error_to_prompt_on_retry(
        self,
        _mock_model,
        _mock_pick,
        _mock_resolve,
        _mock_notify,
        mock_generate,
    ):
        prompts: list[str] = []

        def fake_generate(*, prompt, provider, model, system_prompt=None):
            prompts.append(prompt)
            if len(prompts) == 1:
                return TextGenerationResult("draft without marker", len(prompt), 20)
            return TextGenerationResult("intro\n<!--more-->\nbody", len(prompt), 30)

        def validate_fn(content):
            if "<!--more-->" not in content:
                raise ValueError("missing <!--more-->")
            return {"title": "ok"}, "ok-slug"

        mock_generate.side_effect = fake_generate

        with patch("post_common.sanitize_generated_content", side_effect=lambda x: x):
            with patch("post_common.strip_preamble", side_effect=lambda x: x):
                with patch("post_common.strip_code_fence", side_effect=lambda x: x):
                    generate_with_retry(
                        "base prompt",
                        validate_fn,
                        max_retries=2,
                    )

        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0], "base prompt")
        self.assertIn("Previous attempt failed validation", prompts[1])
        self.assertIn("missing <!--more-->", prompts[1])

if __name__ == "__main__":
    unittest.main()
