"""BookMetadataService — Google Books / Open Library live behind this interface (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NormalizedBook:
    external_source: str
    external_id: str
    title: str
    subtitle: str | None
    description: str | None
    isbn: str | None
    isbn13: str | None
    cover_url: str | None
    publication_date: str | None
    publisher: str | None
    page_count: int | None
    language: str | None
    authors: list[str]
    genres: list[str]


class BookMetadataService:
    """Replaceable provider. Phase 1 does not call the network."""

    async def search(self, query: str, *, page: int = 1) -> list[NormalizedBook]:
        raise NotImplementedError("Phase 3: Google Books / Open Library")

    async def get_by_external_id(self, source: str, external_id: str) -> NormalizedBook | None:
        raise NotImplementedError("Phase 3: Google Books / Open Library")
