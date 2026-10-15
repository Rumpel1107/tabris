# Spec — 35q · Standing orders survive the distillation

> **Reopened 2026-10-02** with the widened scope (`framing.md`, amendment), and **rewritten for it
> on 2026-10-08** — questions 12 to 21. Questions 4 and 6 are superseded; everything else agreed
> before the reopening stands. **Questions 22 to 27 added on 2026-10-14:** one condition and one
> action per instruction, a repeated instruction, an instruction that orders others, and what code
> carries out of an instruction's steps and of what its reply must contain.

## Purpose and scope

A standing instruction a user gives Tabris is kept apart from the facts it remembers about them, is
created, changed or removed only when that user says yes, and is carried out: on the turns it
applies to, the steps it requires that read — a search, a page, the user's memory — run before the
reply is written, and what the reply must contain is asked of the model. Towards the user these are
**instructions**; this document uses the same word.

It does not make Tabris speak first — "every day at seven, without my writing" is item 39; until
then Tabris says so and offers what it can do (question 18). It does not guarantee what a reply
contains: an exact text, a count, a link or a section an instruction asks for is a request to the
model (question 27), and so is the quality inside it — "verify proper names". It does not clean transient,
expired or oversized facts (item 35g). It does not cap how many instructions a user may hold
(question 7).

## User flow

**F1 — Giving an instruction.**
1. The user says, in their own words, something meant to hold from now on: "from now on, shopping
   options always in Colombia", or "save this instruction: …" — a shape, never a required phrase.
2. Tabris answers the message as usual and adds a proposal: the instruction's text, reworded when
   the user's was unclear, and its three parts — when it applies, the steps it requires beyond
   writing, and what the reply must contain. Each instruction holds one condition and one action:
   a message that gives several is proposed as several, each with its own three parts. Instructions
   carry no order among them; an order or a shape the user wants for several is an instruction of
   its own, and its proposal names the instructions it orders.
3. The user answers in their own words. Agreement saves it, and that reply carries one line with
   the exact text saved; an adjustment brings a new proposal; anything else saves nothing.
4. From then on it is carried out on every turn it applies to (F7).

Four cases stop step 2 short of an ordinary proposal:
- **It contradicts an instruction the user already has.** The proposal shows both, and nothing is
  saved until the user adjusts one of them — an exception such as "except in the report" counts —
  or drops one.
- **It does what an instruction the user already has does** — under the same condition or another,
  in the same words or others. One message shows the existing instruction beside the proposed one
  with its three parts, and asks whether to replace it, keep both, or leave things as they are; the
  user may adjust the text instead.
- **It needs something Tabris cannot do yet.** Tabris says so and, when one exists, proposes an
  alternative it can carry out — "on your first message after seven" instead of "at seven"
  (invented example). When the missing capability is planned — today, only speaking first — the
  request is kept and the user is told once when it arrives.
- **It requires more steps than one turn allows.** The proposal says so and offers a smaller
  version.

**F2 — An instruction the turn did not catch.**
1. The user said something that works as an instruction without phrasing it as one, and the turn
   did not propose it.
2. Later, in the background, the distillation recognizes it. If the user already has an instruction
   with the same or a related meaning, or turned down a proposal of one before, nothing happens.
3. Otherwise the user's next reply ends with a proposal shaped as F1's, under the same cases.
   Agreement saves it. A refusal is remembered, and the distillation does not propose it again. A
   proposal the user lets pass lapses; said again later, it can be proposed again.

**F3 — Changing an instruction.**
1. The user asks, in their own words, to change one: "in the report, only 5 news items now".
2. Tabris shows the instruction as it stands and the whole new text with its three parts, under
   F1's cases, and asks for a yes. When the new text does what another instruction does, the choice
   is to apply the change and remove the other, keep both, or change nothing. When other
   instructions order this one, the same message shows each of them with its text adjusted.
3. The user answers in their own words. Agreement applies the new text; an adjustment — "make it
   6" — brings a new proposal with it, which the user answers in turn; anything else changes
   nothing.

**F4 — Removing an instruction.**
1. The user asks, in their own words, to drop one.
2. Tabris shows which instruction would go, and asks for a yes. When other instructions order this
   one, the same message shows each of them with its text adjusted.
