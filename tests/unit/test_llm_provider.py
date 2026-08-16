import unittest

from openlens_ai.utils.llm_provider import (
    MINIMAX_DEFAULT_REGION,
    MINIMAX_MODEL_INPUT_MODALITIES,
    MINIMAX_REGIONS,
    build_multimodal_message,
    build_extra_body,
    minimax_base_url,
    minimax_input_modalities,
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

    def test_minimax_model_input_modalities(self):
        self.assertEqual(
            MINIMAX_MODEL_INPUT_MODALITIES["MiniMax-M3"],
            ("text", "image", "video"),
        )
        self.assertEqual(minimax_input_modalities("MiniMax-M2.7"), ("text",))

    def test_multimodal_message_formats_image_input(self):
        self.assertEqual(
            build_multimodal_message(
                "minimax",
                "MiniMax-M3",
                "Describe this image",
                "encoded-image",
                "image",
            ),
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,encoded-image"
                            },
                        },
                    ],
                }
            ],
        )

    def test_multimodal_message_formats_video_input(self):
        video_url = "https://media.example/video.mp4"
        message = build_multimodal_message(
            "minimax",
            "MiniMax-M3",
            "Summarize this video",
            video_url,
            "video",
        )
        self.assertEqual(
            message[0]["content"][1],
            {"type": "video_url", "video_url": {"url": video_url}},
        )

    def test_multimodal_message_rejects_unsupported_model_input(self):
        with self.assertRaisesRegex(ValueError, "does not support 'video' input"):
            build_multimodal_message(
                "minimax",
                "MiniMax-M2.7",
                "Summarize this video",
                "https://media.example/video.mp4",
                "video",
            )

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
