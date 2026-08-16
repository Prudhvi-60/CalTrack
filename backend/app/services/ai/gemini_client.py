from __future__ import annotations

import json
import logging
import re
import threading
import time
from typing import Any

from app.core.config import Settings
from app.core.exceptions import AppError

logger = logging.getLogger("caltrack.ai")

_SECRET = re.compile(r"(?i)(?:AIza[0-9A-Za-z_\-]{10,}|xai-[A-Za-z0-9_\-]+|sk-[A-Za-z0-9_\-]+|Bearer\s+\S+|GEMINI_API_KEY\s*=\s*\S+)")
_lock = threading.Lock()
_shared_client: Any = None
_shared_key: str | None = None


def _sanitize(text: str) -> str:
    return _SECRET.sub("[redacted]", text).strip()


def map_gemini_error(exc: Exception, *, source: str = "vision") -> AppError:
    status = int(getattr(exc, "code", None) or getattr(exc, "status_code", None) or 0)
    detail = _sanitize(str(exc)[:400])
    logger.warning("Gemini error status=%s source=%s detail=%s", status or "n/a", source, detail or type(exc).__name__)

    if isinstance(exc, TimeoutError):
        return AppError("AI_TIMEOUT", "The AI provider timed out", 504)
    if status == 401:
        return AppError("AI_UNAUTHORIZED", "AI service authentication failed. Please check server configuration.", 502)
    if status == 403:
        return AppError(
            "AI_FORBIDDEN",
            "AI analysis service is temporarily unavailable. Please try again.",
            502,
        )
    if status == 404:
        return AppError("AI_INVALID_MODEL", "The configured AI_MODEL was not accepted. Check AI_MODEL.", 502)
    if status == 429:
        return AppError("AI_RATE_LIMIT", "AI analysis limit reached. Please try again later.", 429)
    if status in {400, 415} and source == "vision":
        return AppError("INVALID_IMAGE", "The AI provider could not read this image.", 400)
    return AppError("AI_PROVIDER_ERROR", "AI analysis service is temporarily unavailable. Please try again.", 502)


def get_gemini_client(settings: Settings):
    """Return a process-wide Gemini client. Do not close it per request."""
    global _shared_client, _shared_key
    if not settings.ai_api_key:
        raise AppError(
            "AI_NOT_CONFIGURED",
            "AI analysis is not configured on the server. Set GEMINI_API_KEY in the FastAPI environment or the project .env file.",
            503,
        )
    with _lock:
        if _shared_client is not None and _shared_key == settings.ai_api_key:
            return _shared_client
        previous = _shared_client
        _shared_client = None
        _shared_key = None
    _close_client_instance(previous)
    from google import genai

    with _lock:
        if _shared_client is not None and _shared_key == settings.ai_api_key:
            return _shared_client
        _shared_client = genai.Client(api_key=settings.ai_api_key)
        _shared_key = settings.ai_api_key
        return _shared_client


def close_gemini_client() -> None:
    global _shared_client, _shared_key
    with _lock:
        previous = _shared_client
        _shared_client = None
        _shared_key = None
    _close_client_instance(previous)


def init_gemini_client(settings: Settings) -> None:
    if settings.ai_configured:
        get_gemini_client(settings)


def _close_client_instance(client: Any) -> None:
    if client is None:
        return
    closer = getattr(client, "close", None)
    if callable(closer):
        try:
            closer()
        except Exception:
            logger.debug("Gemini client close failed", exc_info=True)


def generate_vision_json(settings: Settings, prompt: str, image: bytes, content_type: str) -> dict[str, Any]:
    from google.genai import types

    started = time.perf_counter()
    client = get_gemini_client(settings)
    try:
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=[
                types.Part.from_bytes(data=image, mime_type=content_type),
                types.Part.from_text(text="Analyze this image and return JSON only."),
            ],
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
    except TimeoutError as exc:
        raise map_gemini_error(exc, source="vision") from exc
    except Exception as exc:
        raise map_gemini_error(exc, source="vision") from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("Gemini analysis completed in %.0f ms", elapsed_ms)
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise AppError("AI_INVALID_RESPONSE", "AI returned an unexpected payload", 502)
    return _parse_json_object(text)


