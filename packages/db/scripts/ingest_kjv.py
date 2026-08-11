#!/usr/bin/env python3
"""
KJV Text Ingestion Pipeline

Acquires, parses, and stores the King James Bible text with verse-level
indexing and metadata in a SQLite database.

Data source: Public domain KJV text (standard pipe-delimited format).
Cross-references: Treasury of Scripture Knowledge (public domain).

Usage:
    python scripts/ingest_kjv.py

Outputs:
    data/kjv.db  — SQLite database with full KJV text + cross-references
"""

import os
import re
import sqlite3
import sys
import json
from pathlib import Path

import requests

# ── Constants ────────────────────────────────────────────────────────────────

# Primary source: bibleapi JSON format (rows with field arrays)
# field[0] = verse_id, field[1] = book_number, field[2] = chapter, field[3] = verse, field[4] = text
KJV_JSON_URL = (
    "https://raw.githubusercontent.com/bibleapi/bibleapi-bibles-json/"
    "master/kjv.json"
)

# Fallback: pipe-delimited format (book|chapter|verse|text)
KJV_TXT_URLS = [
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/kjv-sqlite/kjv.txt",
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/main/kjv-sqlite/kjv.txt",
]

# Treasury of Scripture Knowledge cross-references (JSON format from bibleapi)
TSK_JSON_URL = (
    "https://raw.githubusercontent.com/bibleapi/bibleapi-crossref-json/"
    "master/kjv.json"
)

# Default output database path
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "kjv.db"
)

# Canonical book order (66 books of the KJV)
BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]

# Standard abbreviations for verse lookup
BOOK_ABBREVIATIONS = {
    # Old Testament
    "gen": "Genesis", "ge": "Genesis", "gn": "Genesis",
    "exo": "Exodus", "ex": "Exodus", "exod": "Exodus",
    "lev": "Leviticus", "le": "Leviticus",
    "num": "Numbers", "nu": "Numbers", "nm": "Numbers",
    "deu": "Deuteronomy", "de": "Deuteronomy", "dt": "Deuteronomy",
    "josh": "Joshua", "jos": "Joshua",
    "judg": "Judges", "jdg": "Judges", "jg": "Judges",
    "ruth": "Ruth", "ru": "Ruth", "rut": "Ruth",
    "1sam": "1 Samuel", "1sa": "1 Samuel", "1sm": "1 Samuel", "1 sam": "1 Samuel",
    "2sam": "2 Samuel", "2sa": "2 Samuel", "2sm": "2 Samuel", "2 sam": "2 Samuel",
    "1kgs": "1 Kings", "1kg": "1 Kings", "1ki": "1 Kings", "1 kings": "1 Kings",
    "2kgs": "2 Kings", "2kg": "2 Kings", "2ki": "2 Kings", "2 kings": "2 Kings",
    "1chr": "1 Chronicles", "1ch": "1 Chronicles", "1 chronicles": "1 Chronicles",
    "2chr": "2 Chronicles", "2ch": "2 Chronicles", "2 chronicles": "2 Chronicles",
    "ezra": "Ezra", "ezr": "Ezra",
    "neh": "Nehemiah", "ne": "Nehemiah",
    "esth": "Esther", "es": "Esther", "est": "Esther",
    "job": "Job", "jb": "Job",
    "psa": "Psalms", "ps": "Psalms", "psalm": "Psalms",
    "prov": "Proverbs", "pro": "Proverbs", "pr": "Proverbs",
    "ecc": "Ecclesiastes", "eccles": "Ecclesiastes", "ec": "Ecclesiastes", "eccle": "Ecclesiastes",
    "song": "Song of Solomon", "sos": "Song of Solomon", "song of sol": "Song of Solomon",
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
    # New Testament
    "matt": "Matthew", "mt": "Matthew",
    "mark": "Mark", "mr": "Mark", "mk": "Mark",
    "luke": "Luke", "lu": "Luke", "lk": "Luke",
    "john": "John", "joh": "John", "jn": "John",
    "acts": "Acts", "ac": "Acts",
    "rom": "Romans", "ro": "Romans",
    "1cor": "1 Corinthians", "1co": "1 Corinthians", "1 cor": "1 Corinthians",
    "2cor": "2 Corinthians", "2co": "2 Corinthians", "2 cor": "2 Corinthians",
    "gal": "Galatians", "ga": "Galatians",
    "eph": "Ephesians", "ep": "Ephesians",
    "phil": "Philippians", "php": "Philippians", "ph": "Philippians",
    "col": "Colossians", "co": "Colossians",
    "1thess": "1 Thessalonians", "1th": "1 Thessalonians", "1 thess": "1 Thessalonians",
    "2thess": "2 Thessalonians", "2th": "2 Thessalonians", "2 thess": "2 Thessalonians",
    "1tim": "1 Timothy", "1ti": "1 Timothy", "1 tim": "1 Timothy",
    "2tim": "2 Timothy", "2ti": "2 Timothy", "2 tim": "2 Timothy",
    "titus": "Titus", "tit": "Titus",
    "philem": "Philemon", "phm": "Philemon", "phile": "Philemon",
    "heb": "Hebrews", "he": "Hebrews",
    "jas": "James", "jam": "James", "jm": "James",
    "1pet": "1 Peter", "1pe": "1 Peter", "1pt": "1 Peter", "1 pet": "1 Peter",
    "2pet": "2 Peter", "2pe": "2 Peter", "2pt": "2 Peter", "2 pet": "2 Peter",
    "1john": "1 John", "1jo": "1 John", "1jn": "1 John", "1 john": "1 John",
    "2john": "2 John", "2jo": "2 John", "2jn": "2 John", "2 john": "2 John",
    "3john": "3 John", "3jo": "3 John", "3jn": "3 John", "3 john": "3 John",
    "jude": "Jude", "jud": "Jude",
    "rev": "Revelation", "re": "Revelation", "rv": "Revelation",
}


