#!/usr/bin/env python3
"""The README's set table must match the manifest.

A count in prose is a claim, and a claim nobody measures goes stale
silently. That happened in this ecosystem the same week, in the one place
where it CANNOT be checked: a GitHub repository description is metadata
outside the repository, so no gate can reach it, and the official content
repo advertised 432 lessons while carrying 325 (the domain extraction had
moved content out and the number stayed behind).

The rule that came out of it: describe WHAT is in a repository, not HOW
MUCH, wherever no check can run. Here a check CAN run - the README is
inside the repository and the manifest is right next to it - so the table
keeps its numbers and this test keeps them honest.

Runs under pytest (``python -m pytest tests -q``).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"

#: Sets inherited from the template. They are not book sets and are not
#: listed in the README table on purpose (hidden, kept as a valid example).
INHERITED_SETS = frozenset({"example-set"})

#: | [`set-id`](sets/...) | 23 | subject |
TABLE_ROW = re.compile(r"^\|\s*\[`([a-z0-9-]+)`\]\([^)]+\)\s*\|\s*(\d+)\s*\|")


def readme_table() -> dict[str, int]:
    """Set id -> claimed lesson count, from the README's set table."""
    claimed: dict[str, int] = {}
    for line in README.read_text(encoding="utf-8").splitlines():
        match = TABLE_ROW.match(line)
        if match:
            claimed[match.group(1)] = int(match.group(2))
    return claimed


def manifest_sets() -> dict[str, int]:
    """Set id -> lesson_count, from the root manifest, own sets only."""
    manifest = yaml.safe_load((REPO_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    return {
        entry["id"]: entry["lesson_count"]
        for entry in manifest.get("sets") or []
        if entry["id"] not in INHERITED_SETS
    }


def test_the_table_is_not_empty() -> None:
    """A run that parsed no rows would agree with anything (the floor rule)."""
    assert readme_table(), "no set rows parsed from the README table"


def test_every_own_set_is_listed() -> None:
    missing = sorted(set(manifest_sets()) - set(readme_table()))
    assert missing == [], f"sets missing from the README table: {missing}"


def test_the_table_lists_no_set_that_does_not_exist() -> None:
    phantom = sorted(set(readme_table()) - set(manifest_sets()))
    assert phantom == [], f"README table lists unknown sets: {phantom}"


def test_the_lesson_counts_match_the_manifest() -> None:
    manifest = manifest_sets()
    wrong = {
        setId: (claimed, manifest[setId])
        for setId, claimed in readme_table().items()
        if setId in manifest and claimed != manifest[setId]
    }
    assert wrong == {}, f"README claims != manifest lesson_count: {wrong}"


def test_the_manifest_count_matches_the_files_on_disk() -> None:
    """The manifest is the yardstick here, so it must itself be honest -
    otherwise the table above would only be pinned to a second claim."""
    manifest = yaml.safe_load((REPO_ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    wrong: dict[str, tuple[int, int]] = {}
    for entry in manifest.get("sets") or []:
        setDir = REPO_ROOT / entry["path"] / "lessons"
        if not setDir.is_dir():
            continue
        onDisk = len(list(setDir.glob("*.json")))
        if onDisk != entry["lesson_count"]:
            wrong[entry["id"]] = (entry["lesson_count"], onDisk)
    assert wrong == {}, f"manifest lesson_count != files on disk: {wrong}"
