from __future__ import annotations

import logging
import re

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger("caltrack.ai")

_SECRET = re.compile(r"(?i)(?:AIza[0-9A-Za-z_\-]{10,}|xai-[A-Za-z0-9_\-]+|sk-[A-Za-z0-9_\-]+|Bearer\s+\S+)")


def raise_for_ai_status(response: httpx.Response) -> None:
    status = response.status_code
    if status < 400:
        return

    detail = _sanitize(_safe_error_detail(response))
    logger.warning("xAI HTTP %s url=%s detail=%s", status, _safe_url(response), detail or "<empty>")

    if status == 429:
        raise AppError("AI_RATE_LIMIT", "The AI provider rate-limited the request. Try again in a moment.", 429)
    if status == 401:
        raise AppError(
            "AI_UNAUTHORIZED",
            _client_message(status, detail, "The AI API key was rejected. Check GEMINI_API_KEY on the FastAPI server."),
            502,
        )
    if status == 403:
        raise AppError(
            "AI_FORBIDDEN",
            _client_message(
                status,
                detail,
                "xAI refused the request (403). The API key is loaded, but the xAI team lacks permission, credits, or a license for this endpoint/model. Check billing and key ACLs in the xAI console.",
            ),
            502,
        )
    if status == 404:
        raise AppError(
            "AI_INVALID_MODEL",
            _client_message(status, detail, "The configured AI_MODEL was not accepted by the provider. Check AI_MODEL."),
            502,
        )
    if status == 413:
        raise AppError("FILE_TOO_LARGE", "The image was too large for the AI provider.", 413)
    if status == 415:
        raise AppError("INVALID_IMAGE", "The AI provider does not support this image type.", 400)
    if status == 400 and _looks_like_model_error(detail):
        raise AppError(
            "AI_INVALID_MODEL",
            _client_message(status, detail, "The configured AI_MODEL was not accepted by the provider. Check AI_MODEL."),
            502,
        )
    if _looks_like_image_error(detail):
        raise AppError("INVALID_IMAGE", _client_message(status, detail, "The AI provider could not read this image."), 400)
    raise AppError(
        "AI_PROVIDER_ERROR",
        _client_message(status, detail, "The AI provider returned an error. Try again later."),
        502,
    )


def _client_message(status: int, detail: str, fallback: str) -> str:
    if not detail:
        return fallback
    if get_settings().is_production:
        return fallback
    return f"{fallback} xAI {status}: {detail}"


def _safe_url(response: httpx.Response) -> str:
    url = str(response.request.url) if response.request is not None else ""
    return _sanitize(url)


def _sanitize(text: str) -> str:
    return _SECRET.sub("[redacted]", text).strip()


def _safe_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return _sanitize((response.text or "")[:500])
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("type") or "")
        if isinstance(error, str):
            code = str(body.get("code") or "")
            return f"{code}: {error}".strip(": ") if code else error
        return str(body.get("message") or "")
    return str(body)[:500]


def _looks_like_model_error(detail: str) -> bool:
    text = detail.lower()
    return "model" in text and any(word in text for word in ("not found", "invalid", "unknown", "does not exist", "not accessible"))


def _looks_like_image_error(detail: str) -> bool:
    text = detail.lower()
    return any(word in text for word in ("image", "unsupported media", "invalid image", "could not process"))
