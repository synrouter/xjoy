/**
 * Xjoy 静态圣经数据模块
 *
 * 从 kjv.json 加载 KJV 经文数据，构建内存索引，提供 O(1) 经文/章节查找。
 * 用于 GitHub Pages 静态部署 — 无需后端即可浏览和搜索经文。
 *
 * 数据格式：kjv.json → { resultset: { row: [{ field: [verse_id, book, chapter, verse, text] }] } }
 * Verse ID 编码：BBCCCVVV（7 位数字）
 */

import type { Verse, Book, SearchResult, Stats } from '@xjoy/shared';

// ── KJV 书卷元数据 ──────────────────────────────────────────────────────────

export interface BookMeta {
  id: number;
  name: string;
  testament: 'OT' | 'NT';
  chapters: number;
}

export const BOOKS: BookMeta[] = [
  // 旧约 (OT) — 39 卷
  { id: 1, name: 'Genesis', testament: 'OT', chapters: 50 },
  { id: 2, name: 'Exodus', testament: 'OT', chapters: 40 },
  { id: 3, name: 'Leviticus', testament: 'OT', chapters: 27 },
  { id: 4, name: 'Numbers', testament: 'OT', chapters: 36 },
  { id: 5, name: 'Deuteronomy', testament: 'OT', chapters: 34 },
  { id: 6, name: 'Joshua', testament: 'OT', chapters: 24 },
  { id: 7, name: 'Judges', testament: 'OT', chapters: 21 },
  { id: 8, name: 'Ruth', testament: 'OT', chapters: 4 },
  { id: 9, name: '1 Samuel', testament: 'OT', chapters: 31 },
  { id: 10, name: '2 Samuel', testament: 'OT', chapters: 24 },
  { id: 11, name: '1 Kings', testament: 'OT', chapters: 22 },
  { id: 12, name: '2 Kings', testament: 'OT', chapters: 25 },
  { id: 13, name: '1 Chronicles', testament: 'OT', chapters: 29 },
  { id: 14, name: '2 Chronicles', testament: 'OT', chapters: 36 },
  { id: 15, name: 'Ezra', testament: 'OT', chapters: 10 },
  { id: 16, name: 'Nehemiah', testament: 'OT', chapters: 13 },
  { id: 17, name: 'Esther', testament: 'OT', chapters: 10 },
  { id: 18, name: 'Job', testament: 'OT', chapters: 42 },
  { id: 19, name: 'Psalms', testament: 'OT', chapters: 150 },
  { id: 20, name: 'Proverbs', testament: 'OT', chapters: 31 },
  { id: 21, name: 'Ecclesiastes', testament: 'OT', chapters: 12 },
  { id: 22, name: 'Song of Solomon', testament: 'OT', chapters: 8 },
  { id: 23, name: 'Isaiah', testament: 'OT', chapters: 66 },
  { id: 24, name: 'Jeremiah', testament: 'OT', chapters: 52 },
  { id: 25, name: 'Lamentations', testament: 'OT', chapters: 5 },
  { id: 26, name: 'Ezekiel', testament: 'OT', chapters: 48 },
  { id: 27, name: 'Daniel', testament: 'OT', chapters: 12 },
  { id: 28, name: 'Hosea', testament: 'OT', chapters: 14 },
  { id: 29, name: 'Joel', testament: 'OT', chapters: 3 },
  { id: 30, name: 'Amos', testament: 'OT', chapters: 9 },
  { id: 31, name: 'Obadiah', testament: 'OT', chapters: 1 },
  { id: 32, name: 'Jonah', testament: 'OT', chapters: 4 },
  { id: 33, name: 'Micah', testament: 'OT', chapters: 7 },
  { id: 34, name: 'Nahum', testament: 'OT', chapters: 3 },
  { id: 35, name: 'Habakkuk', testament: 'OT', chapters: 3 },
  { id: 36, name: 'Zephaniah', testament: 'OT', chapters: 3 },
  { id: 37, name: 'Haggai', testament: 'OT', chapters: 2 },
  { id: 38, name: 'Zechariah', testament: 'OT', chapters: 14 },
  { id: 39, name: 'Malachi', testament: 'OT', chapters: 4 },
  // 新约 (NT) — 27 卷
  { id: 40, name: 'Matthew', testament: 'NT', chapters: 28 },
  { id: 41, name: 'Mark', testament: 'NT', chapters: 16 },
  { id: 42, name: 'Luke', testament: 'NT', chapters: 24 },
  { id: 43, name: 'John', testament: 'NT', chapters: 21 },
  { id: 44, name: 'Acts', testament: 'NT', chapters: 28 },
  { id: 45, name: 'Romans', testament: 'NT', chapters: 16 },
  { id: 46, name: '1 Corinthians', testament: 'NT', chapters: 16 },
  { id: 47, name: '2 Corinthians', testament: 'NT', chapters: 13 },
  { id: 48, name: 'Galatians', testament: 'NT', chapters: 6 },
  { id: 49, name: 'Ephesians', testament: 'NT', chapters: 6 },
  { id: 50, name: 'Philippians', testament: 'NT', chapters: 4 },
  { id: 51, name: 'Colossians', testament: 'NT', chapters: 4 },
  { id: 52, name: '1 Thessalonians', testament: 'NT', chapters: 5 },
  { id: 53, name: '2 Thessalonians', testament: 'NT', chapters: 3 },
  { id: 54, name: '1 Timothy', testament: 'NT', chapters: 6 },
  { id: 55, name: '2 Timothy', testament: 'NT', chapters: 4 },
  { id: 56, name: 'Titus', testament: 'NT', chapters: 3 },
  { id: 57, name: 'Philemon', testament: 'NT', chapters: 1 },
  { id: 58, name: 'Hebrews', testament: 'NT', chapters: 13 },
  { id: 59, name: 'James', testament: 'NT', chapters: 5 },
  { id: 60, name: '1 Peter', testament: 'NT', chapters: 5 },
  { id: 61, name: '2 Peter', testament: 'NT', chapters: 3 },
  { id: 62, name: '1 John', testament: 'NT', chapters: 5 },
  { id: 63, name: '2 John', testament: 'NT', chapters: 1 },
  { id: 64, name: '3 John', testament: 'NT', chapters: 1 },
  { id: 65, name: 'Jude', testament: 'NT', chapters: 1 },
  { id: 66, name: 'Revelation', testament: 'NT', chapters: 22 },
];

