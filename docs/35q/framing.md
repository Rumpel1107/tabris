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
  "what is due now" machinery. *Narrowed on 2026-10-02: only an order that needs Tabris to speak
  first stays out — see the amendment below.*
- **Clearing transient or expired facts, long multi-subject rows, what is stored in excess** → 35g.
- **Trying another model for the distillation** → 35g's first measurement.
- **Repeating the moving pass periodically** → deferred, not rejected. Decided once there is evidence
  that an order escaped classification at save time.

## Decision

Build.

---

## Amendment, 2026-10-02 — an instruction is carried out, not only kept

**Why the scope widened.** On 2026-10-02 the owner's daily report arrived in full shape with no
search behind it: the turn's message was a greeting, the freshness classifier read it `stable`, and
the model wrote sourced, dated figures it never looked up. A probe rebuilt that turn from a backup of
production — same history, facts and clock — and read only the model's first response, 10 runs per
cell:

| Prompt | Greeting in Spanish | Greeting in English |
|---|---|---|
| Today's (instruction among the facts) | 6 of 10 searched | 1 of 10 |
| The planned block above the facts, with persona line 5 pointing at it | 0 of 10 | 3 of 10 |

In every run that did not search, the model recognised the report and either wrote it without the
search or promised to fetch it and stopped. The instruction asks for the searches and persona line 17
forbids a figure no search returned: both present and correct, so wording is not the lever. Storing
an instruction apart and weighing it above the facts keeps it from being lost, and does nothing to get
it carried out. The owner's call: this item ensures instructions are carried out, as far as code
allows, and was paused at slice 1 to widen; it is one item and not two because the store, the
proposals and the execution are one piece.

**In scope, added — a direction, not a design:**

- **Interpreted once, carried out by code.** When an instruction is created, the model translates it
  into three parts: *when* it applies, the *steps* it requires beyond writing, and what the *reply*
  must contain. From then on code evaluates those parts on every turn, and a model is consulted only
  where interpretation is genuinely needed.
- **Any trigger, not one kind.** Always on; by count or clock ("the third message of the day", "on
  Mondays"); by literal text ("whenever I say blue"); by meaning ("when I ask for a product"). The
  first three are decided by code. The last is decided by a classifier shaped like the freshness one,
  given the user's message and the instruction's condition — measurable, and only as reliable as the
  measurement says.
- **Steps forced, not hoped for.** A step fixed in advance is run by code before the model is called;
  an open one is forced as a tool call, one round per step; whatever is left is checked after.
- **A literal reply is the code's.** "Say X" is added or checked by code.
- **Reliability is told, not implied.** Each instruction knows which of its parts code guarantees and
  which depend on a model, and the user can be told so. **Corrected 2026-10-07:** told to the
  operator, never to the user (spec question 16).
- **Creating one is a proposal.** The user sees the translation — the exact text and its three parts —
  and confirms, rejects or adjusts it in words, on the proposal machinery already designed for
  changing and removing (plan D12).

**Out of scope, still:**

- **An instruction that needs Tabris to speak first** — "at seven, without my writing" → item 39. The
  rule fits the three parts; sending a message unprompted is that item's piece.
- **Quality inside a reply** — "verify proper names", "no duplicate links" — stays a request to the
  model, fenced only where a fence already exists.

**Research for this half (2026-10-02):**

- **OpenClaw** structures a standing order much like the three parts above — scope, trigger
  (schedule, event or condition), approval gates, escalation — and asks the agent to
  "Execute-Verify-Report". The order is injected into every session and the verifying is the agent's
  own; nothing outside the model checks it. Time-based triggers go through its scheduler —
  [Automation](https://docs.openclaw.ai/automation.md),
  [Standing Orders](https://docs.openclaw.ai/automation/standing-orders.md).
- **Hermes** carries out scheduled jobs only: a gateway ticking every 60 seconds launches what is due
  in a fresh session — [Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron).
  Nothing found for a rule a message triggers.
- **Claude Code** draws the same line this amendment does: instructions in `CLAUDE.md` the model will
  probably follow, hooks that run whether or not it cooperates —
  [Hooks explained](https://blakecrosley.com/blog/claude-code-hooks-explained),
  [CLAUDE.md vs hooks](https://www.aicodex.to/articles/claude-md-vs-hooks). A compliance figure for
  instructions quoted there (70–90%) is a third party's, unmeasured; this item's own is 3 of 20.
- **Rasa Mantle** enforces three things in its runtime loop: ordered steps, where the framework holds
  a step pointer and fixed steps run "with no model call at all"; tools gated by a condition, removed
  from the model's list when it does not hold; and conditional instructions, stripped from the prompt
  when they do not apply — [Guarantees](https://mantle.rasa.com/maestro/guarantees.md).
- **Read together:** the two assistants Tabris is modelled on rely on the prompt for message-triggered
  orders, which is what this item measured failing; where a guarantee exists, code decides.

**Open, for the Spec:**

- Whether the distillation may still create an instruction without asking, now that creating one is
  a proposal.
- Whether the prompt carries every instruction on every turn, or only those whose trigger holds on
  this one, worded as this turn's task (Mantle's conditional instructions). It would take from the
  model the decision of whether an instruction applies — where the 2026-10-02 report failed — and
  helps the parts code cannot force.
