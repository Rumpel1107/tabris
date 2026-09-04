# Defects — Tabris

> **What goes in this document:** everything that broke after an item was called done — found
> in real use, by a test that had been passing, by a review, or reported by a tester. A test
> that goes red while its slice is being built stays out: that is the method working.
>
> Not here: what is pending and what happened (`PLAN.md`), the trail behind one item
> (`docs/<item>/`), or what a defect taught beyond this project (`lessons.md` in `/method`).
>
> Append-only. A defect that comes back is a **new row** naming the earlier one in Cause,
> never an edit of the old row: the pair is the signal.
>
> Seeded on 2026-09-03 with the defects that had already recurred, plus D6, whose lesson is
> already promoted in the method. Everything else keeps its full story in `PLAN.md` and enters
> here the day it repeats.

## Rows

| id | Found | Where | Symptom | Cause | Fix | Caught by | Class | Status |
|---|---|---|---|---|---|---|---|---|
| DEF-1 | 2026-08-27 | `core/memory_manager.py` | A distilled fact was stored with the id prefix of the fact it replaced, `[1] …` | The known facts are shown to the model as `- [id] content`, so the format it is given is the format it writes back | Strip the prefix in code when parsing the response, rather than asking the prompt not to copy it — `83b2fd2` | [NEEDS CLARIFICATION: live or review? the row was seeded from `PLAN.md` §35c, which does not say] | ornament-leaks-into-output | fixed |
| DEF-2 | 2026-08-29 | `core/prompt.py` | The first production reply after the time stamp shipped opened with `[2026-08-29 00:15]` | The assistant's own turns were stamped too, so every turn showed the model ten examples of a reply that starts with a date | Stamp only the user's turns, and strip the mark from the reply before it is stored, echoed or sent — `305f1eb` | live | ornament-leaks-into-output | fixed |
| DEF-3 | 2026-09-01 | `core/memory_manager.py` | A merged fact was stored as `[15,58] Retomó la actividad…` | DEF-1's stripper matched one id only, and a merge cites several | Widen the pattern to a list of ids — `98c1285` | review | ornament-leaks-into-output | fixed |
| DEF-4 | 2026-08-31 | release | The live check of item 34a slice 2 failed against code that did not contain the slice | `v0.1.11` was cut before the fix was committed, so the commit belonged to no tag | Redeployed; `git tag --contains <commit>` before calling anything deployed, written into `collaboration.md` §Git | live | deployed-not-what-was-built | fixed |
| DEF-5 | 2026-09-01 | release | `v0.1.12` served the morning's code; the tag object carried the morning's message | The name was already used that day: `git tag -a` refuses with exit 128 and does not move the tag, and the four commands ran unchained, so push and deploy proceeded anyway | `v0.1.13` cut and deployed; chain a handed-over sequence with `&&` and end it with the check that proves it worked — `collaboration.md` §Git | review | deployed-not-what-was-built | fixed |
| DEF-6 | 2026-08-31 | `core/memory_manager.py` | Twelve facts retired in production with nothing put in their place, including the owner's professional profile and a run he had been told was saved | `apply_memory_changes` applied `RETIRE_IDS` even when `NEW_FACTS` came back empty; item 35c had been verified by reading its merges, which cannot see a deletion that leaves no successor | Drop the retires and log when a pass proposes them with no replacement — `e4a92e8`, in service from `v0.1.13` | review | measured-only-where-it-succeeds | fixed |

## Class

The class names the shape of the mistake, not the area of code. Reuse one whenever it fits.

| Class | What it means | Rows |
|---|---|---|
| ornament-leaks-into-output | Something added to a message for the model's benefit is copied by the model into what it writes | DEF-1, DEF-2, DEF-3 |
| deployed-not-what-was-built | What runs is not the code that was verified | DEF-4, DEF-5 |
| measured-only-where-it-succeeds | A change was verified by counting what it did right, by an instrument blind to what it destroyed | DEF-6 |

## Notes

**DEF-6.** The fence stops a retire that nothing replaces; it does not stop a duplicate being
added, and the same profile later held fourteen active facts of which twelve were distinct.
That half belongs to item 35g and is open there, not here.

**DEF-1 – DEF-3.** Three occurrences of one shape in six days, all fixed the same way: deterministically,
in code. The alternative — an instruction telling the model not to copy the mark — was rejected
each time, because it competes with every other instruction in `prompts/persona.md`.