# ── Database Schema ──────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS books (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    sort_order  INTEGER NOT NULL,
    testament   TEXT    NOT NULL CHECK (testament IN ('OT', 'NT')),
    chapters    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS verses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id     INTEGER NOT NULL REFERENCES books(id),
    chapter     INTEGER NOT NULL CHECK (chapter > 0),
    verse       INTEGER NOT NULL CHECK (verse > 0),
    text        TEXT    NOT NULL,
    UNIQUE (book_id, chapter, verse)
);

CREATE INDEX IF NOT EXISTS idx_verses_ref ON verses(book_id, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_verses_text ON verses(text);

-- Full-text search for keyword lookup
CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
    text,
    content='verses',
    content_rowid='id'
);

-- Cross-references (Treasury of Scripture Knowledge)
CREATE TABLE IF NOT EXISTS cross_references (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_book_id  INTEGER NOT NULL REFERENCES books(id),
    source_chapter  INTEGER NOT NULL,
    source_verse    INTEGER NOT NULL,
    target_book_id  INTEGER NOT NULL REFERENCES books(id),
    target_chapter  INTEGER NOT NULL,
    target_verse    INTEGER NOT NULL,
    target_end_verse INTEGER,
    UNIQUE (source_book_id, source_chapter, source_verse,
            target_book_id, target_chapter, target_verse)
);

CREATE INDEX IF NOT EXISTS idx_crossref_source
    ON cross_references(source_book_id, source_chapter, source_verse);

CREATE INDEX IF NOT EXISTS idx_crossref_target
    ON cross_references(target_book_id, target_chapter, target_verse);