// ── 索引结构 ────────────────────────────────────────────────────────────────

type VerseData = Verse;

interface BibleIndex {
  /** verse_id → Verse 对象 */
  byId: Map<number, VerseData>;
  /** "BookName" → BookMeta */
  booksByName: Map<string, BookMeta>;
  /** book_id → BookMeta */
  booksById: Map<number, BookMeta>;
  /** "BookName:Chapter" → Verse[] */
  chapters: Map<string, VerseData[]>;
  /** 所有经文文本的数组（用于搜索） */
  verseList: VerseData[];
}

let index: BibleIndex | null = null;
let loadPromise: Promise<BibleIndex> | null = null;

// ── 书卷名称解析 ────────────────────────────────────────────────────────────

/**
 * 缩写 → 规范名称映射（复用后端 ABBREV_MAP 逻辑）
 */
const ABBREV_MAP: Record<string, string> = {
  // OT
  gen: 'Genesis', ge: 'Genesis', gn: 'Genesis',
  exo: 'Exodus', ex: 'Exodus', exod: 'Exodus',
  lev: 'Leviticus', le: 'Leviticus',
  num: 'Numbers', nu: 'Numbers', nm: 'Numbers',
  deu: 'Deuteronomy', de: 'Deuteronomy', dt: 'Deuteronomy',
  josh: 'Joshua', jos: 'Joshua',
  judg: 'Judges', jdg: 'Judges', jg: 'Judges',
  ruth: 'Ruth', ru: 'Ruth', rut: 'Ruth',
  '1sam': '1 Samuel', '1sa': '1 Samuel', '1sm': '1 Samuel',
  '2sam': '2 Samuel', '2sa': '2 Samuel', '2sm': '2 Samuel',
  '1kgs': '1 Kings', '1kg': '1 Kings', '1ki': '1 Kings',
  '2kgs': '2 Kings', '2kg': '2 Kings', '2ki': '2 Kings',
  '1chr': '1 Chronicles', '1ch': '1 Chronicles',
  '2chr': '2 Chronicles', '2ch': '2 Chronicles',
  ezra: 'Ezra', ezr: 'Ezra',
  neh: 'Nehemiah', ne: 'Nehemiah',
  esth: 'Esther', es: 'Esther', est: 'Esther',
  job: 'Job', jb: 'Job',
  psa: 'Psalms', ps: 'Psalms', psalm: 'Psalms',
  prov: 'Proverbs', pro: 'Proverbs', pr: 'Proverbs',
  ecc: 'Ecclesiastes', eccles: 'Ecclesiastes', ec: 'Ecclesiastes',
  song: 'Song of Solomon', sos: 'Song of Solomon',
  isa: 'Isaiah', is: 'Isaiah',
  jer: 'Jeremiah', je: 'Jeremiah',
  lam: 'Lamentations', la: 'Lamentations',
  eze: 'Ezekiel', ezek: 'Ezekiel', ez: 'Ezekiel',
  dan: 'Daniel', da: 'Daniel',
  hos: 'Hosea', ho: 'Hosea',
  joel: 'Joel', joe: 'Joel', jl: 'Joel',
  amos: 'Amos', am: 'Amos',
  obad: 'Obadiah', oba: 'Obadiah', ob: 'Obadiah',
  jonah: 'Jonah', jon: 'Jonah', jh: 'Jonah',
  mic: 'Micah', mc: 'Micah',
  nah: 'Nahum', na: 'Nahum',
  hab: 'Habakkuk', hb: 'Habakkuk',
  zeph: 'Zephaniah', zep: 'Zephaniah',
  hag: 'Haggai', hg: 'Haggai',
  zec: 'Zechariah', zech: 'Zechariah', zc: 'Zechariah',
  mal: 'Malachi', ml: 'Malachi',
  // NT
  matt: 'Matthew', mt: 'Matthew',
  mark: 'Mark', mr: 'Mark', mk: 'Mark',
  luke: 'Luke', lu: 'Luke', lk: 'Luke',
  john: 'John', joh: 'John', jn: 'John',
  acts: 'Acts', ac: 'Acts',
  rom: 'Romans', ro: 'Romans',
  '1cor': '1 Corinthians', '1co': '1 Corinthians',
  '2cor': '2 Corinthians', '2co': '2 Corinthians',
  gal: 'Galatians', ga: 'Galatians',
  eph: 'Ephesians', ep: 'Ephesians',
  phil: 'Philippians', php: 'Philippians', ph: 'Philippians',
  col: 'Colossians', co: 'Colossians',
  '1thess': '1 Thessalonians', '1th': '1 Thessalonians',
  '2thess': '2 Thessalonians', '2th': '2 Thessalonians',
  '1tim': '1 Timothy', '1ti': '1 Timothy',
  '2tim': '2 Timothy', '2ti': '2 Timothy',
  titus: 'Titus', tit: 'Titus',
  philem: 'Philemon', phm: 'Philemon',
  heb: 'Hebrews', he: 'Hebrews',
  jas: 'James', jam: 'James', jm: 'James',
  '1pet': '1 Peter', '1pe': '1 Peter', '1pt': '1 Peter',
  '2pet': '2 Peter', '2pe': '2 Peter', '2pt': '2 Peter',
  '1john': '1 John', '1jo': '1 John', '1jn': '1 John',
  '2john': '2 John', '2jo': '2 John', '2jn': '2 John',
  '3john': '3 John', '3jo': '3 John', '3jn': '3 John',
  jude: 'Jude', jud: 'Jude',
  rev: 'Revelation', re: 'Revelation', rv: 'Revelation',
};

