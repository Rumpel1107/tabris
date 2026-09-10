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
| DEF-7 | 2026-09-07 | `core/conversation.py` | An image sent on Discord could not be asked about in the next message: the assistant reported seeing nothing | `session.images` is replaced on every turn — `{position: images} if images else {}` — so a turn carrying no image erases the previous one. The history keeps text only, and the picture meets it just once, on the call that carries it | open — persist the images of every turn still inside the history window | reported | drops-out-of-view-silently | open |
| DEF-8 | 2026-09-07 | `prompts/persona.md` | Asked whether it could see the images, the assistant answered "sí, estoy viendo las imágenes que enviaste" with no image in its context, and said the opposite a minute later | The model has no way to inspect its own context and answered as though it had. Same shape as `87386d7`, which stopped it offering to save things to memory | open | reported | claims-what-it-cannot-check | open |
| DEF-9 | 2026-09-07 | `core/prompt.py` | The stored instruction to open the first message of each day with a report did not fire, though the fact was never retired (id 78, `retired_at` null) | A standing order is stored as a fact, so it reaches the model under the heading `## What I know about the user`, as one bullet among some forty — an order presented as biography. Its trigger is elsewhere: the line "This is the user's first message of the day" sits in the context block with nothing linking it to that bullet. Timezone (`America/Bogota`) and tool budget (`MAX_TOOL_ROUNDS` = 10) were both checked and ruled out | open — see F7 | reported | instruction-competes-and-loses | open |

| DEF-10 | 2026-09-09 | `core/conversation.py` | Asked for five publications, the answer carried five links; one was `news.ycombinator.com/item?id=` with no id, and the descriptions around them summarised articles nobody had opened | Nothing compared the answer against what the turn had received: the search returns a title, a snippet and an address, and the reply is written from those plus whatever the model supplies. Item 35b answered this same shape with a line in `prompts/persona.md`, which is the DEF-9 class — an instruction among forty | The search now hands over the first 4000 characters of the page itself; the answer is checked before it leaves and, when an address is in none of the results, it goes back to the model — which may search again to complete the request — and only what it still cannot justify is cut, `v0.1.17`–`v0.1.18` | reported | claims-what-it-cannot-check | fixed |
| DEF-11 | 2026-09-09 | `prompts/persona.md` | Asked for the TRM of 30 and 31 December 2025, answered $4,420.00 and $4,409.15 — the real ones are $3,706.97 and $3,757.08 — heading both replies "Confirmado con fuentes" | The journal shows no `tools:` line for either turn: it never searched. A question about a past date reads as something already known, and nothing anywhere checks a claim of having confirmed something. Same class as DEF-10 and same day, but no address is involved, so the fence built for DEF-10 cannot see it | open | reported | claims-what-it-cannot-check | open |

## Class

The class names the shape of the mistake, not the area of code. Reuse one whenever it fits.

| Class | What it means | Rows |
|---|---|---|
| ornament-leaks-into-output | Something added to a message for the model's benefit is copied by the model into what it writes | DEF-1, DEF-2, DEF-3 |
| deployed-not-what-was-built | What runs is not the code that was verified | DEF-4, DEF-5 |
| measured-only-where-it-succeeds | A change was verified by counting what it did right, by an instrument blind to what it destroyed | DEF-6 |
| drops-out-of-view-silently | Something the user believes is still in the conversation has left it, and nothing says so | DEF-7 |
| claims-what-it-cannot-check | The model asserts something about its own context, tools or capabilities that it has no way to verify | DEF-8, DEF-10, DEF-11 |
| instruction-competes-and-loses | An instruction that is present and correct is not followed, because it is one among many | DEF-9 |

## Notes

**DEF-6.** The fence stops a retire that nothing replaces; it does not stop a duplicate being
added, and the same profile later held fourteen active facts of which twelve were distinct.
That half belongs to item 35g and is open there, not here.

**DEF-7 – DEF-9.** All three surfaced in one session on 2026-09-07, none of them caught by a test
or a log line. The vision path writes nothing when an image leaves view, so the log for that hour
holds no error at all — the only evidence was the `attachment` column of the `messages` table and
the conversation itself.

**DEF-8.** Its class already had a precedent before this row existed: `87386d7` stopped the model
offering to save things to memory. Two occurrences of the same shape — the model speaking about
what it can do rather than doing it.

**DEF-10.** What the fix removes is invisible to the user by design, so the log names the host of every
rejected address — and that is what showed the shape: on the first draft of a repeat run it invented five
addresses under five real domains (`docs.docker.com`, `backblaze.com`, `digitalocean.com`, `hostinger.com`,
`vultr.com`) before searching at all. Invented paths under real sites, which is why they read as credible.

**DEF-1 – DEF-3.** Three occurrences of one shape in six days, all fixed the same way: deterministically,
in code. The alternative — an instruction telling the model not to copy the mark — was rejected
each time, because it competes with every other instruction in `prompts/persona.md`.