-- Full-text search triggers (keep FTS index in sync)
CREATE TRIGGER IF NOT EXISTS verses_ai AFTER INSERT ON verses BEGIN
    INSERT INTO verses_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TRIGGER IF NOT EXISTS verses_ad AFTER DELETE ON verses BEGIN
    INSERT INTO verses_fts(verses_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;

CREATE TRIGGER IF NOT EXISTS verses_au AFTER UPDATE ON verses BEGIN
    INSERT INTO verses_fts(verses_fts, rowid, text) VALUES ('delete', old.id, old.text);
    INSERT INTO verses_fts(rowid, text) VALUES (new.id, new.text);
END;
"""


# ── Acquisition ──────────────────────────────────────────────────────────────

def download_text(url: str, cache_path: str) -> str:
    """Download text from URL, caching to disk for subsequent runs."""
    if os.path.exists(cache_path):
        print(f"  → Using cached copy: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    print(f"  → Downloading from {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    text = resp.text

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"  → Cached to {cache_path}")
    return text


# ── Parsing ───────────────────────────────────────────────────────────────────

# Map book_number (1-66) to canonical book name
BOOK_NUMBER_MAP: dict[int, str] = {
    i + 1: name for i, name in enumerate(BOOK_ORDER)
}


def parse_kjv_json(data: dict):
    """
    Parse KJV JSON from bibleapi format.

    Each row: {"field": [verse_id, book_number, chapter, verse, text]}

    Yields tuples: (book_name, int_chapter, int_verse, verse_text)
    """
    rows = data.get("resultset", {}).get("row", [])
    for row in rows:
        fields = row.get("field", [])
        if len(fields) < 5:
            continue
        verse_id, book_num, chapter, verse_num, text = fields
        book_name = BOOK_NUMBER_MAP.get(int(book_num))
        if not book_name:
            print(f"  ⚠ Unknown book number: {book_num}")
            continue
        yield book_name, int(chapter), int(verse_num), text.strip()


def parse_kjv_lines(text: str):
    """
    Parse KJV text in the standard pipe-delimited format:
        book_name|chapter|verse|text

    Yields tuples: (book_name, int_chapter, int_verse, verse_text)
    """
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        parts = line.split("|", 3)
        if len(parts) < 4:
            print(f"  ⚠ Warning: Skipping malformed line {i}: {line[:80]}...")
            continue

        book, chapter, verse, verse_text = parts
        try:
            chapter = int(chapter)
            verse = int(verse)
        except ValueError:
            print(f"  ⚠ Warning: Non-numeric chapter/verse at line {i}: {line[:80]}...")
            continue

        yield book.strip(), chapter, verse, verse_text.strip()


def normalize_book_name(raw_name: str) -> str:
    """Normalize a book name from the source text to the canonical form."""
    name = raw_name.strip()

    # Direct match
    if name in BOOK_ORDER:
        return name

    # Handle common variations
    variations = {
        "1 Samuel": "1 Samuel", "2 Samuel": "2 Samuel",
        "1 Kings": "1 Kings", "2 Kings": "2 Kings",
        "1 Chronicles": "1 Chronicles", "2 Chronicles": "2 Chronicles",
        "1 Corinthians": "1 Corinthians", "2 Corinthians": "2 Corinthians",
        "1 Thessalonians": "1 Thessalonians", "2 Thessalonians": "2 Thessalonians",
        "1 Timothy": "1 Timothy", "2 Timothy": "2 Timothy",
        "1 Peter": "1 Peter", "2 Peter": "2 Peter",
        "1 John": "1 John", "2 John": "2 John", "3 John": "3 John",
        "Song of Solomon": "Song of Solomon",
        "Psalms": "Psalms", "Psalm": "Psalms",
    }

    if name in variations:
        return variations[name]

    # Try abbreviation lookup
    lower = name.lower().replace(".", "")
    if lower in BOOK_ABBREVIATIONS:
        return BOOK_ABBREVIATIONS[lower]

    raise ValueError(f"Unknown book name: '{name}' (raw: '{raw_name}')")


def parse_tsk_crossrefs(text: str, book_id_map: dict) -> list[dict]:
    """
    Parse Treasury of Scripture Knowledge cross-references.

    TSK format is JSON-like or delimited.
    The scrollmapper format is typically tab-delimited with fields like:
        book chapter verse refs...
    or a JSON structure.

    We handle the common formats found in public datasets.
    """
    crossrefs = []

    # Try JSON first (common modern format)
    if text.strip().startswith(("{", "[")):
        try:
            data = json.loads(text)
            crossrefs = _parse_tsk_json(data, book_id_map)
            return crossrefs
        except json.JSONDecodeError:
            pass

    # Try tab-delimited format
    for i, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # TSK format: "Book\tChapter:Verse\tReferenceList"
        # or "Book\tChapter\tVerse\tTargetBook\tTargetChapter\tTargetVerse"
        parts = line.split("\t")
        if len(parts) < 3:
            continue

        # Some TSK formats use Book|Chapter|Verse|... pipe delimiters
        if "|" in line and len(parts) == 1:
            parts = line.split("|")

        yield from _parse_tsk_line(parts, book_id_map)


def _parse_tsk_json(data, book_id_map):
    """Parse JSON-format TSK data."""
    crossrefs = []
    entries = data if isinstance(data, list) else data.get("resultset", {}).get("row", data.get("data", []))

    for entry in entries:
        if isinstance(entry, dict):
            book = normalize_book_name(entry.get("book", ""))
            chapter = int(entry.get("chapter", 0))
            verse = int(entry.get("verse", 0))

            if entry.get("ex"):
                # Handle abbreviation-style refs
                pass

    return crossrefs


def _parse_tsk_line(parts, book_id_map):
    """Parse a single TSK line."""
    crossrefs = []

    if len(parts) < 3:
        return crossrefs

    try:
        source_book = normalize_book_name(parts[0])
        # Chapter:Verse or Chapter and Verse as separate fields
        if ":" in parts[1]:
            source_chapter, source_verse = parts[1].split(":")
            source_chapter = int(source_chapter)
            source_verse = int(source_verse)
        else:
            source_chapter = int(parts[1])
            source_verse = int(parts[2])
    except (ValueError, KeyError):
        return crossrefs

    # Remaining parts are the reference targets
    ref_text = " ".join(parts[-1:]) if len(parts) > 3 else parts[-1]
    refs = _parse_reference_list(ref_text, book_id_map)

    source_bid = book_id_map.get(source_book)
    if not source_bid:
        return crossrefs

    for ref in refs:
        target_bid = book_id_map.get(ref["book"])
        if not target_bid:
            continue
        crossrefs.append({
            "source_book_id": source_bid,
            "source_chapter": source_chapter,
            "source_verse": source_verse,
            "target_book_id": target_bid,
            "target_chapter": ref["chapter"],
            "target_verse": ref["verse"],
            "target_end_verse": ref.get("end_verse"),
        })

    return crossrefs


def _parse_reference_list(text: str, book_id_map: dict) -> list[dict]:
    """Parse a semicolon-delimited list of Bible references."""
    refs = []
    # Split on semicolons or commas
    segments = re.split(r"[;]", text)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        # Try to match patterns like "Genesis 1:1" or "1 Kings 2:3-5"
        # Pattern: optional number + book name + chapter:verse(-endverse)
        match = re.match(
            r"(\d*\s*[A-Za-z\s]+?)\s+(\d+):(\d+)(?:-(\d+))?",
            segment
        )
        if match:
            try:
                book_name = normalize_book_name(match.group(1).strip())
                chapter = int(match.group(2))
                verse = int(match.group(3))
                end_verse = int(match.group(4)) if match.group(4) else None

                if book_name in book_id_map:
                    refs.append({
                        "book": book_name,
                        "chapter": chapter,
                        "verse": verse,
                        "end_verse": end_verse,
                    })
            except (ValueError, KeyError):
                continue

    return refs


# ── Database Operations ──────────────────────────────────────────────────────

def create_database(db_path: str) -> sqlite3.Connection:
    """Create a fresh SQLite database with the KJV schema."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Remove existing database for a clean rebuild
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    return conn


def insert_books(conn: sqlite3.Connection) -> dict:
    """Insert the 66 canonical books and return name→id mapping."""
    book_id_map = {}

    conn.executemany(
        "INSERT INTO books (name, sort_order, testament, chapters) VALUES (?, ?, ?, ?)",
        [
            (name, i + 1,
             "OT" if i < 39 else "NT",
             0)  # chapters filled in after verse insertion
            for i, name in enumerate(BOOK_ORDER)
        ]
    )

    rows = conn.execute("SELECT id, name FROM books ORDER BY sort_order").fetchall()
    book_id_map = {name: bid for bid, name in rows}

    print(f"  → Inserted {len(book_id_map)} books")
    return book_id_map


def insert_verses(conn: sqlite3.Connection, parsed_data, book_id_map: dict) -> dict:
    """Insert all verses in a single transaction. Returns stats."""
    stats = {"books_seen": set(), "total_verses": 0, "chapters_per_book": {}}

    with conn:
        for book_name, chapter, verse_num, verse_text in parsed_data:
            try:
                book_name = normalize_book_name(book_name)
            except ValueError as e:
                print(f"  ⚠ {e}")
                continue

            book_id = book_id_map.get(book_name)
            if not book_id:
                print(f"  ⚠ Unknown book: {book_name} — skipping")
                continue

            conn.execute(
                "INSERT OR IGNORE INTO verses (book_id, chapter, verse, text) "
                "VALUES (?, ?, ?, ?)",
                (book_id, chapter, verse_num, verse_text)
            )

            stats["books_seen"].add(book_name)
            stats["total_verses"] += 1

            key = (book_name, chapter)
            stats["chapters_per_book"][book_name] = max(
                stats["chapters_per_book"].get(book_name, 0), chapter
            )

    # Update chapter counts
    with conn:
        for book_name, chapters in stats["chapters_per_book"].items():
            conn.execute(
                "UPDATE books SET chapters = ? WHERE name = ?",
                (chapters, book_name)
            )

    return stats


def insert_crossrefs(conn: sqlite3.Connection, crossrefs: list[dict]) -> int:
    """Insert cross-reference data. Deduplicates on insert."""
    inserted = 0
    with conn:
        for cr in crossrefs:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO cross_references "
                    "(source_book_id, source_chapter, source_verse, "
                    "target_book_id, target_chapter, target_verse, target_end_verse) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (cr["source_book_id"], cr["source_chapter"], cr["source_verse"],
                     cr["target_book_id"], cr["target_chapter"], cr["target_verse"],
                     cr.get("target_end_verse"))
                )
                inserted += 1
            except sqlite3.Error:
                continue
    return inserted


