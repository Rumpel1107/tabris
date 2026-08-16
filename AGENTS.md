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
- **Findings and trade-offs are written to be read, not to be complete.** When raising something the user did not ask about — a finding, a design trade-off, a possible improvement — write a handful of short plain lines: what it is, what it costs to do nothing, then the options as A/B with a one-line recommendation. Avoid library and API names where a plain word works. Say up front when nothing is broken, and **always list "leave it as is" when it is a legitimate option**. Dense technical prose fails this rule even when it contains no code and every sentence is correct.
- **Propose, don't apply.** Show the code and let the user implement it manually. Never ask "do you want me to apply this?" — just show it. After the user applies a change, read the full file to confirm it matches (green tests are not enough).
- **Let the user set the pace.** Don't end messages pushing to advance.
- **Git is the user's.** The user runs git commands himself. When asked for a commit message, draft it only (subject line + terse one-line bullets, matching the repo's history) — don't run git.
- **Nothing personal in committed files.** This repository is public. Never write the maintainer's infrastructure (machine names, host/container layout, mount paths, absolute paths from a personal setup) or personal data (real names, real locations) into code, tests, or docs. Document the general mechanism instead — it leaks nothing and is more useful to anyone cloning the project. Specifics belong in the conversation.

## Keeping PLAN.md current

When a task is confirmed done, update `PLAN.md` directly: mark the item ✅ and bump the "Last updated" date. This is the one file to edit without proposing first.

Item descriptions stay **one line**. Reasoning, alternatives, and session narrative belong in the conversation — not in the roadmap.

## Keeping README.md current

`README.md` is the project's public face — assume a stranger reads it before anything else. Update it **in the same change** that alters what it promises: the setup command, the requirements, the entry points, the channel list, or the documentation map. Do not defer it to a later cleanup. A stale instruction costs a newcomer more than a missing one.

## Dev setup

- **First run, and every new environment:** `./tools/setup.sh`. Requires Python 3.13+. It checks the preconditions, builds the virtualenv, installs `requirements.txt`, locks down file permissions, and verifies by running the suite. Safe to re-run — it never overwrites an existing `.env`.
- **Run tests:** `~/.venvs/tabris/bin/python -m pytest` (pytest is the official runner — it sees both test styles; plain `unittest discover` silently skips function-style tests).
- **Virtualenv:** lives at `~/.venvs/tabris`, deliberately **outside** the repo. A venv hardcodes absolute paths, so one created inside a project directory breaks for any environment that did not create it — and a project directory is easily shared (mounts, sync, multiple checkouts) while `$HOME` is not. Keeping it under `$HOME` means the same command resolves to the right venv everywhere. Never create one inside the project. Override with `TABRIS_VENV=...` (location) or `PYTHON=...` (interpreter).