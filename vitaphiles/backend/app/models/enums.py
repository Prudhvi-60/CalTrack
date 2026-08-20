from enum import StrEnum


class ItemKind(StrEnum):
    BOOK = "BOOK"
    MOVIE = "MOVIE"


class ReadingStatus(StrEnum):
    WANT_TO_READ = "WANT_TO_READ"
    CURRENTLY_READING = "CURRENTLY_READING"
    READ = "READ"
    ABANDONED = "ABANDONED"


class WatchStatus(StrEnum):
    WATCHLIST = "WATCHLIST"
    WATCHED = "WATCHED"


class ListPrivacy(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    FOLLOWERS_ONLY = "FOLLOWERS_ONLY"


class CreditRole(StrEnum):
    DIRECTOR = "DIRECTOR"
    CAST = "CAST"


class ActivityVerb(StrEnum):
    BOOK_ADDED = "BOOK_ADDED"
    BOOK_STARTED = "BOOK_STARTED"
    BOOK_FINISHED = "BOOK_FINISHED"
    BOOK_RATED = "BOOK_RATED"
    BOOK_REVIEWED = "BOOK_REVIEWED"
    MOVIE_WATCHED = "MOVIE_WATCHED"
    MOVIE_RATED = "MOVIE_RATED"
    MOVIE_REVIEWED = "MOVIE_REVIEWED"
    LIST_CREATED = "LIST_CREATED"
    USER_FOLLOWED = "USER_FOLLOWED"


class GenreKind(StrEnum):
    BOOK = "BOOK"
    MOVIE = "MOVIE"
    BOTH = "BOTH"