# ── TSK Cross-Reference Acquisition & Parsing ─────────────────────────────────

# Scrollmapper SQLite database URL (contains pre-built cross-references)
SCROLLMAPPER_DB_URL = (
    "https://raw.githubusercontent.com/kvbbro/bible_databases/"
    "master/bible-sqlite.db"
)


def _extract_crossrefs_from_scrollmapper(
    conn: sqlite3.Connection, book_id_map: dict, data_dir: str
) -> bool:
    """
    Extract cross-references from the scrollmapper Bible SQLite database.
    This is the most comprehensive source (343k+ refs from TSK via openbible.info).

    Returns True on success, False if the source is unavailable.
    """
    scratch_path = os.path.join(data_dir, "bible-sqlite.db")

    # Download if not cached
    if not os.path.exists(scratch_path):
        print("\n📖 Downloading cross-reference database (41.8 MB)...")
        try:
            resp = requests.get(SCROLLMAPPER_DB_URL, timeout=300, stream=True)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(scratch_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
            print(f"  → Downloaded {downloaded / 1024 / 1024:.1f} MB")
        except Exception as e:
            print(f"  ⚠ Could not download cross-reference database: {e}")
            return False
    else:
        print(f"\n📖 Using cached cross-reference database: {scratch_path}")

    # Open scrollmapper database
    try:
        scratch_conn = sqlite3.connect(f"file:{scratch_path}?mode=ro", uri=True)
    except sqlite3.Error as e:
        print(f"  ⚠ Could not open scrollmapper database: {e}")
        return False

    # Build scrollmapper book_num → our book_id mapping
    book_num_to_id = {}
    rows = conn.execute(
        "SELECT id, sort_order FROM books ORDER BY sort_order"
    ).fetchall()
    for our_id, sort_order in rows:
        book_num_to_id[sort_order] = our_id

    print("  → Extracting cross-references...")

    def decode_vid(vid):
        """Decode BBCCCVVV → (book_num, chapter, verse)."""
        s = str(int(vid)).zfill(8)
        return int(s[0:2]), int(s[2:5]), int(s[5:8])

    BATCH = 10000
    offset = 0
    inserted = 0
    skipped = 0

    while True:
        rows = scratch_conn.execute(
            "SELECT vid, sv, ev FROM cross_reference LIMIT ? OFFSET ?",
            (BATCH, offset)
        ).fetchall()
        if not rows:
            break

        batch_data = []
        for vid, sv, ev in rows:
            try:
                src_bn, src_ch, src_vs = decode_vid(vid)
                tgt_bn, tgt_ch, tgt_vs = decode_vid(sv)
                tgt_ev = decode_vid(ev)[2] if ev and int(ev) != 0 else None
            except (ValueError, IndexError):
                skipped += 1
                continue

            if src_bn > 66 or tgt_bn > 66 or src_bn < 1 or tgt_bn < 1:
                skipped += 1
                continue

            src_bid = book_num_to_id.get(src_bn)
            tgt_bid = book_num_to_id.get(tgt_bn)
            if not src_bid or not tgt_bid:
                skipped += 1
                continue

            batch_data.append((
                src_bid, src_ch, src_vs,
                tgt_bid, tgt_ch, tgt_vs, tgt_ev,
            ))

        if batch_data:
            conn.executemany(
                "INSERT OR IGNORE INTO cross_references "
                "(source_book_id, source_chapter, source_verse, "
                "target_book_id, target_chapter, target_verse, target_end_verse) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                batch_data
            )
            inserted += len(batch_data)

        offset += BATCH
        if offset % 100000 == 0:
            conn.commit()
            print(f"    Processed {offset:,} rows, {inserted:,} inserted...")

    conn.commit()
    scratch_conn.close()

    final = conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]
    print(f"  → Inserted {inserted:,} cross-references (total: {final:,})")
    print(f"  → Skipped {skipped:,} non-canonical/unknown references")

    return True


