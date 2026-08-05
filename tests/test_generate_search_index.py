#!/usr/bin/env python3
"""Set-entry ``visibility`` and repo-slug parsing in the search index
(mirrored from adaptive-learner-content-test, engine#83 / content-test#87).

``visibility`` is a consumer-display hint on the manifest set entry
(learn-content-engine 0.14.0, schema 1.8, additive): ``hidden`` asks a
consumer app not to surface the set to learners. The generator mirrors
the engine's ``asContentSetEntry`` projection: absent or out-of-enum
values normalize to ``"visible"``, so every index entry carries a
concrete value consumers can filter on without their own defaulting.

Runs under pytest (``python -m pytest tests -q``).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_search_index as gsi  # noqa: E402


def test_slug_from_https_url() -> None:
    assert (
        gsi.slug_from_url("https://github.com/astrapi69/adaptive-learner-content-test.git")
        == "astrapi69/adaptive-learner-content-test"
    )


def test_slug_from_ssh_url() -> None:
    """Regression guard for #87: the scp-like SSH form separates host and
    owner with a colon; the slug must not keep the git@host: prefix."""
    assert (
        gsi.slug_from_url("git@github.com:astrapi69/adaptive-learner-content-test.git")
        == "astrapi69/adaptive-learner-content-test"
    )


def test_slug_from_ssh_scheme_url() -> None:
    assert (
        gsi.slug_from_url("ssh://git@github.com/astrapi69/adaptive-learner-content-test")
        == "astrapi69/adaptive-learner-content-test"
    )


def test_slug_from_url_without_git_suffix_and_trailing_slash() -> None:
    assert (
        gsi.slug_from_url("https://github.com/astrapi69/adaptive-learner-content-test/")
        == "astrapi69/adaptive-learner-content-test"
    )


def test_slug_from_unusable_url_is_none() -> None:
    assert gsi.slug_from_url("") is None
    assert gsi.slug_from_url("just-a-name") is None


def test_absent_visibility_defaults_to_visible() -> None:
    """Absent flag means visible - every pre-1.8 manifest keeps its shape."""
    assert gsi.normalize_visibility(None) == "visible"


def test_hidden_passes_through() -> None:
    assert gsi.normalize_visibility("hidden") == "hidden"


def test_visible_passes_through() -> None:
    assert gsi.normalize_visibility("visible") == "visible"


def test_out_of_enum_normalizes_to_visible() -> None:
    """Engine parity: asContentSetEntry folds unknown values back to visible."""
    assert gsi.normalize_visibility("internal") == "visible"


def test_every_index_entry_carries_visibility() -> None:
    """The generator emits a concrete visibility on every set entry."""
    index, build_errors = gsi.build_index()
    assert not build_errors
    assert index["sets"], "index carries no sets"
    for entry in index["sets"]:
        assert entry["visibility"] in ("visible", "hidden")


def test_absent_review_status_defaults_to_authored() -> None:
    assert gsi.normalize_review_status(None) == "authored"


def test_review_status_states_pass_through() -> None:
    for state in ("authored", "generated", "reviewed"):
        assert gsi.normalize_review_status(state) == state


def test_out_of_enum_review_status_normalizes_to_authored() -> None:
    assert gsi.normalize_review_status("verified") == "authored"


def test_every_index_entry_carries_review_status() -> None:
    """The field has to reach the INDEX, not just the manifest: the index is
    what consumers read, so a badge counting advertisable sets would
    otherwise count every set (engine#94)."""
    index, build_errors = gsi.build_index()
    assert not build_errors
    assert index["sets"], "index carries no sets"
    for entry in index["sets"]:
        assert entry["review_status"] in ("authored", "generated", "reviewed")


#: Sets inherited from adaptive-learner-content-template. They are not this
#: repository's content and must stay out of the learner's Discover list.
INHERITED_EXAMPLE_SETS = frozenset({"example-set"})


def test_inherited_example_sets_are_hidden() -> None:
    """The example sets this repo inherited from the template stay hidden
    (adaptive-learner-content-template#42).

    A template is copied, not shipped: whatever visibility its example
    carries is inherited by every repository created from it. A visible
    example means an author registers their new repo and advertises a demo
    set as their first content - and does not notice, because the list
    looks filled. Nothing between here and the learner's Discover list
    catches it: ``validate_registered_repo.py`` checks clone, commit,
    schema and repo slug but says nothing about the content, and
    ``visible`` is the app's normal case.

    Narrowed from "every set is hidden" when this repo gained its own
    content: the blanket form would have forced real book sets to stay
    hidden too. What must not regress is the INHERITED example, so that is
    what this pins. Deleting the example set is the other valid answer -
    then this list goes empty and the test still holds.
    """
    index, build_errors = gsi.build_index()
    assert not build_errors
    assert index["sets"], "index carries no sets"
    for entry in index["sets"]:
        if entry["id"] not in INHERITED_EXAMPLE_SETS:
            continue
        assert entry["visibility"] == "hidden", (
            f"inherited example set {entry['id']!r} is advertised as visible"
        )


def test_own_sets_are_not_accidentally_hidden() -> None:
    """The repo's OWN sets must be visible - a hidden book set would be
    invisible to learners while looking fine in the file tree (the failure
    the sibling check above guards from the other direction)."""
    index, build_errors = gsi.build_index()
    assert not build_errors
    own = [entry for entry in index["sets"] if entry["id"] not in INHERITED_EXAMPLE_SETS]
    assert own, "repo ships no own sets"
    for entry in own:
        assert entry["visibility"] == "visible", (
            f"own set {entry['id']!r} is hidden and would never reach a learner"
        )
