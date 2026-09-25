# Tasks — 35h · Recite stored memory deterministically

## Slices

| # | Slice | Covers | Test command | Exercised in the app by | Dependencies: refusing / silent / wait | Done |
|---|---|---|---|---|---|---|
| 1 | The refactor, alone and first. `run_with_tools` returns a small result carrying the reply and the tool names the turn ran, instead of a bare string (plan D5); `handle_turn` reads the reply from it. No behaviour changes: every existing test asserts the same outcome through the new shape, and the ~30 call sites that read the return are updated with it. | — (enables AC5 and AC6) | `~/.venvs/tabris/bin/python -m pytest` | `~/.venvs/tabris/bin/python -m channels.cli` — hold a normal exchange, one that searches and one that does not; the replies are what they were before, which is the whole point of a refactor | none — no I/O is added or moved | ✅ |
| 2 | The capability. `core/prompt.py` gains the marker, the one pattern that recognizes it (tolerating case and inner spacing), the renderer extracted from `build_system_prompt` — every line-breaking character the standard library recognizes collapsed to a space, bracketed digits in content parenthesized, no active facts rendering as a new `core/strings.py` key in both languages — and the substitution, which removes any other marker-shaped token from the model's text before inserting the block in place of the first. `core/conversation.py` gains `LIST_FACTS_TOOL` (no arguments) and an executor returning the placement instruction and no fact content, registered in `handle_turn`'s tools and executors. `handle_turn` reads the facts again and substitutes as the last step of its reply cleanup, after the timestamp strip and the address filter, only when the result says the tool ran; it logs what happened — the tool ran, the marker was there or not, the block was inserted — so the slice ships with its own instrument. `prompts/persona.md` lines 19 and 33 and `CHANGELOG.md` in the same change. | AC1, AC2, AC3, AC4, AC5, AC7 | `~/.venvs/tabris/bin/python -m pytest tests/test_prompt.py tests/test_conversation.py tests/test_strings.py` | Two runs, because the default language is English and the one in use is Spanish. First, the CLI against a scratch `DATA_DIR` so the user is new: ask "what do you remember about me?" and read the no-facts line in English. Then Discord, in Spanish: "¿qué recuerdas de mí?" — every active fact as `- [id] content`, one per line, compared against the rows in the database; and "¿qué puedes hacer?" naming listing what it remembers | the database, one read at substitution. Refusing: an unreadable or missing path, the library raises — produced in a test by pointing the path at a directory. Silent: a lock held by the background distillation's write, which WAL lets a reader pass; if it ever did block, the bound is `DB_BUSY_TIMEOUT_MS = 5000`. The read itself is timed when the slice is built rather than assumed | ⬜ |
| 3 | The net beneath it. In the branch that already holds the address and fresh-data cycles, a reply from a turn where `list_facts` ran and that carries no marker is asked for once more through the same `continue`, so the regenerated reply passes every check again; a reply that comes back without a marker a second time is sent as the model wrote it. Both outcomes keep their journal line — the loop's says it corrected, the cleanup's says nothing was substituted. | AC6 | `~/.venvs/tabris/bin/python -m pytest tests/test_conversation.py` | Cannot be provoked on demand: the model either places the marker or it does not, and it cannot be made to fail deliberately in production. It stands on its tests and on the two correction cycles already in service (35i, 35j). Declared here rather than found out later | one more round on the model provider the turn already calls. Refusing: a provider error, covered by the ordered fallback. Silent: a hang, bounded by the 15 s `PROVIDER_TIMEOUT` the role already carries | ⬜ |

## Notes

- Slice 1 is a refactor with no behaviour change and goes alone, because the method's size rule
  refuses a review that mixes a refactor with a new behaviour — and because the loud failure it buys
  (plan D5) is what slices 2 and 3 stand on.
- Slice 2 carries its own detection on purpose (the journal lines), not only the capability: without
  it, shipping the capability alone would teach nothing about whether the model places the marker in
  real use, which is the reason it precedes slice 3.
- Slice 2 is the tightest against the 200-line limit. If the renderer, the pattern and the tool
  together exceed it once written, the split is the renderer and the pattern first (no caller), then
  the tool and the wiring — decided here rather than during review.
- Slice 3 is what closes the silence of a marker-less turn; without it, such a turn behaves exactly as
  Tabris behaves today, which is no worse than before.
- Slice 3 must tell a model's reply from the code's own. When the freshness net withholds, the reply
  the turn returns was written by the code, while `tools_ran` still says `list_facts` ran — so a
  marker check that only asks "did the tool run and is the marker missing" would send a notice the
  model never wrote back to the model to be rewritten. Raised by the review of slice 1 on
  2026-09-25, before the branch exists.
- The third correction cycle this adds joins the unification item 35k already owns (D8 and D9 in
  `docs/35j/plan.md`): addresses, fresh data, and now the marker.
- Read against the other phase documents after the review of 2026-09-24: the spec's guarantee is the
  block, not the absence of a model paraphrase; the plan's D3, D4, D9 and D10 are what the slices
  implement in that order; and the system prompt's rendering changes on purpose (plan D6), which the
  spec now states rather than disclaims.

---

**Exit gate**

- [x] Slices in execution order
- [x] Each slice names its literal test command and how the real app exercises it
- [x] Each dependency has its refusing case, its silent case and its bounded wait as a number, or the slice says "none"
- [x] No slice changes more than 200 hand-written lines, tests included; one that would is split here, not in Review
- [x] No slice leaves code that nothing calls
- [x] The phase documents were read against each other; contradictions resolved or recorded
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
- [x] `tools/review.py` ran on the phase documents with the spec as contract, before any code; every finding is resolved or recorded — run 2026-09-24, three reviewers, 16 distinct findings, all resolved in conversation and folded in above
