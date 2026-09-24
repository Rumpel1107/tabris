# Contributing to Tabris

How this project is built and how to keep building it — for any collaborator, human or agent. **This file is the single source of truth for how the project is run:** setup, tests, code conventions and documentation upkeep. For what the product is see `PLAN.md`; for what is pending, `docs/roadmap.md`; for why something was decided, `docs/decisions.md`; for the principles this project does not negotiate, `memory/constitution.md` — this file states the actionable rule and points there instead of repeating the why.

## Layout

```
channels/        thin adapters, one per channel — cli.py, discord_ch.py
                 started with `python -m channels.<name>`
core/            channel-agnostic — conversation, onboarding, memory_manager, db,
                 account, providers, search, prompt, session, strings, text
tools/           operator-side, unreachable from any chat — admin.py (account
                 lifecycle), backup.py, setup.sh
deploy/          the service definition that keeps Tabris running unattended
config.py        roles, providers, limits (committed)  ·  .env — secrets (gitignored)
prompts/         persona.md, loaded into the system prompt
docs/<item>/     the `/method` trail behind one roadmap item — framing, spec, plan, tasks
data/            DATA_DIR, overridable per environment — the database, the channel
                 identity file and the exports; owner-only, created locked down
tests/           mirrors the modules one to one
```

Per-turn flow, identical on every channel:
```
incoming message
  └── adapter: resolve (channel, key) → Session
        ├── no user yet → advance_onboarding()          (shared state machine)
        └── route_message() → safe_handle_turn()
              └── handle_turn(): rebuild system prompt (persona + facts + profile + now)
                    └── run_with_tools() ⇄ providers.chat() → ordered fallback chain
                          └── after replying: distillation runs in a background thread
```

## Dev setup

- **First run, and every new environment:** `./tools/setup.sh`. Requires Python 3.13+. It checks the preconditions, builds the virtualenv, installs `requirements.txt`, locks down file permissions, and verifies by running the suite. Safe to re-run — it never overwrites an existing `.env`.
- **Run tests:** `~/.venvs/tabris/bin/python -m pytest` (pytest is the official runner — it sees both test styles; plain `unittest discover` silently skips function-style tests).
- **Virtualenv:** lives at `~/.venvs/tabris`, deliberately **outside** the repo. A venv hardcodes absolute paths, so one created inside a project directory breaks for any environment that did not create it — and a project directory is easily shared (mounts, sync, multiple checkouts) while `$HOME` is not. Keeping it under `$HOME` means the same command resolves to the right venv everywhere. Never create one inside the project. Override with `TABRIS_VENV=...` (location) or `PYTHON=...` (interpreter).

## Development workflow

- **TDD.** Write the failing test first (red), then the implementation (green), then refactor. Never write implementation before a failing test exists.
- **End-to-end at every step.** An item is done only when the real app (`channels/cli.py`) exercises the new code path and the path it replaces is retired — not when a module exists with green unit tests. No deferred integration.
- **The suite runs twice, neither run by hand.** `.github/workflows/ci.yml` runs `pytest` on every push and pull request to `main` — no keys, no network, nothing to configure. `tools/deploy.sh` runs it again on the server before restarting anything.
- **Deploying and going back are the same command:** `sudo /opt/tabris/deploy.sh <tag>`, with the older tag to return. It checks the tag exists, installs dependencies only if `requirements.txt` moved, refuses a keys file missing a name from `.env.example`, runs the suite, restarts, and confirms the service came up; any failure returns the tag that was in service. Active is not working — the reply from Discord is what proves it.
- **Review runs on the diff before anything is deployed.** `/code-review` for correctness plus reuse and efficiency, `/simplify` for quality alone, `/security-review` when the change touches secrets, personal data or anything reachable from a chat.
- **Before removing something that looks unnecessary, find out why it is there.** The reason is rarely in the code: look in `PLAN.md`, in the item that introduced it, or in `docs/defects.md`. *Why: a defect row that cites a line is a fence — what reads as leftover complexity is the fix for something that already broke in production.*
- **Vibe-coding boundary.** Scaffolding (UI, framework, deploy, boilerplate) may be generated fast. Domain logic (e.g. tax/payroll calculations) must be fully understood, owned, and tested — it is the product. Vibe-code how it looks; understand how it calculates.
- **Memory writes auto-apply; other destructive actions stay human-confirmed.** Memory distillation applies automatically — soft-delete + `retired_at` keep every change reversible, and the user prunes via the forget flow. File changes and any non-reversible action are still confirmed by the user before being applied.

## Versioning

- **A capability raises the second number; everything else raises the third.** Something new the user can do — a channel, a modality, a tool — is `0.N+1.0`. A fix, an adjustment, a later slice completing a capability already shipped, or documentation alone is `0.N.M+1`. The number exists to be read under pressure: when something breaks and an earlier release has to go back into service, the tag list has to say at a glance which ones changed what Tabris can do.
- **`1.0.0` is when Tabris works as an assistant in full** — able to work on code and to take actions through MCP servers, on a calendar or tools of that kind. Until then it is a chat whose memory is still being made reliable, and a major of zero says exactly that.

This is the number a release gets; `README.md` covers how a release is put into service.

## Testing

