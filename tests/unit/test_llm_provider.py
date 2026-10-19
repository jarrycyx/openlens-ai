import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from openlens_ai.utils.llm_provider import (
    MINIMAX_DEFAULT_REGION,
    MINIMAX_MODEL_THINKING,
    MINIMAX_REGIONS,
    build_chat_model,
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

    def test_current_minimax_models(self):
        self.assertEqual(list(MINIMAX_MODEL_THINKING), ["MiniMax-M3.1-Flash", "MiniMax-M3"])

    def test_flash_always_uses_adaptive_thinking(self):
        for enable_thinking in (True, False):
            with self.subTest(enable_thinking=enable_thinking):
                self.assertEqual(
                    resolve_minimax_thinking_mode("MiniMax-M3.1-Flash", enable_thinking),
                    "adaptive",
                )
                self.assertEqual(
                    build_extra_body("minimax", "MiniMax-M3.1-Flash", enable_thinking),
                    {"thinking": {"type": "adaptive"}},
                )

    def test_thinking_mode_adaptive_disabled_model(self):
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M3", True), "adaptive")
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M3", False), "disabled")

    def test_thinking_mode_always_on_model(self):
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M2.7", True), "always_on")
        self.assertEqual(resolve_minimax_thinking_mode("MiniMax-M2.7", False), "always_on")

    def test_thinking_mode_unknown_model(self):
        for enable_thinking in (True, False):
            with self.subTest(enable_thinking=enable_thinking):
                self.assertIsNone(resolve_minimax_thinking_mode("unknown-model", enable_thinking))
                self.assertEqual(build_extra_body("minimax", "unknown-model", enable_thinking), {})

    def test_flash_chat_model_forwards_adaptive_thinking_and_options(self):
        chat_models = ModuleType("langchain.chat_models")
        chat_models.init_chat_model = Mock()
        with patch.dict("sys.modules", {"langchain.chat_models": chat_models}):
            for region, explicit_url, expected_url in (
                ("global_en", None, "https://api.minimax.io/v1"),
                ("cn_zh", None, "https://api.minimaxi.com/v1"),
                ("global_en", "https://proxy.example/v1", "https://proxy.example/v1"),
            ):
                with self.subTest(region=region, explicit_url=explicit_url):
                    model_cfg = SimpleNamespace(
                        provider="minimax",
                        model="MiniMax-M3.1-Flash",
                        region=region,
                        base_url=explicit_url,
                        api_key="test-key",
                    )
                    model = build_chat_model(model_cfg, enable_thinking=False, max_tokens=2048)
                    chat_models.init_chat_model.assert_called_with(
                        "MiniMax-M3.1-Flash",
                        base_url=expected_url,
                        model_provider="openai",
                        openai_api_key="test-key",
                        max_tokens=2048,
                        extra_body={"thinking": {"type": "adaptive"}},
                    )
                    self.assertIs(model, chat_models.init_chat_model.return_value)

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
