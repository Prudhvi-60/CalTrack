"""CalTrack model-improvement infrastructure. Does not train until enough validated data exists."""

__all__ = ["ROOT"]

from pathlib import Path

ROOT = Path(__file__).resolve().parent