/**
 * 解析书卷名称或缩写为规范名称
 */
export function resolveBookName(name: string): string {
  const cleaned = name.trim();
  const lower = cleaned.toLowerCase().replace(/\.$/, '');

  // 先查缩写映射
  if (ABBREV_MAP[lower]) {
    return ABBREV_MAP[lower];
  }

  // 尝试无空格形式（如 "1cor"）
  const noSpace = lower.replace(/\s+/g, '');
  if (ABBREV_MAP[noSpace]) {
    return ABBREV_MAP[noSpace];
  }

  // Title case 匹配（用于处理 "genesis" → "Genesis"）
  const titleCase = cleaned.replace(/\b\w/g, (c) => c.toUpperCase());
  // 查找 BOOKS 中的匹配
  const found = BOOKS.find(
    (b) => b.name.toLowerCase() === lower || b.name === titleCase
  );
  if (found) return found.name;

  throw new Error(`未识别的书卷名称: "${name}"`);
}

// ── 数据加载 ────────────────────────────────────────────────────────────────

interface KjvRow {
  field: [number, number, number, number, string];
}

interface KjvJson {
  resultset: {
    row: KjvRow[];
  };
}

/**
 * 懒加载 kjv.json 并构建索引
 */
export async function loadBibleData(): Promise<BibleIndex> {
  if (index) return index;
  if (loadPromise) return loadPromise;

  loadPromise = (async () => {
    const resp = await fetch('/data/kjv.json');
    if (!resp.ok) {
      throw new Error(`加载圣经数据失败: ${resp.status}`);
    }
    const json: KjvJson = await resp.json();

    const byId = new Map<number, VerseData>();
    const booksByName = new Map<string, BookMeta>();
    const booksById = new Map<number, BookMeta>();
    const chapters = new Map<string, VerseData[]>();
    const verseList: VerseData[] = [];

    // 构建书卷索引
    for (const book of BOOKS) {
      booksByName.set(book.name.toLowerCase(), book);
      booksById.set(book.id, book);
    }

    // 解析经文
    for (const row of json.resultset.row) {
      const [verseId, bookId, chapter, verseNum, text] = row.field;

      const book = booksById.get(bookId);
      if (!book) {
        // 跳过未知书卷
        continue;
      }

      const verse: VerseData = {
        id: verseId,
        book_id: bookId,
        book_name: book.name,
        chapter,
        verse: verseNum,
        text,
        reference: `${book.name} ${chapter}:${verseNum}`,
      };

      byId.set(verseId, verse);
      verseList.push(verse);

      // 按章节分组 — key: "BookName:Chapter"
      const chapterKey = `${book.name}:${chapter}`;
      const chapterVerses = chapters.get(chapterKey);
      if (chapterVerses) {
        chapterVerses.push(verse);
      } else {
        chapters.set(chapterKey, [verse]);
      }
    }

    // 排序每个章节中的经文
    chapters.forEach((vers) => {
      vers.sort((a, b) => a.verse - b.verse);
    });

    index = { byId, booksByName, booksById, chapters, verseList };
    return index;
  })();

  return loadPromise;
}

