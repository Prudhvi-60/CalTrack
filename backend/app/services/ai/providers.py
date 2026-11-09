from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError


@dataclass(slots=True)
class ModelProviderConfig:
    provider: str
    model: str
    api_key: str = ""
    base_url: str | None = None
    timeout_seconds: float = 45.0


class HuggingFaceProvider:
    """Small compatibility layer for Hugging Face-backed AI inference.

    The runtime keeps Gemini as the default production provider, while exposing a
    real Hugging Face path for experimentation and model switching.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.huggingface_model) and (
            bool(self.settings.huggingface_api_key) or self.settings.enable_huggingface
        )

    def generate_text(self, prompt: str, *, image: bytes | None = None, content_type: str | None = None) -> str:
        if not self.configured:
            raise AppError(
                "AI_NOT_CONFIGURED",
                "Hugging Face is not configured. Set HUGGINGFACE_API_KEY or enable the provider in the backend environment.",
                503,
            )
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise AppError(
                "AI_PROVIDER_ERROR",
                "Hugging Face support is not installed. Add huggingface-hub to backend dependencies.",
                503,
            ) from exc

        client = InferenceClient(
            model=self.settings.huggingface_model,
            token=self.settings.huggingface_api_key or None,
            timeout=self.settings.ai_timeout_seconds,
        )
        try:
            if image is not None:
                result = client.image_to_text(image, prompt=prompt)
            else:
                result = client.text_generation(prompt, max_new_tokens=256)
            return str(result).strip()
        except Exception as exc:
            raise AppError(
                "AI_PROVIDER_ERROR",
                "Hugging Face model inference failed. Check the model ID and provider configuration.",
                502,
            ) from exc

    def analyze_image(self, prompt: str, image: bytes, content_type: str | None = None) -> dict[str, Any]:
        return {"text": self.generate_text(prompt, image=image, content_type=content_type), "provider": "huggingface"}


def build_model_registry(settings: Settings | None = None) -> dict[str, dict[str, Any]]:
    resolved = settings or get_settings()
    registry = {
        "gemini": {
            "configured": bool(resolved.ai_api_key),
            "model": resolved.ai_model,
            "provider": "gemini",
        },
        "huggingface": {
            "configured": bool(resolved.huggingface_model) and (bool(resolved.huggingface_api_key) or resolved.enable_huggingface),
            "model": resolved.huggingface_model,
            "provider": "huggingface",
        },
    }
    return registry
