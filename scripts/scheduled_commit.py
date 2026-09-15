#!/usr/bin/env python3
"""Publish exactly one word of the day, at a randomized time.

Unlike the other daily-commit repos, "word of the day" is inherently a
once-a-day thing, so this picks a single random 2-hour window per day
(deterministic from a date-seeded RNG -- every run of the day agrees),
then a random 0-85 minute sleep inside it, and commits once the pick
lands. GitHub Actions cron can't randomize timing on its own, so the
workflow fires every 2 hours and this script decides which firing (if
any) actually publishes.

A manual `workflow_dispatch` run always publishes immediately, ignoring
the plan (handy for testing).
"""

from __future__ import annotations

import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pick_word as pw  # noqa: E402

WINDOW_HOURS = list(range(0, 24, 2))  # 0,2,...,22 -- matches cron "0 */2 * * *"
MAX_JITTER_SECONDS = 85 * 60
EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME", "")
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"
MANUAL = EVENT_NAME == "workflow_dispatch"

GIT_NAME = os.environ.get("DIGEST_GIT_NAME", "nbyrd9")
GIT_EMAIL = os.environ.get(
    "DIGEST_GIT_EMAIL", "50628304+nbyrd9@users.noreply.github.com"
)

COMMIT_PHRASINGS = [
    "Pick today's word",
    "Publish the word of the day",
    "Add today's word",
    "Reveal today's word",
    "Set the word for today",
    "Post today's vocabulary pick",
    "Choose today's word",
    "Refresh the word of the day",
]


def sh(*args: str, check: bool = True) -> str:
    return subprocess.run(
        args, check=check, capture_output=True, text=True
    ).stdout.strip()


def todays_window(day: str) -> int:
    rng = random.Random(f"word-of-the-day::window::{day}")
    return rng.choice(WINDOW_HOURS)


def current_window(now: datetime) -> int:
    return (now.hour // 2) * 2


def already_committed_today(day: str) -> bool:
    subjects = sh(
        "git", "log", f"--since={day}T00:00:00Z", "--pretty=%s", check=False
    )
    return "[wotd]" in subjects


def publish() -> int:
    rc = pw.main()
    if rc != 0:
        return rc

    if not IN_CI:
        print("[local] picked today's word; skipping git commit/push.")
        return 0

    sh("git", "config", "user.name", GIT_NAME)
    sh("git", "config", "user.email", GIT_EMAIL)
    sh("git", "add", "-A")
    if not sh("git", "status", "--porcelain"):
        print("Nothing changed; nothing to commit.")
        return 0

    now = datetime.now(timezone.utc)
    tag = "" if MANUAL else " [wotd]"
    phrasing = random.choice(COMMIT_PHRASINGS)
    msg = f"{phrasing} ({now:%Y-%m-%d}){tag}"
    sh("git", "commit", "-m", msg)

    for attempt in range(1, 5):
        sh("git", "pull", "--rebase", "--autostash", "origin", "main", check=False)
        push = subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            capture_output=True, text=True,
        )
        if push.returncode == 0:
            print(f"Pushed: {msg}")
            return 0
        print(f"push attempt {attempt} failed: {push.stderr.strip()}", file=sys.stderr)
        time.sleep(5)
    return 1


def main() -> int:
    now = datetime.now(timezone.utc)
    day = f"{now:%Y-%m-%d}"

    if MANUAL:
        print("Manual dispatch: publishing immediately.")
        return publish()

    window = current_window(now)
    chosen = todays_window(day)
    print(f"{day}: today's chosen window is {chosen:02d}; this run is window {window:02d}.")

    if window != chosen:
        print("Not today's chosen window; exiting without commit.")
        return 0
    if already_committed_today(day):
        print("Already published today; exiting.")
        return 0

    jitter = random.randint(0, MAX_JITTER_SECONDS)
    print(f"Sleeping {jitter // 60}m{jitter % 60:02d}s before publishing (time randomization).")
    time.sleep(jitter)

    return publish()


if __name__ == "__main__":
    raise SystemExit(main())