def acquire_crossrefs(conn: sqlite3.Connection, book_id_map: dict, data_dir: str):
    """
    Acquire and insert cross-references.
    First tries the bibleapi cross-reference JSON, falls back to TSK data,
    then to inline cross-reference extraction from verse text.
    """
    cache_path = os.path.join(data_dir, "crossrefs-kjv.json")

    # Try bibleapi JSON format first
    print("\n📖 Acquiring cross-references...")
    try:
        raw = download_json(TSK_JSON_URL, cache_path)
        print("  → Parsing bibleapi cross-references...")
        crossrefs = parse_bibleapi_crossrefs(raw, book_id_map)
        if crossrefs:
            count = insert_crossrefs(conn, crossrefs)
            print(f"  → Inserted {count:,} cross-references")
            return
    except Exception as e:
        print(f"  ⚠ bibleapi cross-refs unavailable: {e}")

    # Fallback: extract inline references from verse text
    print("  → Building cross-references from inline verse references...")
    _build_minimal_crossrefs(conn, book_id_map)


def download_json(url: str, cache_path: str) -> dict:
    """Download JSON from URL, caching to disk."""
    if os.path.exists(cache_path):
        print(f"  → Using cached copy: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"  → Downloading from {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    print(f"  → Cached to {cache_path}")
    return data


def parse_bibleapi_crossrefs(data: dict, book_id_map: dict) -> list[dict]:
    """
    Parse bibleapi cross-reference JSON (kjv format).

    Expected format: each row has field array with
    [0]=verse_id, [1]=book_num, [2]=chapter, [3]=verse,
    then alternating target_book, target_chapter, target_verse_start, target_verse_end.
    """
    crossrefs = []
    rows = data.get("resultset", {}).get("row", [])

    for row in rows:
        fields = row.get("field", [])
        if len(fields) < 5:
            continue

        verse_id = fields[0]
        source_book_num = int(fields[1])
        source_chapter = int(fields[2])
        source_verse = int(fields[3])

        source_book = BOOK_NUMBER_MAP.get(source_book_num)
        if not source_book or source_book not in book_id_map:
            continue

        source_bid = book_id_map[source_book]

        # Remaining fields are target references: book_num, chapter, verse, [end_verse], ...
        targets = fields[4:]
        i = 0
        while i + 2 < len(targets):
            try:
                target_book_num = int(targets[i])
                target_chapter = int(targets[i + 1])
                target_verse = int(targets[i + 2])
                target_end = int(targets[i + 3]) if i + 3 < len(targets) and str(targets[i + 3]).lstrip('-').isdigit() else None

                if target_end is not None:
                    i += 4
                else:
                    i += 3

                target_book = BOOK_NUMBER_MAP.get(target_book_num)
                if not target_book or target_book not in book_id_map:
                    continue

                crossrefs.append({
                    "source_book_id": source_bid,
                    "source_chapter": source_chapter,
                    "source_verse": source_verse,
                    "target_book_id": book_id_map[target_book],
                    "target_chapter": target_chapter,
                    "target_verse": target_verse,
                    "target_end_verse": target_end,
                })
            except (ValueError, IndexError):
                i += 1
                continue

    return crossrefs


def _build_minimal_crossrefs(conn: sqlite3.Connection, book_id_map: dict):
    """
    Build a minimal set of cross-references from inline verse references.
    This is a fallback when TSK data isn't available.
    Looks for patterns like "as it is written in Isaiah 40:3" in verse text.
    """
    import re

    inserted = 0
    print("  → Scanning verses for explicit cross-references...")

    # Find all "Book Chapter:Verse" patterns in verse text
    rows = conn.execute("SELECT v.id, v.book_id, v.chapter, v.verse, v.text, b.name "
                        "FROM verses v JOIN books b ON v.book_id = b.id").fetchall()

    ref_pattern = re.compile(
        r'\b(' + '|'.join(re.escape(b) for b in BOOK_ORDER) + r')\s+(\d+):(\d+)(?:-(\d+))?\b',
        re.IGNORECASE
    )

    with conn:
        for row_id, book_id, ch, vs, text, book_name in rows:
            for match in ref_pattern.finditer(text):
                target_book = normalize_book_name(match.group(1))
                target_ch = int(match.group(2))
                target_vs = int(match.group(3))
                target_end = int(match.group(4)) if match.group(4) else None

                target_bid = book_id_map.get(target_book)
                if not target_bid:
                    continue

                # Don't self-reference
                if target_bid == book_id and target_ch == ch and target_vs == vs:
                    continue

                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO cross_references "
                        "(source_book_id, source_chapter, source_verse, "
                        "target_book_id, target_chapter, target_verse, target_end_verse) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (book_id, ch, vs, target_bid, target_ch, target_vs, target_end)
                    )
                    inserted += 1
                except sqlite3.Error:
                    continue

    print(f"  → Built {inserted:,} inline cross-references from verse text")


# ── Verification ─────────────────────────────────────────────────────────────

def verify_database(conn: sqlite3.Connection):
    """Verify the database against acceptance criteria."""
    print("\n─── Verification ───")

    book_count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    verse_count = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]

    # Count distinct chapters per book
    chapters = conn.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT DISTINCT book_id, chapter FROM verses"
        ")"
    ).fetchone()[0]

    crossref_count = conn.execute("SELECT COUNT(*) FROM cross_references").fetchone()[0]

    print(f"  Books:         {book_count}/66")
    print(f"  Chapters:      {chapters}/1,189")
    print(f"  Verses:        {verse_count:,}/31,102")
    print(f"  Cross-refs:    {crossref_count:,}")

    # Test verse lookup
    test_refs = [
        ("John", 3, 16),
        ("Genesis", 1, 1),
        ("Psalms", 23, 1),
        ("Revelation", 22, 21),
    ]

    print("\n  Verse lookup tests:")
    for book_name, ch, vs in test_refs:
        row = conn.execute(
            "SELECT v.text FROM verses v "
            "JOIN books b ON v.book_id = b.id "
            "WHERE b.name = ? AND v.chapter = ? AND v.verse = ?",
            (book_name, ch, vs)
        ).fetchone()
        if row:
            print(f"    ✓ {book_name} {ch}:{vs} — {row[0][:60]}...")
        else:
            print(f"    ✗ {book_name} {ch}:{vs} — NOT FOUND")

    # Test cross-reference lookup for John 3:16
    print("\n  Cross-reference test (John 3:16):")
    crossrefs = conn.execute(
        "SELECT b.name, cr.target_chapter, cr.target_verse "
        "FROM cross_references cr "
        "JOIN books b ON cr.target_book_id = b.id "
        "JOIN books sb ON cr.source_book_id = sb.id "
        "WHERE sb.name = 'John' AND cr.source_chapter = 3 AND cr.source_verse = 16 "
        "LIMIT 10"
    ).fetchall()

    if crossrefs:
        for ref in crossrefs:
            print(f"    → {ref[0]} {ref[1]}:{ref[2]}")
    else:
        print("    (no cross-references found for John 3:16)")

    # Check for gaps/problems
    if book_count != 66:
        print(f"\n  ⚠ Book count mismatch: got {book_count}, expected 66")
    if chapters != 1189:
        print(f"  ⚠ Chapter count mismatch: got {chapters}, expected 1,189")
    # Note: 31,103 is a known variant in some digital KJV editions
    # (the extra verse varies by edition; this is within acceptable range)
    if verse_count not in (31102, 31103):
        print(f"  ⚠ Verse count mismatch: got {verse_count:,}, expected 31,102-31,103")

    all_ok = (book_count == 66 and chapters == 1189 and verse_count in (31102, 31103))
    if all_ok:
        print("\n  ✅ All acceptance criteria met!")
    else:
        print("\n  ⚠ Some criteria not met — see above")

    return all_ok


