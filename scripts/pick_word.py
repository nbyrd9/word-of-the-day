#!/usr/bin/env python3
"""Pick today's word, record it, and rebuild the Pages site.

Deterministic: seeds a shuffle of the whole word bank with a "cycle number"
(today's day-index // bank size), so the order is reproducible but each
full pass through the bank uses a different order, and no word repeats
until every other word has had its turn.

Writes:
  data/today.json        -- current day's pick (for the workflow / debugging)
  data/archive.json      -- append-only list of every past pick
  docs/index.html        -- the Pages site's homepage (today's word)
  docs/archive.html      -- a browsable history of past words

Standard library only.
"""

from __future__ import annotations

import html
import json
import pathlib
import random
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from word_bank import WORD_BANK  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
TODAY_JSON = DATA / "today.json"
ARCHIVE_JSON = DATA / "archive.json"
EPOCH = date(2026, 1, 1)


def day_index(today: date) -> int:
    return (today - EPOCH).days


def pick_for(today: date) -> dict:
    n = len(WORD_BANK)
    idx = day_index(today)
    cycle, position = divmod(idx, n)
    order = list(range(n))
    random.Random(f"word-of-the-day::cycle::{cycle}").shuffle(order)
    entry = dict(WORD_BANK[order[position]])
    entry["date"] = today.isoformat()
    return entry


def load_archive() -> list[dict]:
    if ARCHIVE_JSON.exists():
        return json.loads(ARCHIVE_JSON.read_text(encoding="utf-8"))
    return []


def save_archive(archive: list[dict]) -> None:
    ARCHIVE_JSON.write_text(json.dumps(archive, indent=2) + "\n", encoding="utf-8")


PAGE_CSS = """
  :root {
    --bg: #faf8f5; --fg: #1c1a17; --accent: #8a5a2b; --muted: #6b6558;
    --card: #ffffff; --border: #e6e0d6;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#17140f; --fg:#f2ede4; --accent:#e0a868; --muted:#a89f8f; --card:#221e17; --border:#332c22; }
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--fg); font-family: Georgia, 'Times New Roman', serif;
         margin: 0; padding: 2.5rem 1.25rem; line-height: 1.55; }
  main { max-width: 640px; margin: 0 auto; }
  .eyebrow { color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-size: .78rem; font-family: -apple-system, sans-serif; }
  .word { font-size: 2.6rem; margin: .3rem 0 0; color: var(--accent); }
  .pos { font-style: italic; color: var(--muted); margin: .2rem 0 1.4rem; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem 1.75rem; margin-bottom: 1.5rem; }
  .definition { font-size: 1.15rem; margin: 0 0 1rem; }
  .example { color: var(--muted); margin: 0; }
  .example::before { content: "\\201C"; }
  .example::after { content: "\\201D"; }
  a { color: var(--accent); }
  footer { font-family: -apple-system, sans-serif; font-size: .85rem; color: var(--muted); margin-top: 2rem; }
  table { width: 100%; border-collapse: collapse; font-family: -apple-system, sans-serif; font-size: .95rem; }
  td, th { text-align: left; padding: .5rem .25rem; border-bottom: 1px solid var(--border); }
"""


def render_index(entry: dict, total: int) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Word of the Day &mdash; {html.escape(entry['word'])}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<main>
  <div class="eyebrow">Word of the Day &middot; {html.escape(entry['date'])}</div>
  <h1 class="word">{html.escape(entry['word'])}</h1>
  <p class="pos">{html.escape(entry['pos'])}</p>
  <div class="card">
    <p class="definition">{html.escape(entry['definition'])}</p>
    <p class="example">{html.escape(entry['example'])}</p>
  </div>
  <footer>
    Word #{total} of an ever-growing list &middot; <a href="./archive.html">browse past words</a>
    &middot; <a href="https://github.com/nbyrd9/word-of-the-day">source</a>
  </footer>
</main>
</body>
</html>
"""


def render_archive(archive: list[dict]) -> str:
    rows = "\n".join(
        f"<tr><td>{html.escape(e['date'])}</td><td><strong>{html.escape(e['word'])}</strong></td>"
        f"<td>{html.escape(e['pos'])}</td><td>{html.escape(e['definition'])}</td></tr>"
        for e in reversed(archive)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Word of the Day &mdash; Archive</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<main>
  <div class="eyebrow">Word of the Day</div>
  <h1 class="word" style="font-size:1.8rem;">Archive</h1>
  <p class="pos"><a href="./index.html">&larr; back to today's word</a></p>
  <div class="card">
    <table>
      <thead><tr><th>Date</th><th>Word</th><th>Part of speech</th><th>Definition</th></tr></thead>
      <tbody>
      {rows}
      </tbody>
    </table>
  </div>
</main>
</body>
</html>
"""


def main() -> int:
    today = datetime.now(timezone.utc).date()
    archive = load_archive()

    if archive and archive[-1]["date"] == today.isoformat():
        entry = archive[-1]
        print(f"Today's word already picked: {entry['word']}")
    else:
        entry = pick_for(today)
        archive.append(entry)
        save_archive(archive)
        print(f"Picked today's word: {entry['word']} ({entry['pos']})")

    TODAY_JSON.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(render_index(entry, len(archive)), encoding="utf-8")
    (DOCS / "archive.html").write_text(render_archive(archive), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
