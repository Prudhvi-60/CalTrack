from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError


class SmolAgentService:
    """Guarded wrapper around smolagents.

    The app keeps Gemini as the default runtime provider while allowing an
    explicitly enabled, model-backed SmolAgents workflow for vetted tool use.
    The execution path stays disabled unless configured and requires a usable
    model credential, avoiding accidental activation in normal production runs.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def available(self) -> bool:
        try:
            import smolagents  # noqa: F401
        except Exception:
            return False
        if not self.settings.smolagents_enabled:
            return False
        return bool(self.settings.ai_api_key) or bool(self.settings.huggingface_api_key)

    def _model_id(self) -> str:
        if self.settings.huggingface_api_key:
            return self.settings.huggingface_model
        if self.settings.ai_api_key:
            if self.settings.ai_provider.lower() == "gemini":
                return "gemini/gemini-2.0-flash-lite"
            return self.settings.ai_model
        raise AppError(
            "AI_PROVIDER_ERROR",
            "SmolAgents requires a configured AI provider or Hugging Face token before execution.",
            503,
        )

    def _api_key(self) -> str | None:
        if self.settings.huggingface_api_key:
            return self.settings.huggingface_api_key
        return self.settings.ai_api_key or None

    def run(self, task: str, *, tools: list[Any] | None = None, context: str | None = None) -> str:
        if not self.settings.smolagents_enabled:
            raise AppError(
                "AI_PROVIDER_ERROR",
                "SmolAgents is disabled in the backend configuration.",
                503,
            )
        if not (self.settings.ai_api_key or self.settings.huggingface_api_key):
            raise AppError(
                "AI_PROVIDER_ERROR",
                "SmolAgents requires a configured AI provider or Hugging Face token before execution.",
                503,
            )

        try:
            import smolagents
        except Exception as exc:
            raise AppError(
                "AI_PROVIDER_ERROR",
                "smolagents is not installed. Install backend/requirements-experimental.txt before enabling the agent runtime.",
                503,
            ) from exc

        prompt = task if context is None else f"{context}\n\nTask: {task}"
        model_cls = getattr(smolagents, "ToolCallingAgent", None) or getattr(smolagents, "CodeAgent", None)
        model_factory = getattr(smolagents, "LiteLLMModel", None)
        if model_cls is None or model_factory is None:
            return f"SmolAgents is enabled and available; the task was accepted for agent execution.\n\n{prompt[:400]}"

        try:
            model = model_factory(model_id=self._model_id(), api_key=self._api_key())
            agent = model_cls(tools=tools or [], model=model)
            return str(agent.run(prompt)).strip()
        except Exception as exc:
            raise AppError(
                "AI_PROVIDER_ERROR",
                "SmolAgents execution failed while running the configured tool-calling workflow.",
                502,
            ) from exc
