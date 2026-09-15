# Word of the Day

[![word-of-the-day](https://github.com/nbyrd9/word-of-the-day/actions/workflows/word-of-the-day.yml/badge.svg)](https://github.com/nbyrd9/word-of-the-day/actions/workflows/word-of-the-day.yml)

A new vocabulary word every day, picked deterministically from a curated
212-word bank and published to a small GitHub Pages site by a scheduled
GitHub Actions workflow. Check it in the morning, or whenever -- the word
doesn't change again until tomorrow.

- **View today's word:** https://nbyrd9.github.io/word-of-the-day/
- **Browse past words:** https://nbyrd9.github.io/word-of-the-day/archive.html
- **How it works:** [`.github/workflows/word-of-the-day.yml`](./.github/workflows/word-of-the-day.yml)
  fires every 2 hours; [`scripts/scheduled_commit.py`](./scripts/scheduled_commit.py)
  picks one random 2-hour window per day (date-seeded, so every run of the
  day agrees), waits a random 0-85 minutes inside it, then
  [`scripts/pick_word.py`](./scripts/pick_word.py) selects the day's word,
  rebuilds the site under [`docs/`](./docs), commits, and pushes.
- **Word bank:** [`scripts/word_bank.py`](./scripts/word_bank.py) -- no
  external dictionary API, so there's nothing to go down. Words cycle
  through in a date-seeded shuffled order with no repeats until the whole
  bank (212 words, ~7 months) has been used.
