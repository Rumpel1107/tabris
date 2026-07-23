# Contributing to Tabris

How this project is built and how to keep building it — for any collaborator, human or agent. This file covers the **code**; for collaboration style and commands see `AGENTS.md`, and for goals/decisions/roadmap see `PLAN.md`. The *rationale* behind these rules lives in `PLAN.md` (§3 decisions, §4 architecture) — this file states the actionable rule and points there instead of repeating the why.

## Development workflow

- **TDD.** Write the failing test first (red), then the implementation (green), then refactor. Never write implementation before a failing test exists.
- **End-to-end at every step.** An item is done only when the real app (`main.py`) exercises the new code path and the path it replaces is retired — not when a module exists with green unit tests. No deferred integration.
- **Vibe-coding boundary.** Scaffolding (UI, framework, deploy, boilerplate) may be generated fast. Domain logic (e.g. tax/payroll calculations) must be fully understood, owned, and tested — it is the product. Vibe-code how it looks; understand how it calculates.
- **Memory writes auto-apply; other destructive actions stay human-confirmed.** Memory distillation applies automatically — soft-delete + `retired_at` keep every change reversible, and the user prunes via the forget flow. File changes and any non-reversible action are still confirmed by the user before being applied.

## Testing

- **Runner:** `python3 -m pytest`. It runs both `unittest.TestCase` classes and plain function tests; `unittest discover` silently skips the function ones.
- **Style for new tests:** function style with plain `assert`. Use `@pytest.mark.parametrize` instead of copy-pasting near-identical tests. Mock external APIs (models, search) — tests must not hit the network.
- **Per item:** unit tests (TDD) inside, plus an end-to-end smoke check that runs the real flow with no mocks.
- Existing `unittest.TestCase` tests are fine; migrate them to function style opportunistically when you touch a file, not in bulk.
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
- **Database access.** Every `core/db.py` function goes through the `_connect` helper (sets `PRAGMA foreign_keys = ON` and `row_factory`). Facts are append-only: retire via `is_active = 0` (soft-delete, scoped by `user_id`), never edit content in place or hard delete (§4.3).
- **Bounded context window (§4.4).** Only the system prompt + last N messages are sent to the model, to avoid silent top-truncation that drops the system prompt.