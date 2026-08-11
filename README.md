# Xjoy — AI-Powered KJV Bible

> An AI-powered devotional tool centered on KJV scripture with AI as a wise assistant.

## About

Xjoy is a mobile-first web application for KJV Bible study, featuring:

- **KJV Scripture** — Complete 31,103 verses across 66 books, with full-text search (FTS5)
- **AI Chat** — RAG-powered Q&A with strict scripture grounding guardrails
- **Bible Reader** — Clean, reverent reading experience
- **Study Tools** — Gamified learning with quiz and jigsaw puzzles
- **Reflection Coach** — AI-guided scripture meditation
- **Notes & Bookmarks** — Personal study tools with localStorage persistence
- **PWA Support** — Installable on iOS and Android

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | SQLite + FTS5 |
| AI | Claude API + RAG |

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build static export
npm run build
```

## Deployment

This project is deployed via GitHub Pages as a static export.

## License

MIT License — see [LICENSE](LICENSE) for details.