/**
 * 确保数据已加载（内部使用）
 */
async function ensureIndex(): Promise<BibleIndex> {
  return loadBibleData();
}

// ── 公共 API（与后端 API 返回格式一致）──────────────────────────────────────

/**
 * 获取所有书卷列表
 */
export async function getBooks(): Promise<Book[]> {
  return BOOKS.map((b, i) => ({
    id: b.id,
    name: b.name,
    sort_order: i + 1,
    testament: b.testament,
    chapters: b.chapters,
  }));
}

/**
 * 获取单节经文（通过引用，如 "John 3:16"）
 */
export async function getVerse(reference: string): Promise<Verse> {
  const idx = await ensureIndex();

  // 解析引用
  const match = reference.match(
    /^\s*(\d*\s*[A-Za-z]+(?:\s+(?:of\s+)?[A-Za-z]+)*)\s+(\d+)\s*:\s*(\d+)\s*$/
  );
  if (!match) {
    throw new Error(`无效的经文引用格式: "${reference}"`);
  }

  const [, bookRaw, chapterStr, verseStr] = match;
  const bookName = resolveBookName(bookRaw);
  const chapter = parseInt(chapterStr, 10);
  const verseNum = parseInt(verseStr, 10);

  const chapterKey = `${bookName}:${chapter}`;
  const chapterVerses = idx.chapters.get(chapterKey);
  if (!chapterVerses) {
    throw new Error(`经文未找到: ${reference}`);
  }

  const verse = chapterVerses.find((v) => v.verse === verseNum);
  if (!verse) {
    throw new Error(`经文未找到: ${reference}`);
  }

  return verse;
}

