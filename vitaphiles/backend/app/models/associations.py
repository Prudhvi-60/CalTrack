from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BookAuthor(Base):
    __tablename__ = "book_authors"
    __table_args__ = (UniqueConstraint("book_id", "author_id", name="uq_book_authors"),)

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    book: Mapped["Book"] = relationship("Book", back_populates="authors")
    author: Mapped["Author"] = relationship("Author")


class BookGenre(Base):
    __tablename__ = "book_genres"
    __table_args__ = (UniqueConstraint("book_id", "genre_id", name="uq_book_genres"),)

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)


class MovieGenre(Base):
    __tablename__ = "movie_genres"
    __table_args__ = (UniqueConstraint("movie_id", "genre_id", name="uq_movie_genres"),)

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)


class MovieCredit(Base):
    __tablename__ = "movie_credits"
    __table_args__ = (UniqueConstraint("movie_id", "person_id", "role", name="uq_movie_credits"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    billing_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    movie: Mapped["Movie"] = relationship("Movie", back_populates="credits")
    person: Mapped["Person"] = relationship("Person")
