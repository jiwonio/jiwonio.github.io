import os
import unittest
from unittest.mock import patch

from llm_client import (
    filter_available_providers,
    pick_provider_for_attempt,
    pick_translation_target,
    resolve_image_providers,
    resolve_text_providers,
    resolve_translation_providers,
)

class LlmClientTests(unittest.TestCase):
    def test_resolve_text_providers_deep_dive_prefers_gemini(self):
        env = {
            "GEMINI_API_KEY": "g",
            "ANTHROPIC_API_KEY": "a",
            "OPENAI_API_KEY": "o",
            "XAI_API_KEY": "x",
        }
        with patch.dict(os.environ, env, clear=True):
            providers = resolve_text_providers("deep-dive")
        self.assertEqual(providers[0], "gemini")
        self.assertEqual(len(providers), 4)

    def test_resolve_text_providers_honors_override(self):
        env = {
            "GEMINI_API_KEY": "g",
            "ANTHROPIC_API_KEY": "a",
        }
        with patch.dict(os.environ, env, clear=True):
            providers = resolve_text_providers("deep-dive", override="anthropic")
        self.assertEqual(providers[0], "anthropic")
        self.assertIn("gemini", providers)

    def test_resolve_text_providers_skips_missing_keys(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "g"}, clear=True):
            providers = resolve_text_providers("deep-dive")
        self.assertEqual(providers, ["gemini"])

    def test_pick_provider_for_attempt_rotates(self):
        providers = ["gemini", "anthropic", "openai"]
        self.assertEqual(pick_provider_for_attempt(providers, 1), "gemini")
        self.assertEqual(pick_provider_for_attempt(providers, 2), "anthropic")
        self.assertEqual(pick_provider_for_attempt(providers, 4), "gemini")

    def test_pick_translation_target_uses_cheaper_models_on_retry(self):
        providers = ["gemini", "anthropic"]
        provider, model = pick_translation_target(providers, 1)
        self.assertEqual(provider, "gemini")
        self.assertEqual(model, "gemini-2.5-flash")

        provider, model = pick_translation_target(providers, 3)
        self.assertEqual(provider, "gemini")
        self.assertEqual(model, "gemini-2.5-pro")

    def test_resolve_translation_providers_defaults_to_chain(self):
        env = {
            "GEMINI_API_KEY": "g",
            "OPENAI_API_KEY": "o",
        }
        with patch.dict(os.environ, env, clear=True):
            providers = resolve_translation_providers()
        self.assertEqual(providers, ["gemini", "openai"])

    def test_resolve_image_providers_gemini_then_xai(self):
        env = {
            "GEMINI_API_KEY": "g",
            "XAI_API_KEY": "x",
        }
        with patch.dict(os.environ, env, clear=True):
            providers = resolve_image_providers()
        self.assertEqual(providers, ["gemini", "xai"])

    def test_filter_available_providers(self):
        env = {"ANTHROPIC_API_KEY": "a"}
        with patch.dict(os.environ, env, clear=True):
            available = filter_available_providers(("gemini", "anthropic", "openai"))
        self.assertEqual(available, ["anthropic"])

if __name__ == "__main__":
    unittest.main()