3. The user answers in their own words. Agreement retires it, and applies the adjustments shown with
   it; anything else changes nothing.

**F5 — Seeing them.**
1. The user asks what Tabris remembers about them.
2. The answer shows their instructions in a block of their own, before the facts, each as stored.

**F6 — Reviewing what memory holds (the one-time move).**
1. The user asks, in their own words, to review their instructions.
2. Tabris looks through their stored facts and proposes: each fact that is an instruction, with its
   text exactly as stored; each fact that is part instruction and part fact, as the original beside
   "this becomes an instruction" and "this stays a fact". Each proposed instruction carries its three
   parts and is split as F1 splits one, and F1's cases for a contradiction and for a repeat apply
   to it.
3. The user answers in their own words: agreeing to all of it, naming what should not move, or
   asking for a part to be worded differently, which brings a new proposal for that part.
4. What was accepted moves; nothing else changes. When there is nothing to propose, Tabris says so
   and shows the instructions the user already has.

**F7 — An instruction carried out.**
1. A turn begins. For each of the user's instructions, whether it applies is decided: by code when
   it depends on the clock, a count or literal words — "the first message of the day", "whenever I
   say blue"; by a check of meaning when it depends on what the message is about — "when I ask for
   a product".
2. Each instruction that applies has the steps it requires that read run before the reply is
   written. A step that would change something — save a fact, change the profile — is asked of the
   model, not run (question 26).
3. What the reply must contain reaches the model with the instruction, and nothing checks it
   (question 27).
4. An instruction that does not apply has no effect on the turn.

## Failure states

