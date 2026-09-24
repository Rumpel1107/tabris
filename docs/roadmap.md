# Roadmap

> **What goes in this document:** what is pending. One line per item, in execution order — the
> `#` column is the running order, not a topic.
>
> Not here: why something was decided (`docs/decisions.md`), what already happened
> (`docs/log.md`), how the project is built (`CONTRIBUTING.md`). Portfolio-wide work — the
> pipeline, the publishable gate, what to write and publish about Tabris — is not Tabris's to
> hold: it lives in the workspace `PLAN.md`, same as the owner, the constraints and the gate
> already didn't.

Moved from `PLAN.md` §5 on 2026-09-23. Each item keeps its original id in bold (`34b`, `35j`...)
because it is already cited elsewhere in the repository — `docs/<id>/`, `CHANGELOG.md`,
`docs/defects.md`, git commit messages — and those references would break if the id changed. The
`#` column is new: it is the order this file reads in, not the id. The narrative that used to sit
behind each closed item in `PLAN.md` (what was tried, what failed, what was measured) moved to
`docs/log.md` on 2026-09-24, dated by when it happened rather than by item id.

Two of the old phases are dropped rather than moved, and the ones that remain are renumbered so
the running order has no gap:
- **The old item 45** (employment contract liquidator) named a dependency on Tabris from a
  *different* project's own roadmap, not work Tabris has to do — that project's backlog is the
  workspace `PLAN.md`.
- **The old items 43 and 44** (a LinkedIn/blog post, a GitHub profile README) are portfolio
  presentation, which this same file's header already says is not Tabris's to hold — the
  workspace `PLAN.md` gained a "Portfolio site" backlog entry on 2026-09-23 for exactly this kind
  of work, and that is where deciding what to write and publish about Tabris now belongs.
- **The old Phase 7 (post-freeze backlog) is renumbered Phase 5**, since the two phases between it
  and Phase 4 are gone. No other document references "Phase 5/6/7" by number (checked), so nothing
  else needed updating.

## Where the project stands

Phase 2 (API-based, zero local-model dependency) is closed. Most of Phase 3 is closed too —
memory, internet access, Discord — but the freeze Phase 3+4 were meant to close before does not
land until everything below through Phase 4 is done (workspace `PLAN.md` P4: Tabris runs in
production today, but production use alone does not close these items). **A deploy freeze is
separately in effect since 2026-09-23**, agreed with the owner, until enough finished work
accumulates for one release worth shipping — items already built and reviewed but not yet
deployed are marked below.

## Phase 3 — Memory, internet, Discord (pre-freeze)

| # | Item | Status |
|---|---|---|
| 1 | **34b** — Image input, slices 2-3: keep an image "in view" across the history window (the risky position bookkeeping), then say once it leaves. Marked for the freeze definition; closes DEF-7 | 🔶 slice 1 in service |
| 2 | **34d** — Telegram as a second channel: a thin adapter reusing item 34's core untouched (D5) | ⬜ |
| 3 | **34l** — Documents attached to a message: plain text first (no model change needed), then PDF, then office formats; reuses 34b's attachment handling | ⬜ |
| 4 | **35e** — A self-description that stays true as the code changes: derive the capabilities block from the tool definitions already sent on every call | ⬜ |
| 5 | **35f** — Search its own stored conversation: a tool beside `web_search`, SQL over `messages` scoped by user, by topic or by date. Foundation for 35g and 35k | ⬜ |
| 6 | **35g** — What deserves to be a fact: an exploration ending in a written decision about the distillation's churn; needs 35f first | ⬜ |
| 7 | **35h** — Recite stored memory deterministically: a `list_facts` tool rendered by code instead of trusting the model's own numbering | ⬜ |
| 8 | **35j** — Fresh data outranks what the model remembers, slice 3 (close): correct `docs/defects.md` DEF-11's wording, mark the item, cut the tag and verify live — held by the deploy freeze above | 🔶 slices 1-2 done, not deployed |
| 9 | **35k** — A precise claim the turn never received: first slice is a probe measuring how often a stable fact is misremembered; also unifies the correction cycles now living side by side (D8 in `docs/35j/plan.md`) | ⬜ |
| 10 | **35l** — A fresh value can still be wrong: needs 35j in service first; decide what makes a search result verified | ⬜ |

## Phase 4 — Always-on (pre-freeze)

| # | Item | Status |
|---|---|---|
| 11 | **37** — Deploy as an always-on service, slice 5: verify the missed-run catch-up (needs the machine off at the scheduled hour) | 🔶 |
| 12 | **37a** — Recovery notice after an outage: tell each channel what was missed while the service was down | ⬜ |
| 13 | **37b** — Move production to the rented host, slice 5 (overdue since 2026-09-20): retire the old homelab deployment; verify every boot-time dependency by an actual reboot, never by reading "enabled" | 🔶 slices 1-4 done |
| 14 | **38** — Basic ops: operator alerts on a private channel (aggregated, no message content), and narrowing broad `except Exception` blocks. Indexes, structured logging and async I/O stay deferred until real concurrent load | 🔶 |
| 15 | **38a** — Service control: a function-calling tool to start/stop a named service, closed allowlist only | ⬜ |
| 16 | **39** — Scheduled messages — Tabris speaking first: a cheap reminder and a costly recurring briefing, built as one Feature with the reminder shipped and verified first | ⬜ |
| 17 | **39a** — Deliver a suspended person their export as a direct-message attachment; needs item 39's "check what is due" machinery | ⬜ |
| 18 | **39b** — Second transcription provider: reassess Gemini 3.5 Transcribe as Groq's fallback | ⬜ |
| 19 | **39c** — Is DeepSeek still the right primary for `general`/`memory`? Needs the owner judging real outputs side by side, not a probe | ⬜ |

## Phase 5 — After the freeze (backlog, not started)

| # | Item | Status |
|---|---|---|
| 20 | **46** — Google Workspace integration (Calendar, Gmail, Drive) via OAuth | ⬜ |
| 21 | **47** — Notion integration via its API | ⬜ |
| 22 | **47a** — File tools: read and write inside a working directory; prerequisite for 47b | ⬜ |
| 23 | **47b** — Terminal client, reusing the link-code identity; needs 47a | ⬜ |
| 24 | **48** — CLI UX remainder: `Ctrl+C` saves memory on exit, streaming responses | ⬜ |
| 25 | **49** — PM / Dev / Tutor role structure on top of the role→provider map | ⬜ |
| 26 | **50** — Specialized agents by strength (research, documents, images, video) as budget allows | ⬜ |
| 27 | **51** — Multi-provider parallel search aggregation; revisit only if single-provider quality proves insufficient | ⬜ |
| 28 | **52** — Add Brave as a second search provider, sequential fallback after Tavily | ⬜ |
| 29 | **53** — Spoken replies (text-to-speech), post-freeze | ⬜ |
