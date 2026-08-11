#!/usr/bin/env python3
"""
Extract cross-references from the scrollmapper Bible SQLite database
and merge them into the Xjoy KJV database.

The scrollmapper cross_reference table uses verse ID encoding:
  vid = BBCCCVVV (book|chapter|verse, zero-padded)
  e.g., 1001001 = Genesis 1:1

This is public domain / CC-BY-4.0 data from openbible.info via TSK.
"""

import os
import sqlite3
import sys
from pathlib import Path

import requests

WORKSPACE = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE / "data"
SCROLLMAPPER_CACHE = DATA_DIR / "bible-sqlite.db"

SCROLLMAPPER_DB_URL = (
    "https://raw.githubusercontent.com/kvbbro/bible_databases/"
    "master/bible-sqlite.db"
)

# Canonical book order (maps scrollmapper book numbers 1-66 → name → our book_id)
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

# Scrollmapper book number → canonical name
BOOK_NUM_MAP: dict[int, str] = {
    i + 1: name for i, name in enumerate(BOOK_ORDER)
}


def decode_vid(vid: int) -> tuple[int, int, int]:
    """Decode verse ID: BBCCCVVV → (book_num, chapter, verse)."""
    s = str(vid)
    # Pad to 8 digits
    s = s.zfill(8)
    book_num = int(s[0:2])
    chapter = int(s[2:5])
    verse = int(s[5:8])
    return book_num, chapter, verse


def download_scrollmapper_db() -> str:
    """Download the scrollmapper database if not cached."""
    if SCROLLMAPPER_CACHE.exists():
        print(f"  → Using cached: {SCROLLMAPPER_CACHE}")
        return str(SCROLLMAPPER_CACHE)

    print(f"  → Downloading scrollmapper database (41.8 MB)...")
    resp = requests.get(SCROLLMAPPER_DB_URL, timeout=300, stream=True)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(SCROLLMAPPER_CACHE, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total and downloaded % (5 * 1024 * 1024) < 65536:
                pct = int(downloaded / total * 100)
                print(f"    {pct}% ({downloaded / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB)")

    print(f"  → Downloaded {downloaded / 1024 / 1024:.1f} MB")
    return str(SCROLLMAPPER_CACHE)


def build_book_id_map(target_conn: sqlite3.Connection) -> dict[int, int]:
    """
    Map scrollmapper book number → our book_id.
    Scrollmapper uses 1-66, our books are ordered the same way.
    """
    mapping = {}
    rows = target_conn.execute(
        "SELECT id, sort_order FROM books ORDER BY sort_order"
    ).fetchall()
    for our_id, sort_order in rows:
        mapping[sort_order] = our_id
    print(f"  → Built book mapping for {len(mapping)} books")
    return mapping


def main():
    target_path = DATA_DIR / "kjv.db"

    print("=" * 60)
    print("  Cross-Reference Extractor")
    print("=" * 60)

    # Download
    print("\n📥 Acquiring scrollmapper database...")
    scratch_path = download_scrollmapper_db()

    # Open databases
    print("\n🔗 Opening databases...")
    scratch_conn = sqlite3.connect(f"file:{scratch_path}?mode=ro", uri=True)
    target_conn = sqlite3.connect(str(target_path))
    target_conn.execute("PRAGMA foreign_keys=ON")
    target_conn.execute("PRAGMA journal_mode=WAL")

    # Build book mapping (scrollmapper book_num → our book_id)
    book_id_map = build_book_id_map(target_conn)

    # First, clear existing cross-references
    target_conn.execute("DELETE FROM cross_references")
    print("  → Cleared existing cross-references")

    # Extract and insert
    print("\n📖 Extracting cross-references...")
    BATCH = 5000
    offset = 0
    inserted = 0
    skipped = 0
    non_canonical = set()

    while True:
        rows = scratch_conn.execute(
            "SELECT vid, r, sv, ev FROM cross_reference "
            "LIMIT ? OFFSET ?",
            (BATCH, offset)
        ).fetchall()

        if not rows:
            break

        batch_data = []
        for vid, relevance, sv, ev in rows:
            try:
                # Decode source verse
                src_book_num, src_ch, src_vs = decode_vid(vid)
                # Decode target verse
                tgt_book_num, tgt_ch, tgt_vs = decode_vid(sv)
                tgt_end_vs = decode_vid(ev)[2] if ev and ev != 0 else None
            except (ValueError, IndexError):
                skipped += 1
                continue

            # Filter non-canonical books (>66)
            if src_book_num > 66 or tgt_book_num > 66:
                if src_book_num > 66:
                    non_canonical.add(src_book_num)
                if tgt_book_num > 66:
                    non_canonical.add(tgt_book_num)
                skipped += 1
                continue

            src_bid = book_id_map.get(src_book_num)
            tgt_bid = book_id_map.get(tgt_book_num)

            if not src_bid or not tgt_bid:
                skipped += 1
                continue

            batch_data.append((
                src_bid, src_ch, src_vs,
                tgt_bid, tgt_ch, tgt_vs,
                tgt_end_vs,
            ))

        # Bulk insert
        if batch_data:
            target_conn.executemany(
                "INSERT OR IGNORE INTO cross_references "
                "(source_book_id, source_chapter, source_verse, "
                "target_book_id, target_chapter, target_verse, target_end_verse) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                batch_data
            )
            inserted += len(batch_data)

        offset += BATCH
        if offset % 50000 == 0:
            target_conn.commit()
            print(f"    Processed {offset:,} rows, inserted {inserted:,}...")

    target_conn.commit()

    # Count and verify
    final_count = target_conn.execute(
        "SELECT COUNT(*) FROM cross_references"
    ).fetchone()[0]

    print(f"\n  Source rows:     {offset:,}")
    print(f"  Inserted:        {inserted:,}")
    print(f"  Skipped:         {skipped:,}")
    if non_canonical:
        print(f"  Non-canonical books referenced: {sorted(non_canonical)}")
    print(f"  Final count:     {final_count:,}")

    # Test queries
    print("\n  Cross-reference test (John 3:16):")
    refs = target_conn.execute(
        "SELECT b.name, cr.target_chapter, cr.target_verse "
        "FROM cross_references cr "
        "JOIN books b ON cr.target_book_id = b.id "
        "JOIN books sb ON cr.source_book_id = sb.id "
        "WHERE sb.name = 'John' AND cr.source_chapter = 3 AND cr.source_verse = 16 "
        "LIMIT 10"
    ).fetchall()
    for r in refs:
        # Also get the target verse text
        verse = target_conn.execute(
            "SELECT v.text FROM verses v JOIN books b ON v.book_id = b.id "
            "WHERE b.name = ? AND v.chapter = ? AND v.verse = ?",
            (r[0], r[1], r[2])
        ).fetchone()
        snippet = verse[0][:60] if verse else "?"
        print(f"    → {r[0]} {r[1]}:{r[2]} — {snippet}...")
    if not refs:
        print("    (none found)")

    # Cleanup
    scratch_conn.close()
    target_conn.close()

    print("\n✅ Cross-reference extraction complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
