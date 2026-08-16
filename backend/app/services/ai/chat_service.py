from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.models import User
from app.schemas.chat import ChatMessage, ChatResponse, ToolTrace
from app.schemas.nutrition import DailyNutritionResponse
from app.services.ai.chat_tools import TOOL_DEFINITIONS, ChatToolbox
from app.services.ai.gemini_client import generate_chat_message
from sqlalchemy.orm import Session

_PROMPT = (Path(__file__).parent / "prompts" / "chat.txt").read_text(encoding="utf-8")
_MAX_TOOL_ROUNDS = 6
_MAX_HISTORY = 12


class ChatCompleter(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]: ...


class GeminiChatCompleter:
    def __init__(self, settings: Settings, client: object | None = None) -> None:
        self.settings = settings
        self._client = client

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.settings.ai_api_key:
            raise AppError(
                "AI_NOT_CONFIGURED",
                "AI chat is not configured on the server. Set GEMINI_API_KEY in the FastAPI environment or the project .env file.",
                503,
            )
        return generate_chat_message(self.settings, messages, tools)


class HttpChatCompleter(GeminiChatCompleter):
    """Kept as an alias so existing imports and tests continue to work."""


class ChatService:
    def __init__(
        self,
        db: Session,
        user: User,
        completer: ChatCompleter | None = None,
        settings: Settings | None = None,
        client: object | None = None,
    ) -> None:
        self.toolbox = ChatToolbox(db, user)
        self.completer = completer or GeminiChatCompleter(settings or get_settings(), client)

    def ask(self, message: str, history: list[ChatMessage]) -> ChatResponse:
        snapshot = self.toolbox.nutrition.daily(None)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": _PROMPT},
            {"role": "system", "content": format_nutrition_context(snapshot)},
        ]
        for item in history[-_MAX_HISTORY:]:
            messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": message.strip()})
        traces: list[ToolTrace] = []

        for _ in range(_MAX_TOOL_ROUNDS):
            reply = self.completer.complete(messages, TOOL_DEFINITIONS)
            tool_calls = reply.get("tool_calls") or []
            if not tool_calls:
                content = (reply.get("content") or "").strip()
                if not content:
                    raise AppError("AI_INVALID_RESPONSE", "AI returned an empty reply", 502)
                return ChatResponse(reply=content, tools_used=traces)
            messages.append(reply)
            for call in tool_calls:
                function = call.get("function") or {}
                name = str(function.get("name") or "")
                raw_args = _parse_args(function.get("arguments") or "{}")
                ok, result, summary = self.toolbox.execute(name, raw_args)
                traces.append(ToolTrace(name=name, ok=ok, summary=summary))
                messages.append(
                    {
                        "role": "tool",
                        "name": name,
                        "tool_call_id": call.get("id") or name,
                        "content": json.dumps(result, default=str),
                    }
                )
        raise AppError("AI_INVALID_RESPONSE", "The assistant exceeded the tool-call limit", 502)


def format_nutrition_context(snapshot: DailyNutritionResponse) -> str:
    totals = snapshot.totals
    goals = snapshot.goals
    remaining = snapshot.remaining
    lines = [
        "CalTrack nutrition snapshot for this authenticated user (authoritative; do not invent other totals):",
        f"Date (UTC): {snapshot.date.isoformat()}",
        f"Calories consumed today: {_num(totals.calories)} kcal",
        f"Protein consumed: {_num(totals.protein)} g",
        f"Carbohydrates consumed: {_num(totals.carbohydrates)} g",
        f"Fat consumed: {_num(totals.fat)} g",
    ]
    if goals is None:
        lines.append("Daily calorie goal: not set")
        lines.append("Protein goal: not set")
        lines.append("Calories remaining: unknown (no calorie goal)")
        lines.append("Do not invent a daily calorie goal or remaining calories.")
    else:
        lines.append(f"Daily calorie goal: {_num(goals.daily_calorie_target)} kcal")
        lines.append(f"Protein goal: {_num(goals.protein_target)} g")
        lines.append(f"Carbohydrate goal: {_num(goals.carb_target)} g")
        lines.append(f"Fat goal: {_num(goals.fat_target)} g")
        if remaining is not None:
            lines.append(
                f"Calories remaining: {_num(remaining.calories)} kcal "
                "(daily calorie goal minus calories consumed today)"
            )
            lines.append(f"Protein remaining: {_num(remaining.protein)} g")
            lines.append(f"Carbohydrate remaining: {_num(remaining.carbohydrates)} g")
            lines.append(f"Fat remaining: {_num(remaining.fat)} g")
    if snapshot.meals:
        lines.append("Meals logged today:")
        for meal in snapshot.meals:
            lines.append(
                f"- {meal.meal_type}: {_num(meal.calories)} kcal, {meal.food_count} food item(s)"
            )
    else:
        lines.append("Meals logged today: none")
    if snapshot.recent_foods:
        lines.append("Foods logged today:")
        for food in snapshot.recent_foods[:12]:
            lines.append(
                f"- {food.food_name}: {_num(food.quantity)} {food.unit}, {_num(food.calories)} kcal, "
                f"{_num(food.protein)} g protein ({food.meal_type})"
            )
    return "\n".join(lines)


def _num(value: Decimal | int | float) -> str:
    quantized = Decimal(value).quantize(Decimal("0.01"))
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _parse_args(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AppError("AI_INVALID_RESPONSE", "Tool arguments were not valid JSON", 502) from exc
    if not isinstance(parsed, dict):
        raise AppError("AI_INVALID_RESPONSE", "Tool arguments must be an object", 502)
    return parsed
