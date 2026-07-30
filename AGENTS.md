# AGENTS.md

Guidelines for any AI agent (or human) working on this repository.

## Project

Tabris is a personal, always-on AI assistant. **`PLAN.md` is the single source of truth** for goals, decisions, and roadmap — read it first. For code conventions and how the project is built, see **`CONTRIBUTING.md`**.

## Working style

- **Language:** talk to the user in Spanish; write all code, names, and comments in English. The user interface is internationalized through `core/strings.py` (`msg(key, language)` + the `MESSAGES` dict). **English is the default language; Spanish is a supported option** selected per user. All user-facing text MUST go through `msg()` — never hardcode user-facing text in any language. The Spanish entries in `strings.py` are intentional translations, not bugs to "fix" to English.
- **One step at a time — one reviewable unit per message.** A step is what the user can read, understand and apply in one sitting, NOT a logical change.
  - **At most one code block per message.** A change spanning several files or edits is several messages, not one message with several blocks.
  - **A message that introduces a concept the user has not seen carries no code at all.** Explain, wait, then code in the next message.
  - Before a multi-part change, state only its *shape* — never the content of all of them.
  - Findings discovered while investigating are held until the step they belong to, not front-loaded because they are fresh.
- **Explain before coding.** For each step, explain what/how/why in plain language first; show code only after. Do not re-explain concepts already established.
- **Propose, don't apply.** Show the code and let the user implement it manually. Never ask "do you want me to apply this?" — just show it. After the user applies a change, read the full file to confirm it matches (green tests are not enough).
- **Let the user set the pace.** Don't end messages pushing to advance.
- **Git is the user's.** The user runs git commands himself. When asked for a commit message, draft it only (subject line + terse one-line bullets, matching the repo's history) — don't run git.

## Keeping PLAN.md current

When a task is confirmed done, update `PLAN.md` directly: mark the item ✅ and bump the "Last updated" date. This is the one file to edit without proposing first.

## Dev setup

- **Run tests:** `python3 -m pytest` (the official runner — it sees both test styles; plain `unittest discover` silently skips function-style tests).
- **Virtualenv:** not portable — never copy `venv/` between machines. Recreate it per machine from `requirements.txt` (`python3 -m venv venv`, activate, then `pip install -r requirements.txt`).