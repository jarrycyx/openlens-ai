"""Provider-aware construction of chat and vision clients.

Historically every chat and vision client was created with a hard-coded
``model_provider="openai"`` together with a backend-specific
``extra_body={"chat_template_kwargs": {"enable_thinking": ...}}`` payload. That
payload is only understood by OpenAI-compatible open-weight backends that gate
reasoning through the chat template, and it does not describe how other
providers express their reasoning ("thinking") behaviour.

This module introduces a small provider registry so the agents can target
different providers, resolve their regional base URLs, and translate a single
"enable thinking" intent into the reasoning control each provider/model
actually supports. The default provider keeps the previous behaviour byte for
byte, so existing configurations are unaffected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .config import ModelConfig

DEFAULT_PROVIDER = "openai"

# MiniMax regional endpoint profiles. The global and mainland-China clusters are
# served from different hosts, so the base URL is resolved from the selected
# region when it is not set explicitly on the model configuration.
MINIMAX_REGIONS: dict[str, dict[str, str]] = {
    "global_en": {
        "openai_base_url": "https://api.minimax.io/v1",
        "anthropic_base_url": "https://api.minimax.io/anthropic",
        "docs_root": "https://platform.minimax.io/docs",
    },
    "cn_zh": {
        "openai_base_url": "https://api.minimaxi.com/v1",
        "anthropic_base_url": "https://api.minimaxi.com/anthropic",
        "docs_root": "https://platform.minimaxi.com/docs",
    },
}
MINIMAX_DEFAULT_REGION = "global_en"

# Per-model reasoning ("thinking") capabilities for the MiniMax provider. The
# tuple lists the thinking modes each model supports; the first entry is used as
# the fallback when a requested mode is unavailable.
MINIMAX_MODEL_THINKING: dict[str, tuple[str, ...]] = {
    "MiniMax-M3": ("adaptive", "disabled"),
    "MiniMax-M2.7": ("always_on",),
}


def normalize_provider(provider: Optional[str]) -> str:
    """Return a canonical provider identifier, defaulting to ``openai``."""
    return (provider or DEFAULT_PROVIDER).strip().lower()


def resolve_minimax_region(region: Optional[str]) -> str:
    """Return a known MiniMax region key, defaulting to the global cluster."""
    key = (region or MINIMAX_DEFAULT_REGION).strip().lower()
    if key not in MINIMAX_REGIONS:
        raise ValueError(
            f"Unknown MiniMax region {region!r}; expected one of {sorted(MINIMAX_REGIONS)}"
        )
    return key


def minimax_base_url(region: Optional[str]) -> str:
    """Return the OpenAI-compatible MiniMax base URL for ``region``."""
    return MINIMAX_REGIONS[resolve_minimax_region(region)]["openai_base_url"]


def resolve_minimax_thinking_mode(model: str, enable_thinking: bool) -> Optional[str]:
    """Map an ``enable_thinking`` intent onto a MiniMax model's thinking mode.

    Returns ``None`` for models with no registered thinking capability. Models
    whose only mode is ``always_on`` always reason and expose no toggle, so the
    caller should not send any thinking control for them.
    """
    modes = MINIMAX_MODEL_THINKING.get(model)
    if not modes:
        return None
    if "always_on" in modes:
        return "always_on"
    if enable_thinking:
        return "adaptive" if "adaptive" in modes else modes[0]
    return "disabled" if "disabled" in modes else modes[0]


def build_extra_body(
    provider: Optional[str],
    model: str,
    enable_thinking: bool,
    max_tokens: Optional[int] = None,
) -> dict[str, Any]:
    """Build the ``extra_body`` request payload for the given provider/model."""
    extra: dict[str, Any] = {}
    if normalize_provider(provider) == "minimax":
        mode = resolve_minimax_thinking_mode(model, enable_thinking)
        # ``always_on`` models cannot be toggled, so no thinking control is sent.
        if mode in ("adaptive", "disabled"):
            extra["thinking"] = {"type": mode}
    else:
        # OpenAI-compatible open-weight backends gate reasoning through the chat
        # template rather than a first-class request field.
        extra["chat_template_kwargs"] = {"enable_thinking": enable_thinking}
        if max_tokens is not None:
            extra["max_tokens"] = max_tokens
    return extra


def resolve_base_url(provider: Optional[str], model_cfg: "ModelConfig") -> Optional[str]:
    """Resolve the base URL, falling back to the MiniMax regional endpoint."""
    if getattr(model_cfg, "base_url", None):
        return model_cfg.base_url
    if normalize_provider(provider) == "minimax":
        return minimax_base_url(getattr(model_cfg, "region", None))
    return None


def build_chat_model(
    model_cfg: "ModelConfig",
    *,
    enable_thinking: bool,
    max_tokens: Optional[int] = None,
):
    """Create a chat/vision client for ``model_cfg`` in a provider-aware way.

    The provider is read from ``model_cfg.provider`` (default ``openai``). All
    supported providers currently speak the OpenAI-compatible protocol, so the
    LangChain ``openai`` adapter is used while the reasoning payload and base URL
    are derived from the selected provider.
    """
    from langchain.chat_models import init_chat_model

    provider = normalize_provider(getattr(model_cfg, "provider", None))
    init_kwargs: dict[str, Any] = {
        "base_url": resolve_base_url(provider, model_cfg),
        "model_provider": "openai",
        "openai_api_key": getattr(model_cfg, "api_key", None),
    }
    if max_tokens is not None:
        init_kwargs["max_tokens"] = max_tokens
    extra_body = build_extra_body(
        provider, getattr(model_cfg, "model", ""), enable_thinking, max_tokens=max_tokens
    )
    if extra_body:
        init_kwargs["extra_body"] = extra_body
    return init_chat_model(model_cfg.model, **init_kwargs)