- **Runner:** see § Dev setup. It runs both `unittest.TestCase` classes and plain function tests; `unittest discover` silently skips the function ones.
- **Style for new tests:** function style with plain `assert`. Use `@pytest.mark.parametrize` instead of copy-pasting near-identical tests. Mock external APIs (models, search) — tests must not hit the network.
- **Per item:** unit tests (TDD) inside, plus an end-to-end smoke check that runs the real flow with no mocks.
- Existing `unittest.TestCase` tests are fine; migrate them to function style opportunistically when you touch a file, not in bulk.
- **Mock at the seam the real code path crosses.** A green test proves nothing if the mock sits where the real path never reaches, or if an error/fallback branch happens to return the value the test expects — both have produced false greens in this project. When changing a contract, confirm each test goes red for the *right reason* before fixing it. Build dispatch tables inside the function rather than at module level (a module-level reference is captured at import and never sees a patch), and pin any config a test depends on instead of relying on production values.
- **A model call on the common path gets its neutral outcome in `tests/conftest.py`, for every test.** A test that is about that call opts into the real one with the marker the fixture names. *Why: a pin each test has to remember drifts — six tests passed through the freshness net without knowing, green only because none looked at the reply (item 35j).*
- **Reuse before adding.** Before writing a new test, search the suite for one that already exercises the behavior. If it exists, extend or parametrize it instead of adding a near-duplicate — a new test must assert something no existing test does. When a test becomes a strict subset of another, merge or drop it as part of the same change.

## Code conventions

- **English** for all code, names, and comments. Comments only when they help an external reviewer understand non-obvious code — never to narrate what the code says.
- **No explanations or narration inside files.** Explanations belong in the pull request / conversation, not in code, tests, or docs.
- **Public functions carry type hints + a short docstring** (e.g. `def save_fact(db_path: str, user_id: int, content: str) -> int:`) — beginner-honest, enough to run `mypy`, not exhaustive.
- **User-facing text goes through `msg(key, language)`** (`core/strings.py`) — never hardcode user-facing text in any language. **English is the default language; Spanish is a supported option** selected per user, so the Spanish entries in `strings.py` are intentional translations, not bugs to "fix".
- **Nothing personal in committed files.** This repository is public. Never write the maintainer's infrastructure (machine names, host/container layout, mount paths, absolute paths from a personal setup) or personal data (real names, real locations) into code, tests, or docs. Document the general mechanism instead — it leaks nothing and is more useful to anyone cloning the project.
- **Examples come in both languages.** Every example written into a model instruction or a test — a few-shot case, a sample message, a fixture — carries a Spanish and an English version. Tabris runs in both (English default, Spanish supported), so a set of examples in one language teaches that language's shape and leaves the other unexercised.

## Architecture — mechanisms

The principles behind these — why the core stays channel-agnostic, why facts are append-only,
why a model never enters a roster untested — are `memory/constitution.md`. This section is only
the "how":

- **Adding a provider** (model, search or transcription) means mirroring the existing structure in `core/providers.py`, `core/search.py` or `core/transcribe.py` and normalizing its response to the common shape — never special-casing a call site. A role that needs longer than the global `PROVIDER_TIMEOUT` declares its own `timeout` beside its providers; it is a property of the role, not of the payload, so two callers can never disagree about the same call.
- **Probing a roster candidate:** `probe_models list` reads the provider's live catalog — the only trustworthy source for a model id and for whether it takes images. `probe_models probe` calls it with a turn-shaped payload and reports whether it answered, how fast, and whether it read the image; add `--tool-choice` for any `general` or `vision` candidate, since a fresh turn forces the search tool on whichever link answers (item 35j) and a model that rejects the parameter turns every fresh turn into a failure (item 35n). Run it again whenever a provider changes its tiers or the size of a turn changes.
- **Changing the freshness classifier:** its prompt lives in `core/freshness.py`, and `tools/probe_freshness.py` imports it from there, so what the probe measures is what production runs. Change the prompt or the `router` roster only after the probe has run against the new wording or model.
- **A schema change** is an `ADD COLUMN`, a new table or a new index, added as an idempotent step inside `init_db`: `CREATE TABLE IF NOT EXISTS` does nothing to a table that already exists, so a new column is an `ALTER TABLE` guarded by a check of `PRAGMA table_info`, safe to run on every start. Add the column to the `CREATE TABLE` as well, so a fresh database and a migrated one end up identical. *Why additive-only: `deploy.sh` returns the code and cannot return the database — after a destructive migration its automatic rollback puts old code on a new schema and reports success. The daily backup is the only way back.*
- **Database access:** every `core/db.py` function goes through the `_connect` helper, which sets `PRAGMA foreign_keys = ON` and `row_factory`.
- **Locking down a new kind of personal data:** owner-only (`600`, or `700` for a directory) applied at the moment the file is created, never by a later sweep — a mode passed at directory creation is ignored when the directory already exists, so enforce it explicitly there.

## Keeping the documentation current

**`PLAN.md`.** When a task is confirmed done, update it directly: mark the item ✅ and bump the "Last updated" date. This is the one file to edit without proposing first. Item descriptions stay **one line** — reasoning, alternatives and session narrative belong in the conversation, not in the roadmap.

**`CHANGELOG.md`.** Internal, for whoever runs or tests this. Every change that someone using Tabris would notice gets its line under `[Unreleased]` **in the same change**, grouped as added, changed, fixed or removed; cutting a tag renames that section to the version. A change nobody outside the code would notice — a refactor, a test, a document — does not need an entry.

**`docs/defects.md`.** Anything that broke after an item was called done — found in real use, by a test that had been passing, by a review, or reported by a tester — gets its row there when the work closes: symptom, cause, fix, how it was caught, and the class of mistake it belongs to. A defect that comes back is a new row naming the earlier one, never an edit of it. A test that goes red while its slice is being built is not a defect. The `/method` skill owns the format.

**`README.md`.** It is the project's public face — assume a stranger reads it before anything else. Update it **in the same change** that alters what it promises: the setup command, the requirements, the entry points, the channel list, or the documentation map. Do not defer it to a later cleanup. A stale instruction costs a newcomer more than a missing one.