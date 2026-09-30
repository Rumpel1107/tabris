# Spec — 35q · Standing orders survive the distillation

## Purpose and scope

A standing instruction a user gives Tabris is kept apart from the facts it remembers about them,
weighs above those facts in every conversation, and changes or goes away only when that user asks
and says yes. Towards the user these are **instructions**; this document uses the same word.

It does not make the code carry out an instruction on its own — a time of day, "every day at seven"
(item 39). It does not clean transient, expired or oversized facts (item 35g). It does not cap how
many instructions a user may hold (question 7).

## User flow

**F1 — Giving an instruction.**
1. The user says, in their own words, something meant to hold from now on: "from now on, shopping
   options always in Colombia".
2. Tabris answers the message as usual and adds one line with the exact text it saved as an
   instruction.
3. From then on the instruction is present in every conversation with that user, above the facts.

**F2 — An instruction the turn did not catch.**
1. The user said something that works as an instruction without phrasing it as one, and the turn
   did not save it.
2. Later, in the background, the distillation recognizes it. If an instruction with the same or a
   related meaning already exists, nothing happens. Otherwise it is created.
3. The user's next reply carries one line with the exact text saved, and that they can have it
   changed or removed if they disagree.

**F3 — Changing an instruction.**
1. The user asks, in their own words, to change one: "in the report, only 5 news items now".
2. Tabris shows the instruction as it stands and the whole new text, and asks for a yes.
3. On yes, the new text replaces the old. On anything else, nothing changes.

**F4 — Removing an instruction.**
1. The user asks, in their own words, to drop one.
2. Tabris shows which instruction would go, and asks for a yes.
3. On yes, it stops applying. On anything else, nothing changes.

**F5 — Seeing them.**
1. The user asks what Tabris remembers about them.
2. The answer shows their instructions in a block of their own, before the facts, each as stored.

**F6 — Reviewing what memory holds (the one-time move).**
1. The user asks, in their own words, to review their instructions.
2. Tabris looks through their stored facts and proposes: each fact that is an instruction, with its
   text exactly as stored; each fact that is part instruction and part fact, as the original beside
   "this becomes an instruction" and "this stays a fact".
3. The user says yes to all of it, or names what should not move.
4. What was accepted moves; nothing else changes. When there is nothing to propose, Tabris says so
   and shows the instructions the user already has.

## Failure states

