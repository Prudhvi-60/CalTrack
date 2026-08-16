from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.schemas.ai import FoodAnalysisResult
from app.services.ai.gemini_client import generate_vision_json
from app.services.ai.pipeline import FoodAnalysisPipeline, parse_label_result, parse_llm_food_result

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPT_DIR / name).read_text(encoding="utf-8")


class VisionService:
    def __init__(
        self,
        settings: Settings | None = None,
        completer: Callable[[str, bytes, str], dict[str, Any]] | None = None,
        pipeline: FoodAnalysisPipeline | None = None,
        client: object | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.completer = completer
        self.pipeline = pipeline or FoodAnalysisPipeline()
        self._client = client

    def analyze_food_image(self, image: bytes, content_type: str) -> FoodAnalysisResult:
        raw = self._complete(_load_prompt("food_image.txt"), image, content_type)
        parsed = parse_llm_food_result(raw)
        return self.pipeline.finalize_llm_photo(parsed)

    def analyze_nutrition_label(self, image: bytes, content_type: str) -> FoodAnalysisResult:
        raw = self._complete(_load_prompt("label_image.txt"), image, content_type)
        parsed = parse_label_result(raw, analysis_type="label")
        return self.pipeline.finalize_label(parsed)

    def _complete(self, prompt: str, image: bytes, content_type: str) -> dict[str, Any]:
        if not self.settings.ai_api_key:
            raise AppError(
                "AI_NOT_CONFIGURED",
                "AI analysis is not configured on the server. Set GEMINI_API_KEY in the FastAPI environment or the project .env file.",
                503,
            )
        if self.completer is not None:
            return self.completer(prompt, image, content_type)
        return generate_vision_json(self.settings, prompt, image, content_type)


def _extract_json(content: str) -> dict:
    from app.services.ai.gemini_client import _parse_json_object

    return _parse_json_object(content)
