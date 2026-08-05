#!/usr/bin/env python3
"""``domain`` must be a real content domain, not an app-internal origin.

Both book sets arrived from the app export carrying ``"domain": "imported"``
on every lesson (astrapi69/adaptive-learner#2376). ``imported`` is the
app's ORIGIN marker for "My Lessons", not a content domain - the app's own
``KNOWN_CONTENT_DOMAINS`` does not list it, so the Discover filter would be
handed a domain that does not exist.

Measured before writing this: a lesson with ``domain: "imported"`` passes
``make lint`` AND ``make validate`` with zero findings. Nothing in the chain
caught it; it was found by reading the files. Three of the five export
defect classes are covered by existing gates, this one was not - and a
defect class that only a careful reader catches will be missed on the third
book.

Runs under pytest (``python -m pytest tests -q``).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_content as vc  # noqa: E402


def test_known_domains_cover_the_app_list() -> None:
    """The list mirrors adaptive-learner's ``KNOWN_CONTENT_DOMAINS`` plus the
    implicit ``language`` default. Kept as a mirror on purpose: the app is
    the consumer that filters on it."""
    assert "language" in vc.KNOWN_DOMAINS
    assert "knowledge" in vc.KNOWN_DOMAINS
    assert "philosophy" in vc.KNOWN_DOMAINS
    assert "imported" not in vc.KNOWN_DOMAINS, "an origin marker is not a domain"


def test_app_origin_marker_is_rejected() -> None:
    """The reproduction: the exact value both book exports shipped."""
    errors: list[str] = []
    vc.validate_domain({"id": "01-probe", "domain": "imported"}, "probe", errors)
    assert errors, "domain 'imported' must be reported"
    assert "imported" in errors[0]


def test_a_real_domain_passes() -> None:
    errors: list[str] = []
    vc.validate_domain({"id": "01-probe", "domain": "knowledge"}, "probe", errors)
    assert errors == []


def test_absent_domain_passes() -> None:
    """A lesson without ``domain`` inherits the set's - that is the normal,
    intended shape after the import cleanup, not a defect."""
    errors: list[str] = []
    vc.validate_domain({"id": "01-probe"}, "probe", errors)
    assert errors == []


def test_every_shipped_lesson_and_set_carries_a_known_domain() -> None:
    """Corpus check: what ships must satisfy the rule it declares."""
    offenders: list[str] = []
    for lessonPath in (REPO_ROOT / "sets").glob("**/lessons/*.json"):
        lesson = json.loads(lessonPath.read_text(encoding="utf-8"))
        domain = lesson.get("domain")
        if domain is not None and domain not in vc.KNOWN_DOMAINS:
            offenders.append(f"{lessonPath.name}: {domain}")
    for manifestPath in [REPO_ROOT / "manifest.yaml", *(REPO_ROOT / "sets").glob("**/manifest.yaml")]:
        manifest = yaml.safe_load(manifestPath.read_text(encoding="utf-8")) or {}
        for entry in manifest.get("sets") or []:
            domain = entry.get("domain")
            if domain is not None and domain not in vc.KNOWN_DOMAINS:
                offenders.append(f"{manifestPath}: set {entry.get('id')}: {domain}")
    assert offenders == [], f"unknown domains shipped: {offenders}"