/**
 * 获取整章经文
 */
export async function getChapter(
  book: string,
  chapter: number
): Promise<Verse[]> {
  const idx = await ensureIndex();

  const bookName = resolveBookName(book);
  const chapterKey = `${bookName}:${chapter}`;
  const verses = idx.chapters.get(chapterKey);

  if (!verses || verses.length === 0) {
    throw new Error(`章节未找到: ${book} ${chapter}`);
  }

  return verses;
}

/**
 * 全文搜索（不区分大小写，返回按匹配质量排序的结果）
 */
export async function searchBibleLocal(
  query: string,
  options?: { limit?: number; testament?: string; book?: string }
): Promise<SearchResult[]> {
  const idx = await ensureIndex();

  const limit = options?.limit ?? 50;
  const queryLower = query.toLowerCase();
  const terms = queryLower.split(/\s+/).filter((t) => t.length > 0);

  const targetBook = options?.book ? resolveBookName(options.book) : null;

  const results: SearchResult[] = [];

  for (const verse of idx.verseList) {
    // 过滤条件
    if (targetBook && verse.book_name !== targetBook) continue;
    if (options?.testament) {
      const bookMeta = idx.booksByName.get(verse.book_name.toLowerCase());
      if (!bookMeta || bookMeta.testament !== options.testament) continue;
    }

    const textLower = verse.text.toLowerCase();

    // 精确匹配得分更高
    const exactMatch = textLower.includes(queryLower);
    const allTermsMatch = terms.every((t) => textLower.includes(t));

    if (exactMatch || allTermsMatch) {
      // 计算匹配得分
      let rank = 0;
      if (exactMatch) {
        rank += 100;
        // 匹配位置越靠前得分越高
        const pos = textLower.indexOf(queryLower);
        rank += Math.max(0, 50 - pos);
      }
      // 每个匹配的词条加分
      for (const term of terms) {
        if (textLower.includes(term)) {
          rank += 10;
        }
      }

      // 生成 snippet（高亮上下文）
      let snippet = verse.text;
      if (exactMatch) {
        const idx2 = textLower.indexOf(queryLower);
        const start = Math.max(0, idx2 - 40);
        const end = Math.min(textLower.length, idx2 + queryLower.length + 40);
        snippet =
          (start > 0 ? '…' : '') +
          verse.text.slice(start, end) +
          (end < textLower.length ? '…' : '');
      }

      results.push({
        verse,
        snippet,
        rank,
      });
    }
  }

  // 按得分降序排列
  results.sort((a, b) => b.rank - a.rank);

  return results.slice(0, limit);
}

/**
 * 获取圣经统计信息
 */
export async function getStats(): Promise<Stats> {
  const idx = await ensureIndex();

  const otBooks = BOOKS.filter((b) => b.testament === 'OT');
  const ntBooks = BOOKS.filter((b) => b.testament === 'NT');

  const otVerses = idx.verseList.filter((v) => {
    const book = idx.booksByName.get(v.book_name.toLowerCase());
    return book?.testament === 'OT';
  }).length;

  const ntVerses = idx.verseList.filter((v) => {
    const book = idx.booksByName.get(v.book_name.toLowerCase());
    return book?.testament === 'NT';
  }).length;

  return {
    books: BOOKS.length,
    verses: idx.verseList.length,
    ot_verses: otVerses,
    nt_verses: ntVerses,
    cross_references: 0, // 静态模式暂不支持交叉引用
  };
}

/**
 * 获取交叉引用（静态模式不支持，返回空数组）
 */
export async function getCrossRefs(
  _reference: string,
  _limit?: number
): Promise<{ target_reference: string }[]> {
  return [];
}

/**
 * 检查数据加载状态
 */
export function isDataLoaded(): boolean {
  return index !== null;
}

/**
 * 预加载数据（可在应用启动时调用）
 */
export function preloadBibleData(): void {
  loadBibleData().catch((err) => {
    console.error('圣经数据预加载失败:', err);
  });
}