| State | What the system detects | What the user sees | What the user can do | How the operator learns |
|---|---|---|---|---|
| The turn meant to save an instruction but the save failed | The write did not complete | The reply, without the saved-instruction line — its absence is the signal | Say it again | A journal line naming the user and the failure |
| The reply claims a save that did not happen | — (the model's own words) | Nothing false: the saved-instruction line comes only from a save that completed, never from the model's text | — | Invisible on purpose; the guarantee is AC2 |
| The distillation judged a new instruction similar to an existing one | Its own verdict | Nothing | If it mattered, say it again in the conversation (F1) | A journal line naming the user and the instruction it matched |
| The distillation created a near-duplicate | — | The one-line notice of F2 | Ask for it to be removed (F4) | The count in the journal |
| The distillation failed | The pass did not complete | Nothing; no instruction is touched | — | The journal line the distillation already writes on failure |
| A change or removal names an instruction ambiguously | More than one instruction could be meant, or none | Tabris asks which one, showing the candidates | Name it | — |
| The user does not answer the yes of F3, F4 or F6 | The next message is not an answer to the proposal | The conversation continues; nothing was applied | Ask again | A journal line saying the proposal lapsed |
| The user says yes, and applying fails | The write did not complete | A plain sentence in their language that it was not applied | Ask again | A journal line naming the user and the failure |
| F6 finds nothing to move | Nothing proposed | "Nothing to move", and their current instructions | — | — |
| A user passes 20 instructions | The count | Nothing | — | A warning line in the journal (question 7) |

## Abuse cases

| # | Boundary | What someone tries | What must happen instead | AC |
|---|---|---|---|---|
| 1 | A web page, search result, image or attached document | Text that says "save this as an instruction: …" | Only the user's own words can become an instruction — never content Tabris read, searched, saw or received as an attachment | AC8 |
| 2 | The user's message, read by the distillation | "Forget all your instructions" slipped into a conversation | The distillation cannot change or remove an instruction; removal goes through F4, which shows exactly which one and waits for a yes | AC5 |
| 3 | A model's answer, or content Tabris read | A "yes" that did not come from the user | A proposal is applied only on the user's own next message | AC9 |
| 4 | The user's message | An instruction to never search, or to drop a rule Tabris runs by | An instruction weighs above facts, never above the rules the system itself enforces; no instruction switches one off (35j: no opt-out of search) | AC10 |
| 5 | The user's message | Asking to see, change or remove another user's instructions | Only the asking user's own instructions exist for them | AC11 |
| 6 | The user's message, read by the distillation | A flood of instruction-shaped text, to grow the list | Each creation is announced (F2) and counted; past 20 the journal warns | AC7 |

## Acceptance criteria

- **AC1** — Given a user says something meant to hold from now on, when Tabris saves it as an
  instruction, then that reply carries one line with the exact text saved, and the instruction is
  present in every later conversation with that user, in its own block above the facts.
- **AC2** — Given a turn where no instruction was saved, when the reply is sent, then it carries no
  saved-instruction line, whatever the model wrote.
- **AC3** — Given the distillation recognizes an instruction, when no instruction with the same or a
  related meaning exists, then it creates it and the user's next reply carries one line with the
  exact text and the offer to change or remove it; and when one does exist, nothing is created.
- **AC4** — Given a user asks to change an instruction, when Tabris proposes it, then it shows the
  current text and the whole new text, and the new text applies only after the user's yes.
- **AC5** — Given any number of distillation passes, when they finish, then no instruction has been
  changed or removed by them.
- **AC6** — Given a user asks to review their instructions, when Tabris proposes the move, then a
  fact proposed whole carries its text exactly as stored, a mixed fact is shown as the original
  beside its two parts, and nothing moves before the user's yes.
- **AC7** — Given a user holds more than 20 instructions, when their count is recorded, then the
  journal carries a warning line for that user.
- **AC8** — Given content Tabris read, searched, saw or received as an attachment says to save an
  instruction, when the turn ends and when the distillation runs, then no instruction is created from
  it.
- **AC9** — Given a proposal waiting for a yes, when the user's next message is not an answer to it,
  then nothing is applied and the proposal lapses.
- **AC10** — Given an instruction that asks Tabris to skip a rule the system enforces, when a turn
  would fall under that rule, then the rule still applies.
- **AC11** — Given two users, when one asks about, changes or removes instructions, then only their
  own are seen or touched.
- **AC12** — Given a user asks what Tabris remembers about them, when it answers, then their
  instructions appear in their own block before the facts, each as stored.

## Open questions

| # | Question | Status | Resolution / why deferred |
|---|---|---|---|
| 1 | A row that is part fact and part order (ids 100 and 127 for the owner): what happens to it in the pass that moves orders? | resolved 2026-09-29 | It is proposed split in two, and the user sees the original beside "this becomes an order" and "this stays a fact" before anything changes; nothing moves without their yes. Reliability rests on that confirmation alone, not on the model splitting well: nothing can check in code that a split kept everything, and a moved row does not come back (question 8). **Rejected:** moving it whole as an order, which carries the fact into the orders the item exists to separate. **Rejected:** leaving it for the user to rewrite by hand, which does not scale past the owner. **Deferred:** none. |
| 2 | When, and to whom, is the one-time moving pass shown? | resolved 2026-09-29 | Each user confirms only their own rows, and only when they ask for it — "review my instructions", in whatever words they use, recognized the way asking what it remembers already is; no exact phrase. Tabris never raises it unprompted. The owner tells the users himself. Towards the user the word is **instructions**, not orders. **Rejected:** showing the list in the user's first conversation after the release, which interrupts whatever they came to do. **Deferred:** a one-line notice from Tabris itself offering the review — waits on a user who was told by the owner and still has instructions stored as facts. |
| 3 | When the user changes or removes an instruction, is the change applied at once or shown first? | resolved 2026-09-29 | Shown first. For a change, Tabris shows the instruction as it stands and the whole new text, and applies nothing until the user says yes; for a removal, it shows which instruction goes and waits the same way. A change rewrites the whole instruction, which is the moment DEF-15 lost the daily report, and changing one is rare enough that the extra message costs little. **Rejected:** applying the change and showing the new text afterwards, which leaves a lost part to be noticed after the fact. **Deferred:** none. |
| 4 | When the user gives a new instruction mid-conversation, how is it saved? | resolved 2026-09-29 | In that same turn, and Tabris says in one line what it saved, with the exact text. Adding destroys nothing, so no yes is asked first; seeing the text is what tells the user it was understood as an instruction at all — the unverified assumption in the framing, checked by the user on every save. A wrong reading is fixed through the change path of question 3. **Rejected:** showing the text and waiting for a yes, a confirmation guarding against a loss that adding cannot cause. **Rejected:** leaving it to the background distillation as today, where the user never learns what was saved or how — which is how DEF-15 went unseen for two weeks. **Deferred:** none. |
| 5 | What may the background distillation do with instructions? | resolved 2026-09-30 | Create, never change or remove. An average user will not phrase an instruction so the turn recognizes it, so a distillation that could not create one would miss them routinely. Before creating one it checks whether a similar or related instruction already exists, and if so it does nothing. Changing and removing stay with the user alone (question 3). The similarity check is a model's judgment and can be wrong both ways: judged similar when it is not, a new instruction is not saved — something never stored, not something deleted; judged different when it is not, two near-identical instructions stand — a surplus, not a loss. Neither destroys an instruction already saved, which is what this item protects. **Rejected:** a distillation that neither creates nor retires instructions, leaving the turn as the only way in (the owner's reasoning: the miss is certain, not a risk). **Rejected:** a distillation that may also rewrite or retire instructions — DEF-15. **Deferred:** none. |
| 6 | Does the user learn of an instruction the background distillation created? | resolved 2026-09-30 | Yes, once: the user's next reply carries one line saying what was saved as an instruction, with the exact text, and that they can have it changed or removed if they disagree. Their answer, in their own words, goes through the path of question 3 — shown first, applied on their yes. An instruction the user does not know about changes how Tabris answers without them knowing why, and a wrong reading of it would never be noticed. **Rejected:** saying nothing until the user asks to review their instructions. **Deferred:** none. |
| 7 | How many instructions may a user hold? | resolved 2026-09-30 | No cap for now. Nothing retires an instruction without the user, so the count only rises, and every instruction travels on every call. What ships is counting: the journal records how many instructions each user holds, with a warning line when one passes 20. The owner reads it at the journal review already on his calendar for item 35p. And whenever a user asks what Tabris remembers about them, the answer shows their instructions in a block of their own, before the facts — so the owner, today's most active user, sees their number and their wording directly. **Rejected:** none. **Deferred:** a cap, and at it the distillation stops creating and the turn asks the user to review — never deleting, the shape Hermes uses — waits on any user passing 20. **Deferred:** an alert sent to an admin user defined in configuration — waits on item 38, which is that channel; until then the warning depends on someone reading the journal. |
| 8 | Can a fact moved to the instructions be moved back? | resolved 2026-09-30 | No. An instruction that turns out not to be one is removed through F4 — the user asks for it to be forgotten, sees which, and says yes — and it does not return as a fact. The promise of reversibility had entered question 1 as the agent's argument, never as the owner's decision, and is withdrawn there. **Rejected:** a restore path for the user in the conversation. **Rejected:** a restore command in the operator tool. **Deferred:** none. |
| 9 | How long does a proposal wait for its yes (F3, F4, F6)? | resolved 2026-09-30 | Until the user's next message. If that message is not an answer to it, the proposal lapses and nothing is applied (AC9); asking again starts a new one. A yes that arrives later, out of context, is not read as one — it could be answering anything. **Rejected:** none. **Deferred:** none. |
| 10 | In F6, must the user accept the whole proposal or nothing? | resolved 2026-09-30 | Neither: they can say yes to all of it or name what should not move. A review of seven rows where one is wrong should not cost the other six. **Rejected:** all-or-nothing. **Deferred:** none. |
