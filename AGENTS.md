# AGENTS.md

Entry point for any AI agent (or human) working on this repository. This file holds no rules
of its own — it names where they live, so there is nothing here to drift out of sync.

- **How this project is run** — setup, tests, code conventions and documentation upkeep: @CONTRIBUTING.md
- **What is pending:** [`docs/roadmap.md`](docs/roadmap.md). Read it first when picking up work.
- **What the project is** — [`PLAN.md`](PLAN.md). The principles it does not negotiate: @memory/constitution.md — and why something was decided: [`docs/decisions.md`](docs/decisions.md). What happened: [`docs/log.md`](docs/log.md). What broke after it was called done: [`docs/defects.md`](docs/defects.md).
- **Process** — phases and gates: the `/method` skill. **Collaboration style** — how the maintainer works with an agent: that same skill's `collaboration.md`. Both are personal and live outside this repository.

The two files written with `@` are imported, not linked: an agent tool that reads this file loads
them in full, so their rules are in context from the first message instead of whenever someone
remembers to open them. Keep them as imports. *Why: a link is only followed when an agent chooses
to, and a session writing documents never opened `CONTRIBUTING.md` — its rule against personal
data in this public repository was in force and unread, and personal data was committed.*
