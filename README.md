# alc-books

[![content validation](https://github.com/astrapi69/alc-books/actions/workflows/validate-content.yml/badge.svg)](https://github.com/astrapi69/alc-books/actions/workflows/validate-content.yml)
[![engine on npm](https://img.shields.io/npm/v/learn-content-engine?label=engine%20on%20npm)](https://www.npmjs.com/package/learn-content-engine)

Lesson sets **for books**: one book, one set, whose lessons follow the
book's own structure. Plain lesson files that
[Adaptive Learner](https://github.com/astrapi69/adaptive-learner) loads
directly and no vendor can lock away.

## The sets

| Set | Lessons | Subject |
|---|---|---|
| [`biologische-souveranitat`](sets/de/biologische-souveranitat/) | 23 | CRISPR, germline editing, and who owns your genetic code |
| [`das-lebende-stimmrecht`](sets/de/das-lebende-stimmrecht/) | 15 | how democratic participation stays alive |
| [`ia-para-principiantes`](sets/es/ia-para-principiantes/) | 10 | practical AI literacy for everyday life, from prompts to real-world projects |

Both carry `review_status: generated`: they were produced from the book
text and have not been reviewed by a domain expert yet. That field states
ORIGIN, not quality, and it is what keeps a set out of the "reviewed"
count until someone has read it.

## Adding the next book

**New books come here.** One earlier book, *Die Währung des Geistes*, lives
in its own repository
([`alc-die-waehrung-des-geistes`](https://github.com/astrapi69/alc-die-waehrung-des-geistes))
because it predates this one. It stays there: moving a published set would
change the lesson identity that learner progress hangs on, which is a real
cost for a tidier layout. So there are two shapes in the ecosystem by
history, not by design, and the rule going forward is the simple one - a new
book becomes a set in this repository.

The layout is one directory per book, as siblings:

```
sets/<source-language>/<set-id>/
  manifest.yaml          # the set entry + metadata.lessons (the file list)
  lessons/NN-slug.json   # NN zero-padded to a fixed width
```

Then one entry in the root `manifest.yaml`, and the lesson ids minted:

```bash
npx --no-install learn-content-engine mint-stable-ids sets/de/<set-id>/lessons/*.json --write
# raise schema/stable-id-coverage.txt by one, then:
make lint && make validate && python3 -m pytest tests -q
```

**Zero-pad the `NN-` prefix, and do it before the first publication.**
Display order is the lexicographic sort of the lesson ids, so `kapitel-10`
sorts between `kapitel-1` and `kapitel-2` without padding. Renaming later
is not an option: the file name IS the lesson identity that learner
progress hangs on, so the prefix has to be right while the set is still
unpublished. Both sets here needed that fix on import; the second one
arrived with no prefixes at all.

Two rules this repository adds on top of the shared gates:

- **Bridge lessons** (an introduction, a part divider, an interlude, an
  epilogue) are exempt from the exercise minimum. They summarise and
  connect rather than teach new material, so their text base cannot carry
  the full floor. Chapter lessons are not exempt.
- **`domain` must be a real content domain.** Book exports arrive with
  `domain: "imported"`, which is the app's origin marker and not a domain
  any consumer knows. It passed every other gate silently
  (adaptive-learner#2376), so there is a check for it now.

## What's inside

- `manifest.yaml`: the root manifest listing the sets.
- `sets/`: one directory per book.
- `schema/`: the pinned [`learn-content-engine`](https://github.com/astrapi69/learn-content-engine)
  schema mirror; [`engine-version.txt`](schema/engine-version.txt) holds the
  pinned engine version and is the source of truth. Content is validated
  against this, independent of the app.
- `templates/`: starting-point lessons per domain (language / programming / knowledge).
- `scripts/validate_content.py`: the local validator.
- `scripts/generate_exercises.py`: an optional BYOK AI exercise generator.
- `generated/`: staging area for AI drafts (never shipped directly).
- `.github/workflows/`: CI that validates every push/PR against the pinned engine.
- `docs/`: [GETTING-STARTED.md](docs/GETTING-STARTED.md) and a local
  [LESSON-FORMAT.md](docs/LESSON-FORMAT.md). The **canonical, test-validated**
  format reference is the engine's
  [`docs/lesson-format.md`](https://github.com/astrapi69/learn-content-engine/blob/main/docs/lesson-format.md).

There is also an inherited `example-set` (`sets/en/es-a1/`) from the
template this repository was created from. It stays on
`visibility: hidden` so it never reaches a learner, and the documentation
and tests still reference it as a minimal valid example.

## Quick start

You only need `make` and `python3`. The first `make validate` sets up a
local environment for you (no manual `pip`, no virtualenv, no Poetry):

```bash
git clone https://github.com/astrapi69/alc-books.git
cd alc-books
make validate      # first run creates .venv and installs deps; exit 0 == all sets pass
make lint          # the semantic engine gate CI also runs
make lint-warnings # the same run, plus the W-* author warnings
```

`make lint` installs the engine release pinned in
`schema/engine-version.txt` into `node_modules/` (gitignored; needs Node.js
and npm) and checks every lesson and manifest with the engine's rule ids
(`E-CARD-REF` and friends).

No `make` (e.g. Windows without WSL)? Run the validator in a virtualenv
yourself:

```bash
python3 -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 scripts/validate_content.py
```

Or just commit and let CI validate; it runs the same checks. Installing
the deps globally with a bare `pip install` fails on modern
Debian/Ubuntu/macOS (PEP 668, "externally-managed-environment"); the
virtualenv above is why.

Full walkthrough: [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).

## Export a set for AI review

`scripts/export_set.py` writes all lessons of ONE set into a single
YAML (or JSON) file so an AI assistant or a human can review the whole
set in one pass (syntax, correctness, consistency across lessons):

```bash
python3 scripts/export_set.py es-a1 --lang en
# -> exports/es-a1-en-<timestamp>.yaml
python3 scripts/export_set.py es-a1 --lang en --format json --out /tmp/review.json
```

The slug is the set id from the root `manifest.yaml` (`example-set`) or
the folder name of the set path (`es-a1`); when the same folder name
exists under several source-language directories, `--lang` (default
`de`) picks the `sets/<lang>/` directory. Non-ASCII characters stay
real UTF-8. An unknown slug aborts with a list of the available sets.

The export is self-contained: its first field `review_instructions`
holds the complete review prompt from
[`docs/ai-review-prompt-template.md`](docs/ai-review-prompt-template.md)
(read at runtime, not copied into the script). The export file can be
handed to a review AI as-is, without manually prepending a prompt. Edit
the review instructions in that template file and keep the sibling
content repos in sync.

**Read-only snapshot, NOT a re-import format:** nothing reads the
export back. Changes flow only through the individual schema-validated
lesson JSONs under `sets/`. The `exports/` folder is gitignored.

Full usage guide and best practices (incl. the source-chapter workflow):
[`docs/export-set-usage.md`](docs/export-set-usage.md) (English) /
[`docs/export-set-usage.de.md`](docs/export-set-usage.de.md) (Deutsch).

## Export a graded quiz to PDF (school tests)

`scripts/export_quiz_pdf.py` turns a lesson that carries a graded-quiz
exercise (an `ext:*-graded-quiz`: a scored question set, points per
question, optional partial credit on multi-select, an optional
percentage pass threshold) into two print-ready PDFs:

```bash
python3 scripts/export_quiz_pdf.py path/to/graded-quiz.json --out-dir out/
# -> out/<id>-test.pdf      (question paper for students, no answers)
# -> out/<id>-loesung.pdf   (answer sheet for the teacher)
```

The test paper shows the questions with blank checkboxes / answer lines
and the points; the answer sheet shows the correct answers, the points,
a partial-credit note, and the pass threshold. This is a consumer tool -
it renders one presentation of a canonical lesson and does not invoke the
engine, so it is independent of the pinned engine version.

**Caveat (adaptive-learner-content-test#66):** graded-quiz content uses
the `ext:` extension tier, which the content gate (`make lint`) does not
yet accept (it validates core-only and refuses ext lessons). Until that
adoption lands, keep graded-quiz lessons OUTSIDE `sets/` and run the tool
on them directly (a runnable sample lives in
[`tests/fixtures/graded-quiz-sample.json`](tests/fixtures/graded-quiz-sample.json)).

## Generate exercises with AI (optional)

`scripts/generate_exercises.py` turns a topic into a full **language**
lesson with a BYOK model (Anthropic / OpenAI / Gemini) and gates every
draft through the validator before writing it into the `generated/`
staging folder. It is language-focused (target and source differ). For a
**knowledge set** (material written in the same language it teaches,
source == target), the generator is not the right tool; hand-author from
[`templates/knowledge/`](templates/knowledge/) instead.

First set your provider key. It is read from the environment (BYOK) and
never committed:

```bash
export ANTHROPIC_API_KEY="sk-..."   # or OPENAI_API_KEY / GEMINI_API_KEY (Gemini also accepts GOOGLE_API_KEY)
```

**Recommended (via make; reuses the local environment `make validate` set up):**

```bash
make generate ARGS="--topic 'Ordering food in a café' --target-lang fr --source-lang en --level A1 --set-id fr-a1"
```

**Direct (fallback; run it inside the venv from the Quick start):**

```bash
python3 scripts/generate_exercises.py \
  --topic "Ordering food in a café" \
  --target-lang fr --source-lang en --level A1 --set-id fr-a1
```

### Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--topic` | (required) | What the lesson is about. |
| `--target-lang` | (required) | The language the learner studies (BCP-47, e.g. `fr`). |
| `--source-lang` | (required) | The explanation language (BCP-47, e.g. `en`). Must differ from the target. |
| `--level` | `A1` | CEFR level. |
| `--count` | `6` | Exercises to request. The effective minimum is **5** (a smaller value is treated as 5, and the quality gate requires at least 5). |
| `--set-id` | `generated-set` | Staging subfolder under `generated/`. |
| `--provider` | `anthropic` | `anthropic` \| `openai` \| `gemini`. Or set `AL_GEN_PROVIDER`. |
| `--model` | provider default | Override the model (`claude-sonnet-4-5` / `gpt-4o` / `gemini-2.5-flash`). |
| `--retries` | `3` | Extra attempts when a draft fails validation before it is discarded. |
| `--out` | `generated` | Staging directory. |

### What happens, and what you still owe

The script pins the exact lesson-schema JSON in the prompt, parses the
model's reply, and runs it through `validate_content.py`. If validation
fails, the errors go back to the model and it retries (up to `--retries`);
a draft that never validates is discarded, not written. A valid draft
lands in `generated/<set-id>/`, never directly in `sets/`.

Two gates remain after generation, neither of them automatic:

1. **Engine semantic gate** (cloze `___` markers equal the blanks,
   `card_ids` integrity, multiselect disjointness). It runs when the
   pinned `learn-content-engine` is installed, otherwise it is deferred to
   CI. The plain validator does not cover it.
2. **Native-speaker review** for a language you do not speak natively. No
   validator catches an unnatural phrasing or a wrong romanization.
   Machine-generated, then human-verified, is the only trustworthy order.

When a draft is good, move it from `generated/` into your set under
`sets/<source>/<target>-<level>/lessons/`, register it in the set
manifest, and re-run `make validate`.

## How it stays current

Your content is validated against the **pinned** engine version in
`schema/engine-version.txt` on every push and pull request (structural +
semantic + drift gates in `.github/workflows/`). A green CI means your
content is valid for every consumer of that engine release. When the
engine is bumped, it reaches this repository the same way it reaches the
rest of the chain: a deliberate pin-bump PR that the drift gate guards.

Background and prompt recipes: the blog post *Build Your Own Lessons for
Adaptive Learner*. Licensed MIT (see [LICENSE](LICENSE)); your authored
content may carry its own license via each set manifest's `metadata.license`.
