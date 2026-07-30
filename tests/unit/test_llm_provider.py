import unittest

from openlens_ai.utils.llm_provider import (
    MINIMAX_DEFAULT_REGION,
    MINIMAX_REGIONS,
    build_extra_body,
    minimax_base_url,
    normalize_provider,
    resolve_minimax_region,
    resolve_minimax_thinking_mode,
)


class TestLLMProvider(unittest.TestCase):
    """Unit tests for the provider-aware client helpers."""

    def test_normalize_provider_defaults_and_case(self):
        self.assertEqual(normalize_provider(None), "openai")
        self.assertEqual(normalize_provider(""), "openai")
        self.assertEqual(normalize_provider("  MiniMax "), "minimax")

    def test_minimax_regions_endpoints(self):
        self.assertEqual(minimax_base_url("global_en"), "https://api.minimax.io/v1")
        self.assertEqual(minimax_base_url("cn_zh"), "https://api.minimaxi.com/v1")
        self.assertEqual(
            MINIMAX_REGIONS["global_en"]["anthropic_base_url"],
            "https://api.minimax.io/anthropic",
        )
        self.assertEqual(
            MINIMAX_REGIONS["cn_zh"]["anthropic_base_url"],
            "https://api.minimaxi.com/anthropic",
        )

    def test_resolve_minimax_region(self):
        self.assertEqual(resolve_minimax_region(None), MINIMAX_DEFAULT_REGION)
        self.assertEqual(resolve_minimax_region("CN_ZH"), "cn_zh")
        with self.assertRaises(ValueError):
            resolve_minimax_region("mars")

    def test_thinking_mode_adaptive_disabled_model(self):
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M3", True), "adaptive")
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M3", False), "disabled")

    def test_thinking_mode_always_on_model(self):
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M2.7", True), "always_on")
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M2.7", False), "always_on")

    def test_thinking_mode_unknown_model(self):
        self.assertIsNone(resolve_minimax_thinking_mode("unknown-model", True))

    def test_extra_body_openai_default_matches_legacy_payload(self):
        self.assertEqual(
            build_extra_body("openai", "any-model", True),
            {"chat_template_kwargs": {"enable_thinking": True}},
        )
        self.assertEqual(
            build_extra_body(None, "any-model", False),
            {"chat_template_kwargs": {"enable_thinking": False}},
        )

    def test_extra_body_openai_with_max_tokens(self):
        self.assertEqual(
            build_extra_body("openai", "any-model", True, max_tokens=1234),
            {"chat_template_kwargs": {"enable_thinking": True}, "max_tokens": 1234},
        )

    def test_extra_body_minimax_toggleable_model(self):
        self.assertEqual(
            build_extra_body("minimax", "MiniMax-M3", True),
            {"thinking": {"type": "adaptive"}},
        )
        self.assertEqual(
            build_extra_body("minimax", "MiniMax-M3", False),
            {"thinking": {"type": "disabled"}},
        )

    def test_extra_body_minimax_always_on_sends_no_thinking_control(self):
        self.assertEqual(build_extra_body("minimax", "MiniMax-M2.7", True), {})
        self.assertEqual(build_extra_body("minimax", "MiniMax-M2.7", False), {})

    def test_extra_body_minimax_never_uses_chat_template_kwargs(self):
        self.assertNotIn("chat_template_kwargs", build_extra_body("minimax", "MiniMax-M3", True))


if __name__ == "__main__":
    unittest.main()
