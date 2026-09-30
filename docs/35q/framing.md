# Framing — 35q · Standing orders survive the distillation

## Research

### In this code

- **The distillation is told not to keep orders at all.** Its prompt reads: *"Extract only durable
  facts about the user as a person — their preferences, personal data, projects and goals — and
  nothing about the assistant, its capabilities, its limitations or the rules of the conversation"*
  (`core/memory_manager.py`, in force since `43958a4`, 2026-06-30). A standing order is a rule of the
  conversation. The line is ignored in practice: on 2026-09-29, an agent reading the owner's 34 active
  facts counted 7 that read as orders (ids 23, 100, 103, 125, 127, 130, 133). That count is one
  reader's judgment, not the classification — which rows are orders is for the moving pass to decide
  and the owner to confirm. Whether an order is stored depends on the model reading it as a
  preference, again on every pass.
- **The rule that should have stopped DEF-15 is present and correct.** *"Whatever replaces an
  existing fact must be at least as complete as what it retires"* (in force since `3cc2a9e`,
  2026-08-20). On 2026-09-15 it was not followed. An instruction present and correct that is not
  followed is evidence that wording is not the lever.
- **The prompt pushes orders into merges.** It tells the model to merge anything that "overlaps,
  extends or refines" a known fact. An order and a fact on the same subject are exactly that: id 125
  holds both how to search the rate and when to deliver the report.
- **The distillation answers in free text.** `NEW_FACTS:` lines and a `RETIRE_IDS:` list; nothing
  says what kind a line is, so the code has nothing fixed to protect. The fences that exist act on
  ids only: unknown ids are dropped, a retire from a pass that saved nothing is kept (DEF-6), a
  retire by its own wording is kept (DEF-12).
- **In the system prompt, orders have no place of their own.** They sit among the facts under
  `## What I know about the user` (`build_system_prompt` in `core/prompt.py`).

### Elsewhere

- **ChatGPT** keeps custom instructions in a field stored verbatim and edited only by the user;
  memory is a synthesis updated from past chats, and OpenAI recommends explicit directives go in the
  instructions — [Is memory different from Custom
  Instructions?](https://help.openai.com/en/articles/8983151-is-memory-different-from-custom-instructions),
  [Memory FAQ](https://help.openai.com/en/articles/8590148-memory-faq), [Context vs Memory vs Custom
  Instructions](https://prompt-architects.com/blog/491-context-vs-memory-vs-custom-instructions-what-goes-where).
  **Read from search extracts and a third-party guide only: both OpenAI pages returned 403.**
- **OpenClaw** loads its rules (`AGENTS.md`, `SOUL.md`) at the start of every session; `USER.md`,
  written by the user, holds stable preferences with its own 4,000-character budget; `MEMORY.md` is
  curated by the agent through tools — [Agent workspace](https://docs.openclaw.ai/concepts/agent-workspace).
- **Hermes** splits `USER.md` (preferences, expectations; 1,375 characters) from `MEMORY.md`
  (environment facts; 2,200). Both change only through an explicit tool call; `replace` overwrites the
  whole matched entry; over capacity the tool returns an error instead of silently dropping entries —
  [memory.md](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md).
- **Common to all three:** a standing instruction has a place of its own in the prompt, and no
  background summary rewrites it. Of the four assistants, Tabris is the only one where a merge can.

### Assumption (unverified)

- That the model tells an order from a fact reliably at the moment it saves it. The seven rows above
  read as orders, but nothing has measured it. This is the first risk the design has to retire.
- **A reference to measure it against, and a shape it has to handle.** The owner's own quick reading
  (2026-09-29): ids 23, 125, 130 and 133 are orders; 100 and 127 are orders **in part**; 103 is not
  one. On 2026-09-30, reading the full texts, 129 and 77 were added as in part too — their
  instructions sat past the 200 characters the first reading showed; 77 was pointed out by all nine
  runs of the probe, and holds part of the daily report's own order, so that order was spread
  across two rows. The other 26 rows are facts. So some rows are mixed — a fact and an order in one text — and "the code copies the text
  verbatim" does not reach them: copied whole, the fact travels into the orders; split, the text is
  rewritten, which is the model's move that failed in DEF-15. How a mixed row is moved is the first
  question the Spec answers.

## Problem

Someone who gives Tabris a standing order — "answer my first message of the day with the report",
"shopping options always in Colombia", "one step at a time" — expects it to hold until they change
it themselves. Today that order is stored as one more fact, and the distillation, which runs in the
background every 15 exchanges or 20 minutes, can merge it with another fact and retire the original
without telling anyone. It cost the owner his daily report: the order was retired on 2026-09-15 and
he noticed two weeks later, reading his own memory. In the meantime the model imitated the report
still sitting in the window, and two working sessions diagnosed a freshness problem where what was
missing was the instruction. And an order is indistinguishable from any ordinary preference: both
compete in the same block of the prompt.

## Who it is for

Every Tabris user who gives it a standing order — the owner and the beta-testers alike. It is not a
tool built for the daily report: it has to serve "shopping options in Colombia" or "one step at a
time" from anyone. It does not serve someone who only converses and never gives an order; for them
nothing changes.

## Evidence it matters

- **DEF-15.** An order stored since 2026-08-24, rewritten five times by merges and retired on
  2026-09-15, unnoticed for two weeks. Read from the production database.
- **About 7 of 34 active rows** for the owner read as orders today (2026-09-29), each exposed to the
  same path. The count is an agent's reading, not the pass's classification.
- **The rule meant to prevent it existed and was not followed**, so better wording has already been
  tried and was not enough.

## In scope

A direction, not a design:

- Orders are stored apart from facts, and the distillation never offers one for retirement.
- An order changes only through an explicit path the user asks for, and the change replaces the
  whole order.
- Orders have their own block in the prompt, above the facts.
- A single pass moves the orders stored as facts today: the model points at which rows are orders,
  the code copies their text verbatim, and the user confirms the list before anything moves.

## Out of scope

Each with where it lives and what it waits on:

- **The code executing an order** (a time of day, "every day at seven") → item 39. Waits on its
  "what is due now" machinery.
- **Clearing transient or expired facts, long multi-subject rows, what is stored in excess** → 35g.
- **Trying another model for the distillation** → 35g's first measurement.
- **Repeating the moving pass periodically** → deferred, not rejected. Decided once there is evidence
  that an order escaped classification at save time.

## Decision

Build.