def generate_structured_json(settings: Settings, prompt: str, parts: list[Any]) -> dict[str, Any]:
    """JSON completion for text and/or image parts using the shared Gemini client."""
    from google.genai import types

    if not parts:
        raise AppError("AI_INVALID_RESPONSE", "Extraction request was empty", 400)
    started = time.perf_counter()
    client = get_gemini_client(settings)
    try:
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                temperature=0.1,
                response_mime_type="application/json",
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
    except TimeoutError as exc:
        raise map_gemini_error(exc, source="extract") from exc
    except Exception as exc:
        raise map_gemini_error(exc, source="extract") from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("Gemini extraction completed in %.0f ms", elapsed_ms)
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise AppError("AI_INVALID_RESPONSE", "AI returned an unexpected payload", 502)
    return _parse_json_object(text)


def generate_chat_message(
    settings: Settings,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    from google.genai import types

    system, contents = _chat_contents(messages)
    declarations = _function_declarations(tools)
    config = types.GenerateContentConfig(
        system_instruction=system or None,
        temperature=0.2,
        tools=[types.Tool(function_declarations=declarations)] if declarations else None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    if not contents:
        raise AppError("AI_INVALID_RESPONSE", "Chat request was missing a text message", 400)
    started = time.perf_counter()
    client = get_gemini_client(settings)
    try:
        response = client.models.generate_content(
            model=settings.ai_model,
            contents=contents,
            config=config,
        )
    except TimeoutError as exc:
        raise map_gemini_error(exc, source="chat") from exc
    except Exception as exc:
        raise map_gemini_error(exc, source="chat") from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("Gemini chat request completed in %.0f ms", elapsed_ms)

    function_calls = _response_function_calls(response)
    if function_calls:
        tool_calls = []
        for index, call in enumerate(function_calls):
            name = str(getattr(call, "name", "") or "")
            args = getattr(call, "args", None) or {}
            tool_calls.append(
                {
                    "id": getattr(call, "id", None) or f"{name}-{index}",
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(dict(args))},
                }
            )
        return {"role": "assistant", "content": None, "tool_calls": tool_calls}
    content = (getattr(response, "text", None) or "").strip()
    return {"role": "assistant", "content": content, "tool_calls": []}


def _function_declarations(tools: list[dict[str, Any]]) -> list[Any]:
    from google.genai import types

    declarations = []
    for tool in tools:
        function = tool.get("function") or {}
        name = str(function.get("name") or "")
        if not name:
            continue
        declarations.append(
            types.FunctionDeclaration(
                name=name,
                description=str(function.get("description") or ""),
                parameters=function.get("parameters") or {"type": "object", "properties": {}},
            )
        )
    return declarations


def _chat_contents(messages: list[dict[str, Any]]) -> tuple[str, list[Any]]:
    from google.genai import types

    system_parts: list[str] = []
    contents: list[Any] = []
    for message in messages:
        role = str(message.get("role") or "")
        if role == "system":
            system_parts.append(str(message.get("content") or ""))
            continue
        if role == "tool":
            name = str(message.get("name") or message.get("tool_call_id") or "tool")
            raw = message.get("content") or "{}"
            try:
                payload = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                payload = {"result": raw}
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(name=name, response=payload if isinstance(payload, dict) else {"result": payload})],
                )
            )
            continue
        if role in {"assistant", "model"}:
            parts = []
            for call in message.get("tool_calls") or []:
                function = call.get("function") or {}
                name = str(function.get("name") or "")
                raw_args = function.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}
                parts.append(types.Part.from_function_call(name=name, args=args if isinstance(args, dict) else {}))
            text = str(message.get("content") or "").strip()
            if text:
                parts.append(types.Part.from_text(text=text))
            if parts:
                contents.append(types.Content(role="model", parts=parts))
            continue
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=str(message.get("content") or ""))])
        )
    return "\n\n".join(part for part in system_parts if part), contents


def _response_function_calls(response: Any) -> list[Any]:
    calls = list(getattr(response, "function_calls", None) or [])
    if calls:
        return calls
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            call = getattr(part, "function_call", None)
            if call is not None:
                calls.append(call)
    return calls


def _parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AppError("AI_INVALID_RESPONSE", "AI did not return valid JSON", 502) from exc
    if not isinstance(parsed, dict):
        raise AppError("AI_INVALID_RESPONSE", "AI JSON must be an object", 502)
    return parsed
