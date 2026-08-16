from __future__ import annotations

import struct

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
}

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_PIXELS = 40_000_000
MAX_EDGE = 12_000


def sniff_image_kind(data: bytes) -> str | None:
    if data.startswith(_JPEG_MAGIC):
        return "jpeg"
    if data.startswith(_PNG_MAGIC):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def content_type_kind(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return ALLOWED_IMAGE_TYPES.get(content_type.split(";")[0].strip().lower())


def image_dimensions(data: bytes, kind: str) -> tuple[int, int] | None:
    if kind == "png":
        if len(data) < 24:
            return None
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    if kind == "jpeg":
        return _jpeg_size(data)
    if kind == "webp":
        return _webp_size(data)
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    index = 2
    length = len(data)
    while index + 9 < length:
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height, width = struct.unpack(">HH", data[index + 5 : index + 9])
            return int(width), int(height)
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            index += 2
            continue
        if index + 4 > length:
            break
        size = struct.unpack(">H", data[index + 2 : index + 4])[0]
        index += 2 + size
    return None


def _webp_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30:
        return None
    if data[12:16] == b"VP8X" and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if data[12:16] == b"VP8 " and len(data) >= 30:
        width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return width, height
    return None


def reject_if_image_too_large(data: bytes, kind: str) -> None:
    from app.core.exceptions import AppError

    size = image_dimensions(data, kind)
    if size is None:
        return
    width, height = size
    if width <= 0 or height <= 0:
        raise AppError("INVALID_IMAGE", "Image dimensions are invalid", 400)
    if width > MAX_EDGE or height > MAX_EDGE or width * height > MAX_PIXELS:
        raise AppError("INVALID_IMAGE", "Image dimensions are too large", 400)
