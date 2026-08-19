# Contributing to Tabris

How this project is built and how to keep building it — for any collaborator, human or agent. This file covers the **code**; for collaboration style and commands see `AGENTS.md`, and for goals/decisions/roadmap see `PLAN.md`. The *rationale* behind these rules lives in `PLAN.md` (§3 decisions, §4 architecture) — this file states the actionable rule and points there instead of repeating the why.

## Development workflow

- **TDD.** Write the failing test first (red), then the implementation (green), then refactor. Never write implementation before a failing test exists.
- **End-to-end at every step.** An item is done only when the real app (`channels/cli.py`) exercises the new code path and the path it replaces is retired — not when a module exists with green unit tests. No deferred integration.
- **Vibe-coding boundary.** Scaffolding (UI, framework, deploy, boilerplate) may be generated fast. Domain logic (e.g. tax/payroll calculations) must be fully understood, owned, and tested — it is the product. Vibe-code how it looks; understand how it calculates.
- **Memory writes auto-apply; other destructive actions stay human-confirmed.** Memory distillation applies automatically — soft-delete + `retired_at` keep every change reversible, and the user prunes via the forget flow. File changes and any non-reversible action are still confirmed by the user before being applied.

## Testing

- **Runner:** `~/.venvs/tabris/bin/python -m pytest` (see `AGENTS.md` § Dev setup). It runs both `unittest.TestCase` classes and plain function tests; `unittest discover` silently skips the function ones.
- **Style for new tests:** function style with plain `assert`. Use `@pytest.mark.parametrize` instead of copy-pasting near-identical tests. Mock external APIs (models, search) — tests must not hit the network.
- **Per item:** unit tests (TDD) inside, plus an end-to-end smoke check that runs the real flow with no mocks.
- Existing `unittest.TestCase` tests are fine; migrate them to function style opportunistically when you touch a file, not in bulk.
- **Mock at the seam the real code path crosses.** A green test proves nothing if the mock sits where the real path never reaches, or if an error/fallback branch happens to return the value the test expects — both have produced false greens in this project. When changing a contract, confirm each test goes red for the *right reason* before fixing it. Build dispatch tables inside the function rather than at module level (a module-level reference is captured at import and never sees a patch), and pin any config a test depends on instead of relying on production values.
- **Reuse before adding.** Before writing a new test, search the suite for one that already exercises the behavior. If it exists, extend or parametrize it instead of adding a near-duplicate — a new test must assert something no existing test does. When a test becomes a strict subset of another, merge or drop it as part of the same change.

## Code conventions

- **English** for all code, names, and comments. Comments only when they help an external reviewer understand non-obvious code — never to narrate what the code says.
- **No explanations or narration inside files.** Explanations belong in the pull request / conversation, not in code, tests, or docs.
- **Public functions carry type hints + a short docstring** (e.g. `def save_fact(db_path: str, user_id: int, content: str) -> int:`) — beginner-honest, enough to run `mypy`, not exhaustive.
- **User-facing text goes through `msg(key, language)`** (`core/strings.py`) — never hardcode user-facing text in any language.

## Architecture patterns

- **Channel-agnostic core (D5).** `core/` must not know which channel (CLI, Telegram) the input came from. Channels are thin adapters that call the core. Per-session state lives in `core/session.py`'s `Session`, never in module globals.
- **Provider abstraction + fallback (D2/D10).** Model providers (`core/providers.py`) and search providers (`core/search.py`) share one shape: an ordered list in `config.py`, tried in order, falling through to the next on error or quota. To add a provider, mirror the existing structure and normalize its response to the common shape — don't special-case call sites.
- **Config vs secrets (D3).** Structure and non-secret config live in `config.py` (committed). Secrets live in `.env` (gitignored); `.env.example` documents the required variables. Never commit a key.
- **Data paths derive from `config.DATA_DIR`, never from `BASE_DIR` (item 37).** Everything a user owns — the database, the channel identity file, the exports — hangs off `DATA_DIR`, which reads `TABRIS_DATA_DIR` and falls back to the repository's `data/`. A deployment keeps its data beside the clone, not inside it, so a hardcoded path breaks it. `BASE_DIR` is only for files that ship with the code, like `prompts/persona.md`.
- **Personal data is created locked down.** The database, `.env`, the channel identity file and every data export are owner-only (`600`, or `700` for a directory), applied at the moment the file is created rather than by a later sweep. Any copy or sync recreates a file with the system default, so permissions drift; setting them at creation is the only version that survives. Careful with directories: a mode passed at creation is ignored when the directory already exists, so enforce it explicitly.
- **Database access.** Every `core/db.py` function goes through the `_connect` helper (sets `PRAGMA foreign_keys = ON` and `row_factory`). Facts are append-only: retire via `is_active = 0` (soft-delete, scoped by `user_id`), never edit content in place or hard delete (§4.3).
- **One deliberate exception to the soft-delete rule: erasing an account.** `delete_user_completely` hard-deletes every row of one user in a single transaction, because a privacy deletion that only marked rows inactive would leave the data exactly where it was. It is the only hard delete in the project, it is reachable from `tools/admin.py` alone, and no chat path may ever call it (item 34c, AC9). Anything else that needs to remove data soft-deletes it.
- **Bounded context window (§4.4).** Only the system prompt + last N messages are sent to the model, to avoid silent top-truncation that drops the system prompt.