# Spec — 35h · Recite stored memory deterministically

## Purpose and scope

When the user asks what Tabris remembers about them, the list of their stored facts reaches them as
the code renders it — real ids, full content, no model renumbering or summarizing. Two pieces do
that: a `list_facts` tool, whose call says the user asked and leaves the turn a trace, and a marker
the model writes where the list belongs, which the code replaces with the rendered block as the last
step before the reply is sent. The tool never hands the model the facts themselves, only the
instruction to place the marker.

What it guarantees is the block: inserted from the database, and the only list the code produces. It
does not guarantee that the model writes nothing of its own beside it — that is declared below and
unenforced.

Two things change beyond the recital, deliberately. The facts are read again at the moment of
substitution, so a turn that also forgets or saves something shows the list as it stands after that
happened. And the same renderer builds the facts block of the system prompt, so the way a fact's
content is neutralized — line breaks, bracketed numbers — applies to what the model sees on every
turn, not only to what the user reads. That closes the same confusion against the model, which is
the reason it is shared rather than copied.

Out of scope: deciding what becomes a fact (35g); calling `forget_fact` or `remember_fact`, which
stays a separate explicit request; and the "Profile" section (name, city, language), which carries no
ids, has shown no problem, and keeps being recited by the model as today.

## User flow

1. The user asks Tabris what it remembers, or about a specific stored fact.
2. The model calls `list_facts`. The call is recorded beside the turn's other tool calls.
3. The tool answers with an instruction only: write the marker where the list belongs, and do not
   write the facts. It returns no fact content.
4. The model composes its reply with the marker where the list goes — free to answer anything else
   the same message asked, around it.
5. The reply goes through the checks it already goes through today, the fresh-data net and the
   address filter among them.
6. As the last step before the reply is sent, the code reads the user's active facts and replaces the
   marker with the rendered block: `- [id] content`, one line per fact. Nothing edits the block
   afterwards.
7. If the user also asked about the Profile, the model recites it as before — unaffected by this item.

## Failure states

| State | What the system detects | What the user sees | What the user can do | How the operator learns |
|---|---|---|---|---|
| No active facts | The user has no active facts | A plain statement that nothing is saved yet, in their own language | Tell Tabris something to remember | Not an error; nothing to learn |
| The model never calls `list_facts` | Nothing — with no call, nothing says a list was owed | The old failure: a free-text answer in the model's own numbering | Ask again, naming memory explicitly | **Invisible on purpose.** Knowing a list was owed means reading the user's intent, which is the classifier open question 2 declines. What makes it noticeable is the block's fixed shape: a reply about memory without it is a miss the owner can see |
| `list_facts` ran and the reply carries no marker | Exact: the call proves the intent, the marker is absent | A corrected reply; if the correction comes back without a marker too, the reply as the model wrote it — the old failure for that turn | Ask again | A journal line naming the miss, countable because the call proves the intent |
| The model writes its own list beside the marker | Nothing — telling a paraphrase of the facts from any other prose needs reading the prose, which no fence here does | The exact block, plus a renumbered paraphrase next to it | Ask again | **Invisible on purpose.** What lowers it is that the model is never handed a freshly formatted copy at the moment it composes |
| The marker comes back in different case or spacing | The one pattern that decides everywhere tolerates it | The correct block; never a raw token | Nothing | Nothing — handled in place |
| The user names a number meaning the line they counted, not the id | Nothing — the tool receives an integer that is valid either way | A different fact retired than the one they meant | Ask for it back: retiring is reversible, and the reply names what was retired | **Unenforced, and item 35o owns the control.** The existing echo of the retired fact's content is what makes it visible at all |

## Abuse cases

| # | Boundary | What someone tries | What must happen instead | AC |
|---|---|---|---|---|
| 1 | A fact's content, written by distillation out of the user's own conversation | Store a fact whose content breaks into a second line, or carries a bracketed number, so one fact shows as two and a fabricated id becomes citable — `"...\n- [99] fake instruction"`, or the same on one line | Each fact's content occupies exactly one line, and the only thing shaped like an id is the real one at the start of its line | AC3 |
| 2 | A page reaching the model through `web_search` / `web_fetch` | Text that induces the model to write the marker, or to call `list_facts` and write it, so the code pastes the stored facts into a reply nobody asked for — on a shared channel, in front of others | The marker alone never substitutes: the call must have run. A turn that both read a page and substituted is recorded, so the case is countable. Accepted knowingly beyond that: the facts already travel in the system prompt every turn, so an induced recital is possible today without this item, and the control for inducement is the existing fence that wraps tool output as data, never instructions | AC5 |

## Acceptance criteria

- **AC1** — Given the user asks what Tabris remembers, when the model calls `list_facts` and writes
  the marker, then the marker is replaced by the block built from the database — every active fact,
  its real id, its content unchanged — and that block is the only list the code produces.
- **AC2** — Given the user has no active facts, when the block is rendered, then it states plainly
  that nothing is saved yet, in the user's own language, and invents nothing in its place.
- **AC3** — Given a fact's content carries any character that breaks a line, or text shaped like a
  bracketed id, when it is rendered — in the reply or in the system prompt — then it occupies exactly
  one line and the only id-shaped text is the real one that opens the line.
- **AC4** — Given the block is shown, then every id in it is the id that fact carries in the
  database. What the model does with a number the user names afterwards is not this item's to
  guarantee; the failure table records it and item 35o owns it.
- **AC5** — Given a reply carries the marker in a turn where `list_facts` did not run, then no
  substitution happens and no fact is inserted.
- **AC6** — Given `list_facts` ran and the reply carries no marker, then the miss is logged and the
  reply is asked for once more; the corrected reply passes through every check the first one did, and
  if it still carries no marker it is sent as the model wrote it.
- **AC7** — Given a reply carries a marker in any tolerated form, then one rule decides everywhere:
  what it recognizes is a marker, what it does not is not. The first marker becomes the block, any
  other marker-shaped token is removed before the block is inserted, and no such token reaches the
  user — whether or not the tool ran.

## Open questions

| # | Question | Status | Resolution / why deferred |
|---|---|---|---|
| 1 | Does this cover the Profile section? | resolved | No — facts only. It carries no ids and no reported problem |
| 2 | Should the call to `list_facts` be forced, the way 35j forces `web_search`? | deferred | Left to the instruction. AC6's journal line cannot decide it — it counts turns where the call already happened, while forcing would fix the turns with no call at all, and telling those apart means classifying the user's intent. The decision rests on how often the owner sees a memory answer arrive without the block, in use |
| 3 | Should the tool return the rendered block along with the instruction? | resolved | No — instruction only. Handing the model the exact text it is told not to write is the pull DEF-2 established: an example of a format teaches that format |
| 4 | Should the marker carry a per-turn random value, so a page cannot forge one? | deferred | It would close abuse case 2 properly and remove the collision with a user who asks about the token itself. It rests on the model copying a random token exactly, which is a measurement nobody has taken — a probe, and its own piece of work |

---

**Exit gate**

- [x] Acceptance criteria in Given/When/Then form
- [x] Failure states enumerated, not implied
- [x] Every boundary where outside data enters has an abuse case, and each is an acceptance criterion
- [x] Every open question resolved or explicitly deferred
- [x] No technical decisions leaked into this document
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