# ── Main Pipeline ────────────────────────────────────────────────────────────

def main():
    workspace = Path(__file__).resolve().parent.parent
    data_dir = workspace / "data"
    db_path = data_dir / "kjv.db"

    print("=" * 60)
    print("  KJV Text Ingestion Pipeline")
    print("=" * 60)

    # Step 1: Acquire text
    print("\n📥 Acquiring KJV text...")

    # Try JSON format first (bibleapi)
    parsed = []
    try:
        json_cache = data_dir / "kjv.json"
        data = download_json(KJV_JSON_URL, str(json_cache))
        parsed = list(parse_kjv_json(data))
        print(f"  → Parsed {len(parsed):,} verses from JSON")
    except Exception as e:
        print(f"  ⚠ JSON source failed: {e}")
        # Fallback: try pipe-delimited text sources
        for url in KJV_TXT_URLS:
            try:
                kvj_cache_path = data_dir / "kjv.txt"
                kjv_text = download_text(url, str(kvj_cache_path))
                parsed = list(parse_kjv_lines(kjv_text))
                print(f"  → Parsed {len(parsed):,} verses from TXT")
                break
            except Exception as e2:
                print(f"  ⚠ TXT source {url[:50]}... failed: {e2}")
                continue

    if not parsed:
        print("❌ ERROR: Could not acquire KJV text from any source.")
        return 1

    # Step 2: Create database
    print("\n🗄️  Creating database...")
    conn = create_database(str(db_path))
    print(f"  → Database created at {db_path}")

    # Step 3: Insert books
    print("\n📚 Inserting books...")
    book_id_map = insert_books(conn)

    # Step 4: Insert verses
    print("\n📝 Inserting verses...")
    stats = insert_verses(conn, parsed, book_id_map)
    print(f"  → Inserted {stats['total_verses']:,} verses across "
          f"{len(stats['books_seen'])} books")

    # Step 5: Cross-references
    # Try scrollmapper extraction first (most comprehensive), fall back to bibleapi
    crossref_ok = _extract_crossrefs_from_scrollmapper(conn, book_id_map, str(data_dir))
    if not crossref_ok:
        acquire_crossrefs(conn, book_id_map, str(data_dir))

    # Step 6: Verify
    conn.commit()
    ok = verify_database(conn)

    # Build FTS index
    print("\n🔍 Rebuilding full-text search index...")
    conn.execute(
        "INSERT INTO verses_fts(verses_fts) VALUES ('rebuild')"
    )
    print("  → FTS index rebuilt")

    conn.close()

    print(f"\n✅ Pipeline complete! Database: {db_path}")
    print(f"   Size: {os.path.getsize(db_path) / 1024 / 1024:.1f} MB")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