| State | What the system detects | What the user sees | What the user can do | How the operator learns |
|---|---|---|---|---|
| The user agreed to a proposal, and saving or applying it failed | The write did not complete | A plain sentence in their language that it was not saved or applied | Ask again | A journal line naming the user and the failure |
| The reply claims a save that did not happen | — (the model's own words) | No 📌 line: that mark comes only from a save that completed, and a line the model writes in its shape is removed. A claim in the model's own prose can still appear; the user's rule is that without 📌 nothing was saved | Say it again | Invisible on purpose: prose cannot be checked by code. The guarantee is AC2 |
| The distillation judged a new instruction similar to an existing one, or to one the user turned down | Its own verdict | Nothing | If it mattered, say it in the conversation (F1), which never consults what was turned down | A journal line naming the user and the instruction it matched |
| The distillation proposed a near-duplicate | — | A proposal much like an instruction they already have | Turn it down | A journal line for every proposal the distillation makes |
| The distillation failed | The pass did not complete | Nothing; no instruction is touched | — | The journal line the distillation already writes on failure |
| A change or removal names an instruction ambiguously | More than one instruction could be meant, or none | Tabris asks which one, showing the candidates | Name it | — |
| The user does not answer a proposal | The next message is not an answer to it | The conversation continues; nothing was applied | Ask again; one the distillation made can come back if they say it again | A journal line saying the proposal lapsed |
| Tabris starts a review nobody asked for | — (a reading of the user's own words) | Move proposals they did not ask for; nothing moves without their agreement | Ignore them; they lapse on the next turn | A journal line for every review, with the message that started it. Question 2's promise is watched, not enforced: the code cannot tell a request to review from a complaint |
| A reply is read as agreement when it was not | — (a reading of the user's own words) | The line saying what was applied, in that same reply | Ask for it back: a change through F3, a removal by giving the instruction again | A journal line for every applied proposal, naming the proposal and the reply that applied it |
| F6 finds nothing to move | Nothing proposed | "Nothing to move", and their current instructions | — | — |
| A user passes 20 instructions | The count | Nothing | — | A warning line in the journal (question 7) |
| A new, changed or moved instruction contradicts one the user has | The check of meaning | Both instructions, and a request to adjust or drop one | Adjust either, or drop one | A journal line naming both |
| A contradiction the check missed | — | Two instructions that pull apart, and the model choosing between them | See both in the recital (F5), and change or drop one | Invisible per turn on purpose. The check's miss rate is measured before it is built and reported to the owner (question 20) |
| A new, changed or moved instruction does what one the user has does | The comparison | Both, and the choice to replace one, keep both, or leave things as they are | Choose, or adjust the text | A journal line naming both |
| A repeat the comparison missed, or one it saw where there was none | — | Missed: a proposal much like an instruction they already have. Seen wrongly: an unrelated instruction shown beside theirs | Missed: turn it down, or remove the older one through F4. Seen wrongly: keep both | Invisible per turn on purpose. Measured with the check of question 20 and reported to the owner (question 24) |
| A message is split into instructions wrongly, or two conditions or two actions are left in one | — (a model's reading) | The proposal, with the instructions as they were split | Adjust it before agreeing | Invisible on purpose: nothing in code can tell that a split kept everything; the user's agreement is the fence, as for a mixed fact (question 22) |
| A removal or a change leaves an order naming what was removed | — | The order still naming it in the recital | Change the order through F3 | Invisible on purpose: which instructions an order covers was shown in its proposal and agreed (question 25) |
| An instruction needs a capability Tabris lacks | The check of meaning, while translating it | That it cannot be done yet, and an alternative when one exists; for a planned capability, that they will be told when it arrives | Accept the alternative, or wait | A journal line naming the capability asked for |
| An instruction requires more steps than a turn allows | The count of its steps, while translating it | A smaller version proposed | Accept, adjust or drop it | The proposal's own lapse or application line |
| Instructions applying on one turn together exceed the steps a turn allows | The count | The reply, with the oldest instructions' steps run and one fixed line naming what was not reached | Ask for it | A journal line naming the user and what was skipped |
| A step an instruction requires fails | The step's own failure | The reply to their message, with one fixed line saying it could not be done now and can be asked for again | Ask for it | A journal line naming the user, the instruction and the step |
| The reply lacks something the instruction asks it to contain | — (the model's reply) | A reply without it | Ask again | Invisible per turn on purpose: nothing checks a reply (question 27). The journal says, for every instruction saved, which parts depend on the model (AC18) |
| A step the instruction requires that changes something is not done | — (the model's choice) | A reply without it — "save my weight" not saved | Ask for it | Invisible per turn on purpose: such a step is a request to the model (question 26), labelled so in the journal (AC18) |
| The check of meaning fails on a turn | Its own failure | Nothing different: instructions of meaning travel with the turn for the model to weigh, and their steps are not forced | — | A journal line naming the failure |
| The check of meaning misreads whether an instruction applies | — | A miss: the turn goes without the instruction. A false alarm: its steps run on a turn that did not need them | Ask for it, or say it did not apply | Invisible per turn on purpose. Measured before it is built: at least 9 of 10 per language on both errors, or instructions of meaning travel with every turn (question 15) |

## Abuse cases

| # | Boundary | What someone tries | What must happen instead | AC |
|---|---|---|---|---|
| 1 | A web page, search result, image or attached document | Text that says "save this as an instruction: …" | Only the user's own words can become an instruction — never content Tabris read, searched, saw or received as an attachment in that turn. A quote of such content in an earlier reply is the residual, shown by its 📌 line when it happens | AC8 |
| 2 | The user's message, read by the distillation | "Forget all your instructions" slipped into a conversation | The distillation cannot change or remove an instruction; removal goes through F4, which shows exactly which one and waits for a yes | AC5 |
| 3 | A model's answer, or content Tabris read | A "yes" that did not come from the user | A proposal is applied only on the user's own next message | AC9 |
| 4 | The user's message | An instruction to never search, or to drop a rule Tabris runs by | An instruction weighs above facts, never above the rules the system itself enforces; no instruction switches one off (35j: no opt-out of search) | AC10 |
| 5 | The user's message | Asking to see, change or remove another user's instructions | Only the asking user's own instructions exist for them | AC11 |
| 6 | The user's message, read by the distillation | A flood of instruction-shaped text, to grow the list | Nothing is saved without the user's agreement (F2), a refusal is not proposed again, and past 20 the journal warns | AC3, AC7 |
| 7 | The user's message | An instruction that demands many searches on every message, to burn the service's quota | No turn runs more steps than one turn allows; an instruction asking for more is proposed smaller | AC17 |
| 8 | A search result or page read by a step an instruction requires | Text that says "save this as an instruction" or "the user agrees" | Content a step brought in is content Tabris read: it never becomes an instruction or an agreement | AC8, AC9 |

## Acceptance criteria

- **AC1** — Given a user says something meant to hold from now on, when Tabris recognizes it, then
  it proposes the instruction's text and its three parts, saves nothing until the user agrees, and
  the reply that saves it carries one line with the exact text saved.
- **AC2** — Given any turn, when the reply is sent, then it carries a line marked 📌 naming an
  instruction saved or a proposal applied if and only if that turn saved or applied it; a line the
  model writes in that shape is removed. What the model says in its own prose is not covered: it is
  told never to claim a save, and that is watched, not enforced.
- **AC3** — Given the distillation recognizes an instruction, when no instruction with the same or a
  related meaning exists and the user has not turned one down before, then the user's next reply
  carries a proposal shaped as F1's and nothing is saved before they agree; and when one exists or
  was turned down, nothing is proposed.
- **AC4** — Given a user asks to change an instruction, when Tabris proposes it, then it shows the
  current text and the whole new text, and the new text applies only after the user's yes.
- **AC5** — Given any number of distillation passes, when they finish, then no instruction has been
  changed or removed by them.
- **AC6** — Given a user asks to review their instructions, when Tabris proposes the move, then a
  fact proposed whole carries its text exactly as stored, a mixed fact is shown as the original
  beside its two parts, and nothing moves before the user's yes.
- **AC7** — Given a user holds more than 20 instructions, when their count is recorded, then the
  journal carries a warning line for that user.
- **AC8** — Given content Tabris read, searched, saw or received as an attachment in a turn says to
  save an instruction, when that turn ends and when the distillation runs, then no instruction is
  created from it. Content Tabris quoted in an earlier reply is not covered: an instruction saved from
  it shows its 📌 line, and is removed through F4.
- **AC9** — Given a proposal waiting for a yes, when the user's next message is not an answer to it,
  then nothing is applied and the proposal lapses.
- **AC10** — Given an instruction that asks Tabris to skip a rule the system enforces, when a turn
  would fall under that rule, then the rule still applies.
- **AC11** — Given two users, when one asks about, changes or removes instructions, then only their
  own are seen or touched.
- **AC12** — Given a user asks what Tabris remembers about them, when the code writes the list, then
  their instructions appear in their own block before the facts, each as stored. When the model writes
  the list itself instead, it copies from a prompt where the instructions already come first: likely
  right, watched, not guaranteed — item 35p decides from a month of journal whether to force the code's
  path.
- **AC13** — Given an instruction that applies to a turn, when the reply is sent, then the steps it
  requires that read ran before it, or the reply carries one fixed line naming the step that
  failed; a step that would change something was not run by code, and what the reply must contain
  reached the model unchecked. Given an instruction that does not apply, then the turn runs as
  though it did not exist.
- **AC14** — Given an instruction whose condition depends on the clock, a count or literal words,
  when a turn begins, then code decides whether it applies. Given one whose condition depends on
  meaning, then a check decides it, and only once that check has measured at least 9 of 10 per
  language on both a miss and a false alarm; until then, and on any turn the check fails,
  instructions of meaning travel with the turn for the model to weigh and their steps are not
  forced.
- **AC15** — Given a new, changed or moved instruction that contradicts one the user has, when it is
  proposed, then the proposal shows both and nothing is saved until the user adjusts or drops one.
- **AC16** — Given an instruction that needs a capability Tabris lacks, when it is proposed, then
  Tabris says it cannot do it yet and proposes an alternative when one exists; and when the
  capability is planned, the request is kept and the user is told once when it arrives.
- **AC17** — Given an instruction whose steps exceed what one turn allows, when it is proposed, then
  a smaller version is offered; and given several instructions apply on one turn and together exceed
  it, then the oldest run first and the reply names, in one fixed line, what was not reached.
- **AC18** — Given an instruction is saved, when the journal records it, then it says which of its
  parts code guarantees and which depend on a model; the user is never shown this.
- **AC19** — Given a message that gives several instructions, or one that holds two conditions or
  two actions, when Tabris proposes it — given in the conversation, recognized by the distillation
  or moved by the review — then each condition and each action is proposed as an instruction of
  its own with its three parts, and nothing is saved until the user agrees.
- **AC20** — Given a new, changed or moved instruction that does what one the user has does, under
  the same condition or another, when it is proposed, then one message shows both and offers to
  replace the existing one, keep both, or leave things as they are, and nothing is saved or
  replaced until the user answers.
- **AC21** — Given an instruction that sets an order or a shape for others, when it is proposed, then
  the proposal names the instructions it orders; and given one of those is changed or removed, when
  that is proposed, then the same message shows the ordering instruction with its text adjusted,
  and one answer decides both.

## Open questions

| # | Question | Status | Resolution / why deferred |
|---|---|---|---|
| 1 | A row that is part fact and part order (ids 100 and 127 for the owner): what happens to it in the pass that moves orders? | resolved 2026-09-29 | It is proposed split in two, and the user sees the original beside "this becomes an order" and "this stays a fact" before anything changes; nothing moves without their yes. Reliability rests on that confirmation alone, not on the model splitting well: nothing can check in code that a split kept everything, and a moved row does not come back (question 8). **Rejected:** moving it whole as an order, which carries the fact into the orders the item exists to separate. **Rejected:** leaving it for the user to rewrite by hand, which does not scale past the owner. **Deferred:** none. |
| 2 | When, and to whom, is the one-time moving pass shown? | resolved 2026-09-29 | Each user confirms only their own rows, and only when they ask for it — "review my instructions", in whatever words they use, recognized the way asking what it remembers already is; no exact phrase. Tabris never raises it unprompted. The owner tells the users himself. Towards the user the word is **instructions**, not orders. **Rejected:** showing the list in the user's first conversation after the release, which interrupts whatever they came to do. **Deferred:** a one-line notice from Tabris itself offering the review — waits on a user who was told by the owner and still has instructions stored as facts. |
| 3 | When the user changes or removes an instruction, is the change applied at once or shown first? | resolved 2026-09-29 | Shown first. For a change, Tabris shows the instruction as it stands and the whole new text, and applies nothing until the user says yes; for a removal, it shows which instruction goes and waits the same way. A change rewrites the whole instruction, which is the moment DEF-15 lost the daily report, and changing one is rare enough that the extra message costs little. **Rejected:** applying the change and showing the new text afterwards, which leaves a lost part to be noticed after the fact. **Deferred:** none. |
| 4 | When the user gives a new instruction mid-conversation, how is it saved? | superseded by 12 | In that same turn, and Tabris says in one line what it saved, with the exact text. Adding destroys nothing, so no yes is asked first; seeing the text is what tells the user it was understood as an instruction at all — the unverified assumption in the framing, checked by the user on every save. A wrong reading is fixed through the change path of question 3. **Rejected:** showing the text and waiting for a yes, a confirmation guarding against a loss that adding cannot cause. **Rejected:** leaving it to the background distillation as today, where the user never learns what was saved or how — which is how DEF-15 went unseen for two weeks. **Deferred:** none. |
| 5 | What may the background distillation do with instructions? | resolved 2026-09-30 | Create, never change or remove. An average user will not phrase an instruction so the turn recognizes it, so a distillation that could not create one would miss them routinely. Before creating one it checks whether a similar or related instruction already exists, and if so it does nothing. Changing and removing stay with the user alone (question 3). The similarity check is a model's judgment and can be wrong both ways: judged similar when it is not, a new instruction is not saved — something never stored, not something deleted; judged different when it is not, two near-identical instructions stand — a surplus, not a loss. Neither destroys an instruction already saved, which is what this item protects. **Rejected:** a distillation that neither creates nor retires instructions, leaving the turn as the only way in (the owner's reasoning: the miss is certain, not a risk). **Rejected:** a distillation that may also rewrite or retire instructions — DEF-15. **Deferred:** none. |
| 6 | Does the user learn of an instruction the background distillation created? | superseded by 13 | Yes, once: the user's next reply carries one line saying what was saved as an instruction, with the exact text, and that they can have it changed or removed if they disagree. Their answer, in their own words, goes through the path of question 3 — shown first, applied on their yes. An instruction the user does not know about changes how Tabris answers without them knowing why, and a wrong reading of it would never be noticed. **Rejected:** saying nothing until the user asks to review their instructions. **Deferred:** none. |
| 7 | How many instructions may a user hold? | resolved 2026-09-30 | No cap for now. Nothing retires an instruction without the user, so the count only rises, and every instruction travels on every call. What ships is counting: the journal records how many instructions each user holds, with a warning line when one passes 20. The owner reads it at the journal review already on his calendar for item 35p. And whenever a user asks what Tabris remembers about them, the answer shows their instructions in a block of their own, before the facts — so the owner, today's most active user, sees their number and their wording directly. **Rejected:** none. **Deferred:** a cap, and at it the distillation stops creating and the turn asks the user to review — never deleting, the shape Hermes uses — waits on any user passing 20. **Deferred:** an alert sent to an admin user defined in configuration — waits on item 38, which is that channel; until then the warning depends on someone reading the journal. |
| 8 | Can a fact moved to the instructions be moved back? | resolved 2026-09-30 | No. An instruction that turns out not to be one is removed through F4 — the user asks for it to be forgotten, sees which, and says yes — and it does not return as a fact. The promise of reversibility had entered question 1 as the agent's argument, never as the owner's decision, and is withdrawn there. **Rejected:** a restore path for the user in the conversation. **Rejected:** a restore command in the operator tool. **Deferred:** none. |
| 9 | How long does a proposal wait for its yes (F3, F4, F6)? | resolved 2026-09-30 | Until the user's next message. If that message is not an answer to it, the proposal lapses and nothing is applied (AC9); asking again starts a new one. A yes that arrives later, out of context, is not read as one — it could be answering anything. **Rejected:** none. **Deferred:** none. |
| 10 | In F6, must the user accept the whole proposal or nothing? | resolved 2026-09-30 | Neither: they can say yes to all of it or name what should not move. A review of seven rows where one is wrong should not cost the other six. **Rejected:** all-or-nothing. **Deferred:** none. |
| 11 | How does the user answer a proposal (F3, F4, F6)? | resolved 2026-10-01 | In their own words, on every channel alike — no button and no required yes/no. The reply is read as agreement, an adjustment or neither; an adjustment brings a new proposal, and only agreement applies anything. A reply misread as agreement shows at once in the line saying what was applied, and is undone with one more message; nothing is deleted. **Rejected:** buttons on Discord with a typed yes/no in the CLI — two paths for one decision, and a fixed answer the owner does not want to ask of users. **Deferred:** none. |
| 12 | Is an instruction given in the conversation saved at once, or proposed first? | resolved 2026-10-02 | Proposed first, and saved on the user's agreement: the user sees the text and its three parts — when it applies, its steps, what the reply must contain — and agrees, adjusts or turns it down in words, as question 11 answers any proposal. The translation decides what code enforces on every turn, so a wrong reading now costs more than the surplus row question 4 weighed. The owner's call, in the framing's amendment. **Rejected:** saving at once and showing the text after (question 4's answer). **Deferred:** none. |
| 13 | May the distillation still create an instruction without asking, now that creating one is a proposal? | resolved 2026-10-07 | It still recognizes them, and proposes: nothing is stored before the user agrees. The proposal ends the user's next reply. A refusal is remembered — the distillation compares against what was turned down as it compares against what exists — so it is not proposed again; a proposal let pass lapses (question 9) and can come back if the user says it again. The conversation never consults what was turned down: a user who changed their mind says it again (F1). Narrows question 5's "create" to "propose". **Rejected:** remembering nothing, so a turned-down instruction can come back on every pass. **Rejected:** keeping an ignored proposal pending and repeating it on every reply until answered — a line on every reply, and an exception to question 9. **Deferred:** none. |
| 14 | Is there a fixed way to give an instruction? | resolved 2026-10-07 | No. "Save this instruction: …" is the shape, recognized the way asking what Tabris remembers already is, never as an exact phrase. **Rejected:** a command, `/instruccion: …`, read by code and ignoring what was turned down — proposed by the owner and withdrawn the same day; it would have been the first command in Tabris. **Deferred:** none. |
| 15 | Does every turn carry every instruction, or only those that apply to it? | resolved 2026-10-07 | Only those that apply, where that is decided reliably. A condition on the clock, a count or literal words is decided by code, so those travel only when they hold. A condition of meaning is decided by a check that must measure at least 9 of 10 per language on both a miss and a false alarm — the floor the owner set for the report on 2026-10-02; below it, instructions of meaning travel with every turn and their steps are not forced. Which check, and the candidates the owner asked to have measured side by side, are the Design's (`plan.md`, header). **Rejected:** 10 of 10 per language — likely out of reach, leaving every instruction of meaning on every turn. **Deferred:** none. |
| 16 | Is the user told which parts of an instruction code guarantees? | resolved 2026-10-07 | No. It is information for the operator: the journal records it for every instruction saved (AC18), and the owner is told it whenever a mechanism is put to him. A user needs the highest reliability, not its label. Corrects the framing's amendment, which said the user could be told. **Rejected:** a short mark on each part of every proposal. **Rejected:** telling it only when the user asks. **Deferred:** none. |
| 17 | What does the user see when a step an instruction requires fails? | resolved 2026-10-07 | The reply to their message, with one fixed line saying it could not be done now and can be asked for again — as Tabris already does when it cannot read the memory or has no confirmed source. Code knows the step failed; nothing is guessed. **Rejected:** saying nothing and leaving it to the journal — the user cannot tell a failed step from a lost instruction, which is how DEF-15 went unseen. Writing what the reply requires without the step's data is not an option: it is the 2026-10-02 report. **Deferred:** none. |
| 18 | What happens to an instruction that needs something Tabris cannot do — speaking first, sending an email? | resolved 2026-10-07 | Tabris says it cannot do it yet and, when one exists, proposes an alternative it can carry out. Only when the capability is planned — today, speaking first (item 39) — is the request kept and the user told once when it arrives. **Rejected:** saving it as given, with a line saying how it is carried out until item 39 exists. **Rejected:** saving it and saying nothing. **Rejected:** promising the notice for any capability, including ones nothing plans to build. **Deferred:** a notice to active users whenever a capability ships, which would cover the rest — item 54, behind item 39; the owner's plan, not a priority. |
| 19 | What about an instruction that requires many steps on every message? | resolved 2026-10-07 | A cap on the steps instructions may require in one turn. An instruction above it is proposed smaller; when several apply together and exceed it, the oldest run first and the rest are named in one fixed line. The number is set in the Design, from the steps the owner's own report requires. Without a cap, a turn that passes its existing limit on tool rounds fails whole, and the user gets no answer to what they asked. **Rejected:** no cap at creation, only the turn's limit — the user learns of it on every turn instead of once. **Rejected:** no cap. **Deferred:** none. |
| 20 | What happens when two instructions contradict each other? | resolved 2026-10-08 | They never stand together. A new, changed or moved instruction is compared with the existing ones; when it contradicts one, the proposal shows both and nothing is saved until the user adjusts one — an exception counts — or drops one. The model is never left to choose. The comparison is a model's judgment: its miss rate is measured with the check of question 15 and reported to the owner. **Rejected:** keeping both, the newest winning on a turn they collide — it leaves the choice to the model. **Rejected:** not handling it. **Deferred:** none. |
| 21 | What happens when the reply lacks what an instruction requires? | superseded by 27 | Where code can check the part — a count, a link, a literal text — a reply missing it is rewritten once, with what is missing named; still missing, it is sent with one fixed line naming what could not be met, and journaled. A part code cannot check stays a request to the model. **Rejected:** no rewrite. **Rejected:** rewriting until it passes, up to a maximum — each round adds a model call's wait. **Deferred:** none. |
| 22 | Can one instruction hold more than one condition? | resolved 2026-10-14 | No. A message that gives several, or one sentence that bundles two — "every morning the news, and when I ask about parts, search in Colombia" (invented) — is proposed as several instructions, each with its three parts, and nothing is saved without the user's agreement. It applies wherever an instruction is translated: given in the conversation (F1), proposed by the distillation (F2), moved by the review (F6). Where one instruction ends and the next begins is a model's reading, unmeasured; nothing in code can tell that a split kept everything, so the user's agreement is the fence, as for a mixed fact (question 1). **Rejected:** splitting in the distillation only, the owner's first proposal — it leaves out the commonest way in, the user saying it directly. **Deferred:** none. |
| 23 | Does an instruction do one thing, and what holds several together? | resolved 2026-10-14 | One action per instruction, with no order among them. A morning report of the weather, the news and an exchange rate (invented) is three instructions under one condition; they land in one reply because Tabris answers each message once, and only speaking first (item 39) needs a rule to group them. An order or a shape the user wants for several is an instruction of its own, there only when asked for. Smaller instructions make a repeat easier to recognize (question 24), at the cost of more of them, so question 7's warning comes sooner. **Rejected:** splitting only where the user could want to drop one part and keep the other, so a report wanted as a block stays one — a guess at what the user might want, harder to apply and to compare. **Rejected:** splitting by condition only (question 22), which leaves unrelated actions together under one condition. **Deferred:** none. |
| 24 | What happens to an instruction that does what one the user already has does? | resolved 2026-10-14 | One message shows the existing instruction beside the proposed one with its three parts, and asks whether to replace it, keep both, or leave things as they are; the user answers in their own words, and may adjust the text instead. Same condition or another, same words or others, the case is the same. It applies to a new, a changed and a moved instruction, as the check for a contradiction does (question 20): one comparison, the same in every way in. For a change, replacing means the other instruction is removed. The distillation still proposes nothing when a similar one exists (question 13). Whether two instructions do the same is a model's reading, measured with question 20's check; misread either way, the user sees it in the proposal — a missed repeat arrives as a near-duplicate to turn down, a wrongly seen one is kept with "keep both". **Rejected:** saying it is already held and saving nothing, proposing a change only when the condition differs — a misread repeat would cost the user an insistence. **Rejected:** two messages, asking replace-or-keep first and showing the proposal after — two answers, and a lapse (question 9) between them. **Rejected:** catching only an identical repeat, leaving two instructions with one action to be removed one by one. **Rejected:** not handling it, so saying an instruction again stores a copy. **Deferred:** none. |
| 25 | What happens to an instruction that orders others when one of them is changed or removed? | resolved 2026-10-14 | It is adjusted with it. An ordering instruction names the instructions it orders, shown in its proposal when it is created; changing or removing one of them shows, in the same message, each instruction that orders it with its text adjusted, and one answer decides all of them. Which instructions an order covers was agreed by the user at creation, so finding them later needs no reading of meaning; the adjusted text is a model's, agreed before it is saved, and unmeasured. **Rejected:** an order that only arranges what is present and is never adjusted — its text keeps naming what was removed, and that the model leaves it out is a request, not a guarantee. **Rejected:** leaving it to the user, who would see a removed part come back without knowing why. **Deferred:** none. |
| 26 | May a step an instruction requires change something? | resolved 2026-10-14 | Not for now. Code runs only steps that read: a search, opening a page, reading the user's memory. A step that would save or forget a fact, change the profile or create a link code stays a request to the model, as those tools work today — "whenever I tell you my weight, save it" (invented) is kept as text the model weighs. A forced write on a false alarm of the check of meaning would change the user's data unasked; a forced read costs a search. The journal labels such a step as depending on the model (AC18). **Rejected:** none. **Deferred:** forced steps that change something — the owner's "for now"; waits on a real instruction that needs one. |
| 27 | What does code do with what the reply must contain? | resolved 2026-10-14 | Nothing, in the first version: it reaches the model with the instruction and is not checked. Code could place an exact text at the start or the end of a reply, count lines or list items, and compare links with what the turn searched or opened; it could not write the content under a section heading, so grouping a reply into sections would stay with the model whatever was built. None of these has a real instruction behind it today. The journal says, for every instruction saved, which parts depend on the model (AC18), and that is where a real need shows. Supersedes question 21. **Rejected:** a model writing code at run time to check a reply — a user's text would end up running on the server, and nothing would verify that code. **Rejected:** a second model reviewing each reply — one more call per turn, reliable only as far as measured. **Deferred:** an exact text placed by code at the start or the end, and checks of a count, a length and section headings — each waits on a real instruction that needs it, seen in the journal. **Deferred:** checking that a link came from the turn's own sources — items 35k and 35l, which own a claim the turn never received. |

---

**Exit gate**

- [x] Acceptance criteria in Given/When/Then form
- [x] Failure states enumerated, not implied
- [x] Every boundary where outside data enters has an abuse case, and each is an acceptance criterion
- [x] Every open question resolved or explicitly deferred
- [x] No technical decisions leaked into this document
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down — questions 12 to 21 on 2026-10-07 and 08; three consequences drawn from them on 2026-10-09: F6 translating a moved instruction into its three parts, a failed check of meaning carrying instructions without forcing their steps, and abuse case 8; questions 22 to 27 on 2026-10-14
