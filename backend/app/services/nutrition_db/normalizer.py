from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_FUZZY_MIN = 0.9
_CONFUSABLE = {
    frozenset({"chicken", "chickpea"}),
    frozenset({"dal", "dosa"}),
    frozenset({"naan", "banana"}),
}

_IRREGULAR = {
    "chapatis": "chapati",
    "rotis": "roti",
    "lentils": "lentil",
    "potatoes": "potato",
    "tomatoes": "tomato",
    "leaves": "leaf",
}


@dataclass(frozen=True)
class NormalizeResult:
    original: str
    cleaned: str
    canonical: str
    confidence: float
    method: str


def _load_alias_config() -> dict:
    path = _DATA_DIR / "food_aliases.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def alias_config() -> dict:
    return _load_alias_config()


def _squash(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _singularize(word: str) -> str:
    if word in _IRREGULAR:
        return _IRREGULAR[word]
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]
    if len(word) > 3 and word.endswith("es") and not word.endswith("ses"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _strip_adjectives(text: str) -> str:
    adjectives = set(alias_config().get("adjectives") or [])
    tokens = [token for token in text.split() if token not in adjectives]
    return " ".join(tokens) or text


def _confusable(a: str, b: str) -> bool:
    return frozenset({a, b}) in _CONFUSABLE


class FoodNormalizer:
    """Maps vision labels to database food ids using aliases, then conservative fuzzy match."""

    def __init__(self, known_names: list[str] | None = None) -> None:
        self._aliases = { _squash(key): value for key, value in (alias_config().get("aliases") or {}).items() }
        self._known = [_squash(name) for name in (known_names or [])]

    def set_known_names(self, names: list[str]) -> None:
        self._known = [_squash(name) for name in names]

    def normalize(self, name: str) -> NormalizeResult:
        original = name.strip()
        cleaned = _squash(original)
        if not cleaned:
            return NormalizeResult(original, "", "", 0.0, "empty")

        alias_hit = self._aliases.get(cleaned)
        if alias_hit:
            return NormalizeResult(original, cleaned, alias_hit, 1.0, "alias")

        if cleaned in self._known:
            return NormalizeResult(original, cleaned, cleaned, 1.0, "exact")

        stripped = _strip_adjectives(cleaned)
        alias_stripped = self._aliases.get(stripped)
        if alias_stripped:
            return NormalizeResult(original, stripped, alias_stripped, 0.97, "alias-stripped")
        if stripped in self._known:
            return NormalizeResult(original, stripped, stripped, 0.97, "exact-stripped")

        singular = " ".join(_singularize(token) for token in stripped.split())
        alias_singular = self._aliases.get(singular)
        if alias_singular:
            return NormalizeResult(original, singular, alias_singular, 0.95, "alias-singular")
        if singular in self._known:
            return NormalizeResult(original, singular, singular, 0.95, "exact-singular")

        fuzzy = self._fuzzy(singular or stripped)
        if fuzzy:
            return fuzzy

        return NormalizeResult(original, singular or stripped, singular or stripped, 0.2, "unmatched")

    def _fuzzy(self, text: str) -> NormalizeResult | None:
        best_name = ""
        best_score = 0.0
        for known in self._known:
            if _confusable(text, known):
                continue
            score = SequenceMatcher(None, text, known).ratio()
            if text in known.split() or known in text.split():
                score = max(score, 0.93)
            if score > best_score:
                best_score = score
                best_name = known
        if best_score >= _FUZZY_MIN and best_name:
            return NormalizeResult(text, text, best_name, round(best_score, 3), "fuzzy")
        return None
