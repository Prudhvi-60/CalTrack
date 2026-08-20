"""MovieMetadataService — TMDB lives behind this interface (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NormalizedMovie:
    external_source: str
    external_id: str
    title: str
    original_title: str | None
    overview: str | None
    poster_url: str | None
    backdrop_url: str | None
    release_date: str | None
    runtime: int | None
    language: str | None
    country: str | None
    genres: list[str]
    directors: list[str]
    cast: list[str]
    production_companies: list[str]


class MovieMetadataService:
    """Replaceable provider. Phase 1 does not call the network."""

    async def search(self, query: str, *, page: int = 1) -> list[NormalizedMovie]:
        raise NotImplementedError("Phase 4: TMDB")

    async def get_by_external_id(self, source: str, external_id: str) -> NormalizedMovie | None:
        raise NotImplementedError("Phase 4: TMDB")
