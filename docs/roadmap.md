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
production today, but production use alone does not close these items). **The deploy freeze of
2026-09-23 ended on 2026-09-29 with `v0.2.0`**, which carried what it had been holding: item 35j's
forced search and its correction cycle, item 35h's stored-fact recital, and DEF-14. The freeze did
what it was for — one release instead of six — at the cost of a batch large enough to be worth
comparing against the outgoing tag before it shipped, which is what was done.

## Phase 3 — Memory, internet, Discord (pre-freeze)

| # | Item | Status |
|---|---|---|
| 1 | **34b** — Image input, slices 2-3: keep an image "in view" across the history window (the risky position bookkeeping), then say once it leaves. Marked for the freeze definition; closes DEF-7 | 🔶 slice 1 in service |
| 2 | **34d** — Telegram as a second channel: a thin adapter reusing item 34's core untouched (D5) | ⬜ |
| 3 | **34l** — Documents attached to a message: plain text first (no model change needed), then PDF, then office formats; reuses 34b's attachment handling | ⬜ |
| 4 | **35e** — A self-description that stays true as the code changes: derive the capabilities block from the tool definitions already sent on every call | ⬜ |
| 5 | **35f** — Search its own stored conversation: a tool beside `web_search`, SQL over `messages` scoped by user, by topic or by date. Foundation for 35g and 35k | ⬜ |
| 6 | **35g** — What deserves to be a fact: an exploration ending in a written decision about the distillation's churn; needs 35f first. Evidence added 2026-09-29, from the owner reading his 34 active rows: the distillation keeps circumstance whole (id 132 stored an entire solved troubleshooting session where the durable fact was one line of it; overnight a merge replaced it with id 134, longer still, keeping the whole diagnosis and adding the decision), and rows grow long and multi-subject, which is what a merge rewrites partially — DEF-15's mechanism. Rows also expire: ids 112 and 118 each hold something whose date has since passed; the owner proposed a periodic pass that clears what is transient or expired, which is in scope here and not in 35q, because a background pass that retires without asking is what lost the order in DEF-15 — it needs the owner's confirmation or a visible, reversible retire. Its first measurement is cheap and offline: replay stored conversations through two or three `memory` models under the same prompt and compare what each keeps | ⬜ |
| 7 | **35h** — Recite stored memory deterministically: a `list_facts` tool rendered by code instead of trusting the model's own numbering | ✅ closed 2026-09-28 at slice 2; the rest became item 35p |
| 8 | **35o** — Act on the fact the user meant when they name a number: the model can read "el 3" as the third line rather than id 3, and the integer the tool receives looks valid either way; decide the control — confirm before retiring, or hand back the fact's content before acting. Needs 35h in service first | ⬜ |
| 9 | **35j** — Fresh data outranks what the model remembers: closed in `v0.2.0`. What remains is the journal watch its own slice 3 names — two weeks of `freshness:` lines decide whether the first persona rule can go, and each real miss joins the probe's lot | 🔶 waiting on the journal, not on code |
| 10 | **35k** — A precise claim the turn never received: first slice is a probe measuring how often a stable fact is misremembered; also unifies the correction cycles now living side by side (D8 in `docs/35j/plan.md`) | ⬜ |
| 11 | **35l** — A fresh value can still be wrong: needs 35j in service first; decide what makes a search result verified | ⬜ |
| 12 | **35q** — Standing instructions as their own kind of memory: kept apart from the facts so no merge can retire one (DEF-15), weighed above them, changed or removed only on the user's own agreement. Executing one on a schedule is item 39, not this one. Trail in `docs/35q/` | 🔶 Tasks drafted; the reviewers' findings are being resolved before Build |
| 13 | **35p** — Decide from the journal whether the `list_facts` path earns its place: a month of `facts: list_facts ran` against `facts: recited without the call` says how often the model uses the tool at all. Few or none, and the marker, the tool and the substitution come out, leaving the renderer and the persona line that actually fixed the recital; a usable fraction, and slices 3 and 4 are what raise it. The counting window opens the day the version carrying 35h is deployed, not the day it was built. Item 35q adds the instructions to the same count, from the day its slice 1 is deployed | ⬜ |

## Phase 4 — Always-on (pre-freeze)

| # | Item | Status |
|---|---|---|
| 14 | **37** — Deploy as an always-on service, slice 5: verify the missed-run catch-up (needs the machine off at the scheduled hour) | 🔶 |
| 15 | **37a** — Recovery notice after an outage: tell each channel what was missed while the service was down | ⬜ |
| 16 | **38** — Basic ops: operator alerts on a private channel (aggregated, no message content), and narrowing broad `except Exception` blocks. The owner's shape for the channel (2026-09-30): an admin user defined in configuration receives them; item 35q's instruction-count warning is one of its first signals. Indexes, structured logging and async I/O stay deferred until real concurrent load | 🔶 |
| 17 | **38a** — Service control: a function-calling tool to start/stop a named service, closed allowlist only | ⬜ |
| 18 | **39** — Scheduled messages — Tabris speaking first: a cheap reminder and a costly recurring briefing, built as one Feature with the reminder shipped and verified first. **Item 35q's execution half lands here**: an order that says "every day at seven" needs the same "what is due" machinery | ⬜ |
| 19 | **39a** — Deliver a suspended person their export as a direct-message attachment; needs item 39's "check what is due" machinery | ⬜ |
| 20 | **39b** — Transcription you can act on: reassess Gemini 3.5 Transcribe as Groq's fallback, and measure the primary's accuracy, which the owner reports as often wrong — unmeasured so far, and dearer since item 35q, where a transcribed voice note can save an instruction or agree to a proposal | ⬜ |
| 21 | **39c** — Is DeepSeek still the right primary for `general`/`memory`? Needs the owner judging real outputs side by side, not a probe | ⬜ |
| 22 | **38b** — An empty model reply costs the whole turn: `strip_time_stamp` receives `None` and raises, and the line sits outside the rollback, so the user's own message stays in the history. Found reviewing item 35h slice 1 on 2026-09-25; the hole predates it and has never been seen in production | ⬜ |

## Phase 5 — After the freeze (backlog, not started)

| # | Item | Status |
|---|---|---|
| 23 | **46** — Google Workspace integration (Calendar, Gmail, Drive) via OAuth | ⬜ |
| 24 | **47** — Notion integration via its API | ⬜ |
| 25 | **47a** — File tools: read and write inside a working directory; prerequisite for 47b | ⬜ |
| 26 | **47b** — Terminal client, reusing the link-code identity; needs 47a | ⬜ |
| 27 | **48** — CLI UX remainder: `Ctrl+C` saves memory on exit, streaming responses | ⬜ |
| 28 | **49** — PM / Dev / Tutor role structure on top of the role→provider map | ⬜ |
| 29 | **50** — Specialized agents by strength (research, documents, images, video) as budget allows | ⬜ |
| 30 | **51** — Multi-provider parallel search aggregation; revisit only if single-provider quality proves insufficient | ⬜ |
| 31 | **52** — Add Brave as a second search provider, sequential fallback after Tavily | ⬜ |
| 32 | **53** — Spoken replies (text-to-speech), post-freeze | ⬜ |
