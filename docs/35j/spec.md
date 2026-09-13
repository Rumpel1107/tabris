# Spec — 35j · Fresh data outranks what the model remembers

## Purpose and scope

A question whose answer can have changed since the model was trained is answered from a search run
in that same turn, and whether that search happens is not left to the model's judgement. When the
value cannot be obtained, it is not stated at all.

It deliberately does not cover: a stable fact the model remembers wrongly (item 35k), how good the
source behind a fresh value is (item 35l), the standing order that makes the daily report fire
(DEF-9, item 35g), and searching on every turn.

## User flow

1. The user asks something whose answer can have changed — a rate, a price, a score, news, the
   state of something in the world.
2. The turn is classified before it is answered. The classification does not depend on the model
   that writes the reply.
3. Classified as needing fresh data, the turn searches. The user waits the seconds that costs.
4. The reply states the value, with the date the value belongs to, as item 35i already requires of
   anything resting on a source.
5. A question that cannot have changed — an opinion, a translation, a summary of the conversation,
   what Tabris remembers about the user — skips step 3 and is answered directly.

## Failure states

| State | What the system detects | What the user sees | What the user can do | How the operator learns |
|---|---|---|---|---|
| The search chain failed entirely on a turn that needed it | Every provider raised or returned nothing | Everything that was verified, and a plain statement that this value could not be obtained now | Ask again later, or ask for a different source | A log line counting the turns where a required search produced nothing, with no conversation content |
| The search ran but the value was not in what came back | **Nothing — invisible on purpose.** Whether the value is present is a judgement only the model makes; the code sees a search that succeeded | Same as the row above | Same as above | Not detectable here. It belongs to item 35l |
| Classified as not needing fresh data when it did | Nothing at the time | A stale answer, the original defect | Ask again naming the date or the word "today" | The classification verdict is recorded for every turn, so the miss is countable afterwards |
| Classified as needing fresh data when it did not | Nothing at the time | A slower answer than the question deserved | Nothing; no action is needed | The same verdict record, counted the other way |
| Fresh results arrived and the reply still came from memory | Nothing for a value carrying no address; item 35i covers the case where an address is involved | A stale answer presented as fresh | Push back, which under this item forces a new search | **Invisible for now**, declared as such |
| No result, and that is the true answer (not a failure) | The search ran and returned nothing relevant | That there is no value to give for that date | Ask for a nearby date | Nothing; this is the system working |

## Abuse cases

| # | Boundary | What someone tries | What must happen instead | AC |
|---|---|---|---|---|
| 1 | A user message | Asking, in any wording, that Tabris not search before answering a changing value | The search runs anyway: no phrasing disables it, because no opt-out exists | AC6 |
| 2 | The text of a fetched page, a transcript or an attached document | Carrying a phrase that reads as an instruction to answer without searching | It changes nothing: what decides the search never reads that content as instruction | AC7 |
| 3 | The text of a fetched page or a user message | Carrying text shaped like search results, so the reply can claim a source that never existed | Whether the turn searched is taken from what the system recorded, never from any text in the turn | AC8 |

## Acceptance criteria

- **AC1** — Given a question whose answer can have changed since training, when it is answered, then
  the reply states no such value unless a search ran in that same turn.
- **AC2** — Given such a turn where the value did not come back, when the reply is composed, then the
  value is absent, its absence is stated plainly, and everything else that was verified is still
  delivered.
- **AC3** — Given a question whose answer cannot have changed — an opinion, a translation, a summary
  of the conversation, what Tabris remembers about the user — when it is answered, then no search is
  forced on that turn.
- **AC4** — Given any turn, when it is classified, then the verdict is recorded where the operator
  can read it without reading the conversation.
- **AC5** — Given a reply, when no search ran in the turn, then it contains no claim of having
  consulted, verified or confirmed anything.
- **AC6** — Given a user message asking in any wording that Tabris answer without searching, when the
  turn needs fresh data, then the search runs regardless.
- **AC7** — Given outside text — a page, a transcript, a document — carrying something that reads as
  an instruction to skip searching, when the turn is classified, then the outcome is the same as
  without that text.
- **AC8** — Given text in the turn shaped like search results, when the reply is checked for a claim
  of having searched, then the check uses what the system recorded and not that text.

## Open questions

| # | Question | Status | Resolution / why deferred |
|---|---|---|---|
| 1 | Does the user keep a way to ask for an answer without a search? | resolved | No. A closed list of phrases would be an undocumented command language, and the same phrase arriving inside content nobody here wrote would disable the fence. The case where it would apply — "without searching, what do you think the rate is?" — is the one case where not guessing is the wanted behaviour |
| 2 | When only part of what was asked could be verified, is the rest delivered? | resolved | Yes. The search chain has three providers, so the common failure is one value missing rather than everything failing; withholding the whole reply for one missing value would cost far more than it buys |
| 3 | Is a value verified because one source carried it? | deferred | Item 35l. A fresh value can still be wrong: a provider's own generated answer gave 3126.08 against a real 3116.47 on 2026-09-10, and a news search returns index pages that carry no article |
| 4 | Can the classification be done accurately by a cheap call? | deferred | To the design, as the first risk it has to retire by measurement rather than by argument. An inaccurate classifier reproduces the defect it is meant to close |
| 5 | How many seconds may a forced search add before the delay is worse than the stale answer? | deferred | Unmeasured today. The design reports the added latency and the owner decides with the number in front of him |

---

**Exit gate**

- [x] Acceptance criteria in Given/When/Then form
- [x] Failure states enumerated, not implied
- [x] Every boundary where outside data enters has an abuse case, and each is an acceptance criterion
- [x] Every open question resolved or explicitly deferred
- [x] No technical decisions leaked into this document
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
