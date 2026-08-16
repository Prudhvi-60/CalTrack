from __future__ import annotations


def sniff_image_kind(data: bytes) -> str | None:
    if len(data) < 12:
        return None
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def is_readable_image(path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return sniff_image_kind(data) is not None
