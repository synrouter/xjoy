"""
Xjoy Bible Data Access Layer

Provides clean, typed access to the KJV SQLite database.
Used by all Xjoy components that need scripture data.

Usage:
    from xjoy.bible import Bible

    bible = Bible("data/kjv.db")

    # Lookup by reference
    verse = bible.verse("John 3:16")
    print(verse.text)  # "For God so loved the world..."

    # Get verses in a chapter
    chapter = bible.chapter("Psalms", 23)

    # Search
    results = bible.search("blessed are the poor in spirit")

    # Cross-references
    refs = bible.cross_refs("John 3:16")
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Optional


# ── Data Types ───────────────────────────────────────────────────────────────

@dataclass
class Verse:
    """A single verse with full metadata."""
    id: int
    book_id: int
    book_name: str
    chapter: int
    verse: int
    text: str

    @property
    def reference(self) -> str:
        return f"{self.book_name} {self.chapter}:{self.verse}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "book_name": self.book_name,
            "chapter": self.chapter,
            "verse": self.verse,
            "text": self.text,
            "reference": self.reference,
        }


@dataclass
class Book:
    """Book metadata."""
    id: int
    name: str
    sort_order: int
    testament: str  # 'OT' or 'NT'
    chapters: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sort_order": self.sort_order,
            "testament": self.testament,
            "chapters": self.chapters,
        }


@dataclass
class CrossReference:
    """A cross-reference from one verse to another."""
    id: int
    source_book: str
    source_chapter: int
    source_verse: int
    target_book: str
    target_chapter: int
    target_verse: int
    target_end_verse: Optional[int] = None

    @property
    def target_reference(self) -> str:
        if self.target_end_verse:
            return f"{self.target_book} {self.target_chapter}:{self.target_verse}-{self.target_end_verse}"
        return f"{self.target_book} {self.target_chapter}:{self.target_verse}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_book": self.source_book,
            "source_chapter": self.source_chapter,
            "source_verse": self.source_verse,
            "target_book": self.target_book,
            "target_chapter": self.target_chapter,
            "target_verse": self.target_verse,
            "target_end_verse": self.target_end_verse,
            "target_reference": self.target_reference,
        }


@dataclass
class SearchResult:
    """A verse search result with relevance snippet."""
    verse: Verse
    snippet: str
    rank: float

    def to_dict(self) -> dict:
        return {
            "verse": self.verse.to_dict(),
            "snippet": self.snippet,
            "rank": self.rank,
        }


# ── Reference Parsing ────────────────────────────────────────────────────────

# Canonical book names and their common abbreviations
BOOK_NAMES = {
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "1 samuel", "2 samuel",
    "1 kings", "2 kings", "1 chronicles", "2 chronicles",
    "ezra", "nehemiah", "esther", "job", "psalms", "proverbs",
    "ecclesiastes", "song of solomon", "isaiah", "jeremiah",
    "lamentations", "ezekiel", "daniel", "hosea", "joel", "amos",
    "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah",
    "haggai", "zechariah", "malachi",
    "matthew", "mark", "luke", "john", "acts", "romans",
    "1 corinthians", "2 corinthians", "galatians", "ephesians",
    "philippians", "colossians", "1 thessalonians", "2 thessalonians",
    "1 timothy", "2 timothy", "titus", "philemon", "hebrews",
    "james", "1 peter", "2 peter", "1 john", "2 john", "3 john",
    "jude", "revelation",
}

# Abbreviation → canonical name mapping
ABBREV_MAP = {
    # OT
    "gen": "Genesis", "ge": "Genesis", "gn": "Genesis",
    "exo": "Exodus", "ex": "Exodus", "exod": "Exodus",
    "lev": "Leviticus", "le": "Leviticus",
    "num": "Numbers", "nu": "Numbers", "nm": "Numbers",
    "deu": "Deuteronomy", "de": "Deuteronomy", "dt": "Deuteronomy",
    "josh": "Joshua", "jos": "Joshua",
    "judg": "Judges", "jdg": "Judges", "jg": "Judges",
    "ruth": "Ruth", "ru": "Ruth", "rut": "Ruth",
    "1sam": "1 Samuel", "1sa": "1 Samuel", "1sm": "1 Samuel",
    "2sam": "2 Samuel", "2sa": "2 Samuel", "2sm": "2 Samuel",
    "1kgs": "1 Kings", "1kg": "1 Kings", "1ki": "1 Kings",
    "2kgs": "2 Kings", "2kg": "2 Kings", "2ki": "2 Kings",
    "1chr": "1 Chronicles", "1ch": "1 Chronicles",
    "2chr": "2 Chronicles", "2ch": "2 Chronicles",
    "ezra": "Ezra", "ezr": "Ezra",
    "neh": "Nehemiah", "ne": "Nehemiah",
    "esth": "Esther", "es": "Esther", "est": "Esther",
    "job": "Job", "jb": "Job",
    "psa": "Psalms", "ps": "Psalms", "psalm": "Psalms",
    "prov": "Proverbs", "pro": "Proverbs", "pr": "Proverbs",
    "ecc": "Ecclesiastes", "eccles": "Ecclesiastes", "ec": "Ecclesiastes",
    "song": "Song of Solomon", "sos": "Song of Solomon",
    "isa": "Isaiah", "is": "Isaiah",
    "jer": "Jeremiah", "je": "Jeremiah",
    "lam": "Lamentations", "la": "Lamentations",
    "eze": "Ezekiel", "ezek": "Ezekiel", "ez": "Ezekiel",
    "dan": "Daniel", "da": "Daniel",
    "hos": "Hosea", "ho": "Hosea",
    "joel": "Joel", "joe": "Joel", "jl": "Joel",
    "amos": "Amos", "am": "Amos",
    "obad": "Obadiah", "oba": "Obadiah", "ob": "Obadiah",
    "jonah": "Jonah", "jon": "Jonah", "jh": "Jonah",
    "mic": "Micah", "mc": "Micah",
    "nah": "Nahum", "na": "Nahum",
    "hab": "Habakkuk", "hb": "Habakkuk",
    "zeph": "Zephaniah", "zep": "Zephaniah",
    "hag": "Haggai", "hg": "Haggai",
    "zec": "Zechariah", "zech": "Zechariah", "zc": "Zechariah",
    "mal": "Malachi", "ml": "Malachi",
    # NT
    "matt": "Matthew", "mt": "Matthew",
    "mark": "Mark", "mr": "Mark", "mk": "Mark",
    "luke": "Luke", "lu": "Luke", "lk": "Luke",
    "john": "John", "joh": "John", "jn": "John",
    "acts": "Acts", "ac": "Acts",
    "rom": "Romans", "ro": "Romans",
    "1cor": "1 Corinthians", "1co": "1 Corinthians",
    "2cor": "2 Corinthians", "2co": "2 Corinthians",
    "gal": "Galatians", "ga": "Galatians",
    "eph": "Ephesians", "ep": "Ephesians",
    "phil": "Philippians", "php": "Philippians", "ph": "Philippians",
    "col": "Colossians", "co": "Colossians",
    "1thess": "1 Thessalonians", "1th": "1 Thessalonians",
    "2thess": "2 Thessalonians", "2th": "2 Thessalonians",
    "1tim": "1 Timothy", "1ti": "1 Timothy",
    "2tim": "2 Timothy", "2ti": "2 Timothy",
    "titus": "Titus", "tit": "Titus",
    "philem": "Philemon", "phm": "Philemon",
    "heb": "Hebrews", "he": "Hebrews",
    "jas": "James", "jam": "James", "jm": "James",
    "1pet": "1 Peter", "1pe": "1 Peter", "1pt": "1 Peter",
    "2pet": "2 Peter", "2pe": "2 Peter", "2pt": "2 Peter",
    "1john": "1 John", "1jo": "1 John", "1jn": "1 John",
    "2john": "2 John", "2jo": "2 John", "2jn": "2 John",
    "3john": "3 John", "3jo": "3 John", "3jn": "3 John",
    "jude": "Jude", "jud": "Jude",
    "rev": "Revelation", "re": "Revelation", "rv": "Revelation",
    # Canonical lowercase names (so full names also resolve)
    "genesis": "Genesis", "exodus": "Exodus", "leviticus": "Leviticus",
    "numbers": "Numbers", "deuteronomy": "Deuteronomy",
    "joshua": "Joshua", "judges": "Judges", "ruth": "Ruth",
    "1 samuel": "1 Samuel", "2 samuel": "2 Samuel",
    "1 kings": "1 Kings", "2 kings": "2 Kings",
    "1 chronicles": "1 Chronicles", "2 chronicles": "2 Chronicles",
    "ezra": "Ezra", "nehemiah": "Nehemiah", "esther": "Esther",
    "job": "Job", "psalms": "Psalms", "proverbs": "Proverbs",
    "ecclesiastes": "Ecclesiastes", "song of solomon": "Song of Solomon",
    "isaiah": "Isaiah", "jeremiah": "Jeremiah", "lamentations": "Lamentations",
    "ezekiel": "Ezekiel", "daniel": "Daniel",
    "hosea": "Hosea", "joel": "Joel", "amos": "Amos",
    "obadiah": "Obadiah", "jonah": "Jonah", "micah": "Micah",
    "nahum": "Nahum", "habakkuk": "Habakkuk", "zephaniah": "Zephaniah",
    "haggai": "Haggai", "zechariah": "Zechariah", "malachi": "Malachi",
    "matthew": "Matthew", "mark": "Mark", "luke": "Luke",
    "john": "John", "acts": "Acts", "romans": "Romans",
    "1 corinthians": "1 Corinthians", "2 corinthians": "2 Corinthians",
    "galatians": "Galatians", "ephesians": "Ephesians",
    "philippians": "Philippians", "colossians": "Colossians",
    "1 thessalonians": "1 Thessalonians", "2 thessalonians": "2 Thessalonians",
    "1 timothy": "1 Timothy", "2 timothy": "2 Timothy",
    "titus": "Titus", "philemon": "Philemon", "hebrews": "Hebrews",
    "james": "James",
    "1 peter": "1 Peter", "2 peter": "2 Peter",
    "1 john": "1 John", "2 john": "2 John", "3 john": "3 John",
    "jude": "Jude", "revelation": "Revelation",
}

# Regex for parsing verse references like "John 3:16" or "1 Kings 2:3-5"
REFERENCE_PATTERN = re.compile(
    r"^\s*"
    r"(\d*\s*[A-Za-z]+(?:\s+(?:of\s+)?[A-Za-z]+)*)"  # Book name (1+ words, handles "Song of Solomon")
    r"\s+"
    r"(\d+)"                                    # Chapter
    r"\s*:\s*"
    r"(\d+)"                                    # Verse
    r"(?:\s*-\s*(\d+))?"                        # Optional end verse
    r"\s*$",
    re.IGNORECASE
)


def resolve_book_name(name: str) -> str:
    """Resolve a book name or abbreviation to the canonical name."""
    lower = name.strip().lower().rstrip(".")
    if lower in ABBREV_MAP:
        return ABBREV_MAP[lower]
    # Try without spaces (e.g., "1 cor" → "1cor")
    no_space = lower.replace(" ", "")
    if no_space in ABBREV_MAP:
        return ABBREV_MAP[no_space]
    # Try stripped of dots and spaces
    cleaned = lower.replace(".", "").replace(" ", "").strip()
    if cleaned in ABBREV_MAP:
        return ABBREV_MAP[cleaned]
    raise ValueError(f"Unknown book: '{name}'")


def parse_reference(ref: str) -> tuple[str, int, int, Optional[int]]:
    """
    Parse a Bible reference string into (book_name, chapter, verse, end_verse).

    Examples:
        "John 3:16" → ("John", 3, 16, None)
        "1 Kings 2:3-5" → ("1 Kings", 2, 3, 5)
        "Gen 1:1" → ("Genesis", 1, 1, None)
    """
    match = REFERENCE_PATTERN.match(ref.strip())
    if not match:
        raise ValueError(f"Invalid reference format: '{ref}'. "
                         f"Expected format: 'Book Chapter:Verse' or 'Book Chapter:Verse-EndVerse'")

    book_raw = match.group(1).strip()
    book_name = resolve_book_name(book_raw)
    chapter = int(match.group(2))
    verse = int(match.group(3))
    end_verse = int(match.group(4)) if match.group(4) else None

    return book_name, chapter, verse, end_verse


# ── Bible Data Access ────────────────────────────────────────────────────────

class Bible:
    """
    Data access layer for the KJV Bible database.

    Thread-safe for reads. All methods return typed dataclass objects.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        """Create a new read-only connection. Thread-safe."""
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        return conn

    @lru_cache(maxsize=128)
    def _get_book_id(self, name: str) -> int:
        """Look up book ID by canonical name (cached)."""
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT id FROM books WHERE name = ?", (name,)
        ).fetchone()
        conn.close()
        if not row:
            raise ValueError(f"Book not found: '{name}'")
        return row[0]

    # ── Book Operations ──────────────────────────────────────────────────

    def books(self) -> list[Book]:
        """List all 66 books in canonical order."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, sort_order, testament, chapters "
                "FROM books ORDER BY sort_order"
            ).fetchall()
            return [Book(**dict(r)) for r in rows]
        finally:
            conn.close()

    def book(self, name: str) -> Book:
        """Get a single book by name or abbreviation."""
        canonical = resolve_book_name(name)
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id, name, sort_order, testament, chapters "
                "FROM books WHERE name = ?",
                (canonical,)
            ).fetchone()
            if not row:
                raise ValueError(f"Book not found: '{canonical}'")
            return Book(**dict(row))
        finally:
            conn.close()

    # ── Verse Lookup ─────────────────────────────────────────────────────

    def verse(self, reference: str) -> Verse:
        """
        Look up a single verse by reference string.

        Examples:
            bible.verse("John 3:16")
            bible.verse("Gen 1:1")
            bible.verse("1 Kings 2:3")
        """
        book_name, chapter, verse_num, _ = parse_reference(reference)
        return self._verse_by_parts(book_name, chapter, verse_num)

    def _verse_by_parts(self, book_name: str, chapter: int, verse_num: int) -> Verse:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT v.id, v.book_id, b.name AS book_name, "
                "v.chapter, v.verse, v.text "
                "FROM verses v JOIN books b ON v.book_id = b.id "
                "WHERE b.name = ? AND v.chapter = ? AND v.verse = ?",
                (book_name, chapter, verse_num)
            ).fetchone()
            if not row:
                raise ValueError(
                    f"Verse not found: {book_name} {chapter}:{verse_num}"
                )
            return Verse(**dict(row))
        finally:
            conn.close()

    def verses(self, *references: str) -> list[Verse]:
        """Look up multiple verses by reference strings."""
        return [self.verse(ref) for ref in references]

    # ── Chapter & Range ──────────────────────────────────────────────────

    def chapter(self, book: str, chapter: int) -> list[Verse]:
        """
        Get all verses in a chapter, in order.

        bible.chapter("Psalms", 23)
        """
        book_name = resolve_book_name(book)
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT v.id, v.book_id, b.name AS book_name, "
                "v.chapter, v.verse, v.text "
                "FROM verses v JOIN books b ON v.book_id = b.id "
                "WHERE b.name = ? AND v.chapter = ? "
                "ORDER BY v.verse",
                (book_name, chapter)
            ).fetchall()
            return [Verse(**dict(r)) for r in rows]
        finally:
            conn.close()

    def range(self, start_ref: str, end_ref: str) -> list[Verse]:
        """
        Get all verses in a range, inclusive.

        bible.range("John 3:16", "John 3:18")
        """
        start_book, start_ch, start_vs, _ = parse_reference(start_ref)
        end_book, end_ch, end_vs, _ = parse_reference(end_ref)

        if start_book != end_book:
            raise ValueError(
                f"Cross-book ranges not supported: {start_book} → {end_book}"
            )

        conn = self._connect()
        try:
            if start_ch == end_ch:
                # Same chapter: simple verse range
                rows = conn.execute(
                    "SELECT v.id, v.book_id, b.name AS book_name, "
                    "v.chapter, v.verse, v.text "
                    "FROM verses v JOIN books b ON v.book_id = b.id "
                    "WHERE b.name = ? AND v.chapter = ? "
                    "AND v.verse >= ? AND v.verse <= ? "
                    "ORDER BY v.verse",
                    (start_book, start_ch, start_vs, end_vs)
                ).fetchall()
            else:
                # Multi-chapter range
                rows = conn.execute(
                    "SELECT v.id, v.book_id, b.name AS book_name, "
                    "v.chapter, v.verse, v.text "
                    "FROM verses v JOIN books b ON v.book_id = b.id "
                    "WHERE b.name = ? "
                    "AND ((v.chapter = ? AND v.verse >= ?) "
                    "  OR (v.chapter > ? AND v.chapter < ?) "
                    "  OR (v.chapter = ? AND v.verse <= ?)) "
                    "ORDER BY v.chapter, v.verse",
                    (start_book,
                     start_ch, start_vs,
                     start_ch, end_ch,
                     end_ch, end_vs)
                ).fetchall()

            return [Verse(**dict(r)) for r in rows]
        finally:
            conn.close()

    # ── Search ───────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        testament: Optional[str] = None,
        book: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Full-text search across the KJV text.

        Args:
            query: Search terms (supports FTS5 syntax)
            limit: Maximum results to return
            testament: Filter to 'OT' or 'NT'
            book: Filter to a specific book
        """
        conn = self._connect()
        try:
            safe_query = self._escape_fts(query)

            # Build filters on the outer join
            extra_joins = ""
            extra_conditions = ""
            extra_params: list = []

            if testament:
                extra_conditions += " AND b.testament = ?"
                extra_params.append(testament.upper())

            if book:
                book_name = resolve_book_name(book)
                extra_conditions += " AND b.name = ?"
                extra_params.append(book_name)

            sql = (
                "SELECT v.id, v.book_id, b.name AS book_name, "
                "v.chapter, v.verse, v.text, "
                "s.snippet, s.rank "
                "FROM ("
                "  SELECT rowid, "
                "  snippet(verses_fts, 0, '<mark>', '</mark>', '...', 40) AS snippet, "
                "  rank "
                "  FROM verses_fts WHERE verses_fts MATCH ? "
                "  ORDER BY rank LIMIT ?"
                ") s "
                "JOIN verses v ON s.rowid = v.id "
                "JOIN books b ON v.book_id = b.id "
                f"{extra_joins} "
                "WHERE 1=1 "
                f"{extra_conditions} "
                "ORDER BY s.rank"
            )

            all_params = [safe_query, limit] + extra_params

            rows = conn.execute(sql, all_params).fetchall()
            results = []
            for r in rows:
                verse = Verse(
                    id=r[0],
                    book_id=r[1],
                    book_name=r[2],
                    chapter=r[3],
                    verse=r[4],
                    text=r[5],
                )
                results.append(SearchResult(
                    verse=verse,
                    snippet=r[6] or verse.text[:60],
                    rank=float(r[7]) if r[7] else 999.0,
                ))

            return results
        finally:
            conn.close()

    def keyword_search(self, keyword: str, *, limit: int = 50) -> list[Verse]:
        """
        Simple keyword search using LIKE (fallback when FTS is too strict).
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT v.id, v.book_id, b.name AS book_name, "
                "v.chapter, v.verse, v.text "
                "FROM verses v JOIN books b ON v.book_id = b.id "
                "WHERE v.text LIKE ? "
                "ORDER BY b.sort_order, v.chapter, v.verse "
                "LIMIT ?",
                (f"%{keyword}%", limit)
            ).fetchall()
            return [Verse(**dict(r)) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def _escape_fts(query: str) -> str:
        """Minimal FTS5 escaping for user input."""
        # Wrap each word so it's treated as a term. FTS5 doesn't need
        # heavy escaping for simple search — just strip special chars.
        escaped = re.sub(r'[^\w\s"*]', '', query)
        if not escaped.strip():
            return '""'
        # Quote the whole phrase for exact-ish matching
        if " " in escaped.strip() and '"' not in escaped:
            return f'"{escaped.strip()}"'
        return escaped.strip()

    # ── Cross-References ─────────────────────────────────────────────────

    def cross_refs(
        self,
        reference: str,
        *,
        limit: int = 50,
    ) -> list[CrossReference]:
        """
        Get cross-references for a given verse.

        Returns both directions: where this verse is referenced, and what it references.
        """
        book_name, chapter, verse_num, _ = parse_reference(reference)
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT cr.id, "
                "sb.name AS source_book, cr.source_chapter, cr.source_verse, "
                "tb.name AS target_book, cr.target_chapter, cr.target_verse, "
                "cr.target_end_verse "
                "FROM cross_references cr "
                "JOIN books sb ON cr.source_book_id = sb.id "
                "JOIN books tb ON cr.target_book_id = tb.id "
                "WHERE sb.name = ? AND cr.source_chapter = ? AND cr.source_verse = ? "
                "LIMIT ?",
                (book_name, chapter, verse_num, limit)
            ).fetchall()
            return [CrossReference(**dict(r)) for r in rows]
        finally:
            conn.close()

    def cross_refs_to(
        self,
        reference: str,
        *,
        limit: int = 50,
    ) -> list[CrossReference]:
        """
        Get verses that reference the given verse (incoming cross-references).
        """
        book_name, chapter, verse_num, _ = parse_reference(reference)
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT cr.id, "
                "sb.name AS source_book, cr.source_chapter, cr.source_verse, "
                "tb.name AS target_book, cr.target_chapter, cr.target_verse, "
                "cr.target_end_verse "
                "FROM cross_references cr "
                "JOIN books sb ON cr.source_book_id = sb.id "
                "JOIN books tb ON cr.target_book_id = tb.id "
                "WHERE tb.name = ? AND cr.target_chapter = ? AND cr.target_verse = ? "
                "LIMIT ?",
                (book_name, chapter, verse_num, limit)
            ).fetchall()
            return [CrossReference(**dict(r)) for r in rows]
        finally:
            conn.close()

    # ── Statistics ───────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Get database statistics."""
        conn = self._connect()
        try:
            book_count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
            verse_count = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
            crossref_count = conn.execute(
                "SELECT COUNT(*) FROM cross_references"
            ).fetchone()[0]
            ot_verses = conn.execute(
                "SELECT COUNT(*) FROM verses v JOIN books b ON v.book_id = b.id "
                "WHERE b.testament = 'OT'"
            ).fetchone()[0]
            nt_verses = conn.execute(
                "SELECT COUNT(*) FROM verses v JOIN books b ON v.book_id = b.id "
                "WHERE b.testament = 'NT'"
            ).fetchone()[0]
            return {
                "books": book_count,
                "verses": verse_count,
                "ot_verses": ot_verses,
                "nt_verses": nt_verses,
                "cross_references": crossref_count,
            }
        finally:
            conn.close()

    def books_by_testament(self) -> dict[str, list[Book]]:
        """Get books grouped by testament."""
        books = self.books()
        ot = [b for b in books if b.testament == "OT"]
        nt = [b for b in books if b.testament == "NT"]
        return {"OT": ot, "NT": nt}


# ── Convenience functions (for quick scripting) ──────────────────────────────

_DEFAULT_BIBLE: Optional[Bible] = None


def get_bible(db_path: str | None = None) -> Bible:
    """Get the default Bible instance (singleton per path)."""
    global _DEFAULT_BIBLE
    if db_path is None:
        db_path = str(
            Path(__file__).resolve().parent.parent / "data" / "kjv.db"
        )
    if _DEFAULT_BIBLE is None or _DEFAULT_BIBLE.db_path != str(db_path):
        _DEFAULT_BIBLE = Bible(str(db_path))
    return _DEFAULT_BIBLE
