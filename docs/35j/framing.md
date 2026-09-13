# Framing — 35j · Fresh data outranks what the model remembers

## Research

- **The model already knows a tool is needed; the generation does not act on it.** Linear probes
  over hidden states predict tool necessity with AUROC 0.89–0.96 across six models, while the
  models' own verbalised decisions are far worse — and asking one family to reason before acting
  dropped accuracy from 83.1% to 47.9% while the probe stayed above 0.9 — [LLM Agents Already Know
  When to Call Tools](https://arxiv.org/html/2605.09252v1). The gap is between knowing and doing,
  not between knowing and not knowing, so a better instruction has nothing to improve.
- **Whether a tool is needed is not a property of the question alone**: it depends on the model
  answering, and capability boundaries do not coincide across models — [Model-Adaptive Tool
  Necessity](https://arxiv.org/pdf/2605.14038). A roster change can therefore move this behaviour
  without anything in this project changing.
- **The standard remedy moves the decision out of the answering model**: a small separate
  classifier predicts what the query needs and selects no retrieval, one retrieval, or an iterative
  one — [Adaptive-RAG](https://arxiv.org/abs/2403.14403). This project already has that shape in the
  `router` role, which classifies every incoming message in one cheap call.
- **In this code, the tool description argues against searching a past date.** `WEB_SEARCH_TOOL`
  tells the model the tool is for current events and for anything "the user implies is recent
  ('today', 'yesterday', 'this week')" (`core/conversation.py`). A question about a date months back
  matches none of that, while the persona demands a search for any figure that changes over time.
- **Assumption (unverified):** that a router-sized call can classify "this answer can have changed
  since training" accurately enough to drive the decision. Nothing has been probed yet, and this is
  the first risk the design has to retire.

## Problem

When someone asks Tabris something whose answer can have changed since its training — a rate, a
price, a piece of news, the state of something in the world — whether to search is left to the
model, and the model fails even when it knows it should search. On 2026-09-09 it gave the exchange
rate of December 2024 as if it were December 2025's. On 2026-09-11 it rebuilt the daily report out
of the previous day's report and headed it "values from the search just now", with no tool call
anywhere in the turn. What this costs the user is worse than an error: an error shaped like a
verified fact, indistinguishable from a correct answer. What it costs the product is its premise —
a tool meant for other people is worth whatever its reliability is worth.

## Who it is for

Anyone who asks Tabris a question of fact: the owner today, the beta-testers at the freeze, and
whoever uses it after. It deliberately does not serve the opposite preference — someone who wants
the model's own knowledge as fast as possible and accepts that it may be stale.

## Evidence it matters

- **DEF-11** (2026-09-09): two exchange-rate figures given for the wrong year, both replies headed
  as confirmed with sources, and no `tools:` line in the journal for either turn.
- **Second live case** (2026-09-11): the daily report turn at 14:50:56 UTC ran the router, one chat
  call and the memory pass — nothing else. The whole day's journal holds no `tools:` line at all,
  and the links in the report were the previous day's.
- **Probe, 5 runs** (2026-09-11): the same question that failed on 2026-09-09, asked with an empty
  history and no facts, searched 5 times out of 5 and answered correctly. The failure is therefore
  not constant: it appears when the window already holds something shaped like the answer.
- **Two rules in `prompts/persona.md`** forbid exactly this — never state a changing figure that did
  not come from a search in the same turn, never claim to have consulted when no tool ran. Both were
  in service before either failure.

## Out of scope

Anything here cannot come back as a requirement without returning to this phase.

1. **A stable fact remembered wrong** — a rare figure, a citation, an article number. It is
   invisible in the question and shows only in the answer, so it needs a different mechanism at a
   different moment of the turn. That is item 35k.
2. **The plumbing behind the daily report** — that its standing order lives among the facts and its
   trigger is severed from the task (DEF-9). 35j makes the report's data fresh; it does not decide
   whether the report fires or whether it follows what it was asked. That is F7 / item 35g.
3. **Searching on every turn.** It would pay a search and its seconds on turns with nothing to
   search — a translation, a summary of the conversation, an opinion — and the experience would get
   worse in the other direction.

## Decision

Build. Feature tier: spec and design before any code.

---

**Exit gate**

- [x] Research done and sources cited
- [x] Problem is one paragraph a stranger could read
- [x] Anti-scope is named
- [x] Evidence exists beyond the owner's intuition
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
