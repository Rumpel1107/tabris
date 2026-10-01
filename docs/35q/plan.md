# Plan — 35q · Standing orders survive the distillation

## Approach

Instructions get a store of their own, numbered from the same counter as facts. Three ways in: the
turn saves one when the user gives it (first round, no attachment); the background distillation
creates one it recognizes, never touching those that exist, and the next reply announces it; and a
review the user asks for moves instructions out of the stored facts. Changing, removing and moving
are proposals: code writes them, the user answers in their own words, the model reads the answer as
agreement, an adjustment or neither, and only code applies — on the turn right after the proposal,
behind conditions it can check (D12). Every conversation carries the
user's instructions in a block of their own above the facts, and the memory recital shows them first.

## Coverage

| AC | Where it lives | Notes |
|---|---|---|
| AC1 | `save_instruction` tool in the turn (D9); the saved line appended by code; the instructions block in the system prompt (D11) | |
| AC2 | The 📌 line is written by code only after the write succeeded, and a line in that shape is stripped from the model's text before it is appended (D9, D14) | A claim in the model's own prose is watched, not enforced |
| AC3 | Distillation sections (D5); announcement on the next reply (D6) | |
| AC4 | `propose_instruction_change`, proposals answered in words (D7, D12) | The model reads the answer; applying is code, behind D12's conditions |
| AC5 | Separate store (D1); the retire filter accepts only fact ids (D4); instructions shown without numbers (D5) | Three fences, none in the model |
| AC6 | `review_instructions` (D10); one proposal per row (D10) | |
| AC7 | Count line whenever an instruction is created, warning past the configured value (D11, D13) | |
| AC8 | First round only, no attachment (D3); the distillation reads only the user's own text (existing since item 30a) | Residual, as the spec now states: a page Tabris quoted in an earlier reply sits in the history. Measured by slice 3's probe; shown by the 📌 line when it happens (D14) |
| AC9 | A proposal not applied or replaced on the turn right after it was made lapses at that turn's end; applying checks the owner, that it is pending, that turn, the first round and no attachment (D7, D12) | |
| AC10 | The instructions block is prompt text only; every fence that enforces a rule is code and reads no instruction | Persona line 5 already says an instruction never outranks what is true of Tabris |
| AC11 | Every read and write scoped by user; `propose_*` refuses an instruction id that is not the user's; applying refuses a proposal that is not the asking user's (D12) | |
| AC12 | The recital renders instructions, then facts, through the shared renderer (D11) | Guaranteed only when `list_facts` runs, which on the owner's account measured 0 of 10 during item 35h (2026-09-25 to 28, `docs/log.md`). Otherwise the model recites from the system prompt, where the block comes first. Watched by item 35h's journal counter, extended to instructions; item 35p decides |

## Trust boundaries and assets

What is worth taking: a user's instructions — altering them changes how Tabris answers that user
from then on, in every conversation — and another user's memory.

| Boundary | What enters | What is worth taking | Control | Answers |
|---|---|---|---|---|
| Web page, search result, image, attachment | Text that reads as an order to save an instruction | A persistent instruction planted in the user's memory | Save only in the first round of a turn with no attachment (D3); distillation reads only the user's text | AC8 |
| The user's message, read by the distillation | "Forget all your instructions" | The user's existing instructions | The distillation cannot retire an instruction (D1, D4, D5); removal is a proposal applied only on the user's own answer (D12) | AC5 |
| A model's answer | A tool call claiming consent, or text claiming a save | Applying a change without the user's yes | Tools create proposals; applying runs only behind D12's conditions; the saved and applied lines come from code, marked 📌, and the model's own 📌 lines are removed (D9, D12, D14) | AC2, AC9 |
| The user's answer to a proposal | Agreement, an adjustment, or a page's text quoted back as if it were an answer | Applying a change the user did not agree to | Read by the model; applied by code only for the proposal's owner, on the turn right after it, in that turn's first round, on a message with no attachment; every application shown to the user and journaled (D12) | AC9, AC11 |
| Tool arguments from the model | An instruction id | Another user's instruction | Every id is checked against the asking user before a proposal is made (D9) | AC11 |
| The user's own instruction text | "Never search", "ignore your rules" | Switching off a fence | Fences are code and read no instruction | AC10 |
| Distillation output | Many instruction-shaped lines | Flooding the list | Each creation announced (D6), counted, warning past the threshold (D11) | AC7 |

## Decisions

| # | Chosen | Rejected | Why | Measurement |
|---|---|---|---|---|
| D1 | Instructions live in a store of their own, apart from the facts. The distillation reads and retires facts only; instructions never reach it as something it can retire | **Rejected:** facts with a kind label. Every reader of facts would have to remember the filter, and one that forgot would put an instruction back in a merge's reach — DEF-15 again. **Deferred:** none | The protection is in how the code is shaped, not in a rule each caller keeps. DEF-6, DEF-12 and DEF-15 are three fences that each saw one shape of the problem | — |
| D2 | **Superseded by D12 (2026-10-01).** Consent by button, negotiation by conversation. Every proposal (change, removal, review) is sent as its own message with the exact text and Apply / Cancel buttons; in the review, each proposed row carries its own. The user can answer in words instead — "yes but not 103", "make it 3 news items" — and Tabris sends a new proposal with that change, whose buttons replace the previous one's; the old buttons stop working. Only a click by the user the proposal belongs to applies anything. The CLI, which has no buttons, keeps a typed yes/no | **Rejected:** a model reading the next message as yes or no — a judgment at the very point a change applies, where a misread yes changes an instruction without consent. **Rejected:** a fixed list of yes-words — brittle, and exact phrases were already turned down (spec question 2). **Deferred:** none | The owner asked for partial acceptance and suggestions, as correcting a fact already allows (`remember_fact`, `update_profile`). There the consent is only in the tool's description — an instruction to the model; here it is enforced by code. Buttons are a new concept in the project: Discord's message components, which report who clicked and which button | — |
| D3 | **Clarified 2026-10-01, for D12's same condition too:** an attachment here is an image or a document; a voice note is transcribed into the user's own words before the turn reaches the core, and is not one. **Corrected the same day:** the edge case named under "Why" works only when the model asks for both tools in one round; when it searches first and saves after, the save is refused and the distillation creates it later, as the Risks section already says. The turn may save an instruction only in its first round, and only when the message carries no attachment. A turn runs in rounds: the model asks for a tool, gets its result, goes on. Search results and fetched pages never enter the stored history — only the user's text and Tabris's replies do — so the first round has seen nothing from outside, unless the message brought an image or a file, which arrives with it. A save asked for later, or in a turn with an attachment, is refused by the code; the instruction can still be created by the distillation, which reads only the text the user wrote, and is announced (spec questions 5 and 6) | **Rejected:** relying on the saved-instruction line alone — by the time the user reads it, the instruction is active. **Deferred:** none | Answers abuse case 1 (AC8) with a check that does not depend on the model. Edge case that still works: "search X and save as an instruction that…" — both are asked for in the first round. What remains: a previous reply of Tabris's that quoted a page is in the history; the saved-instruction line is the net for that | — |
| D4 | One numbering across facts and instructions: both draw their ids from a single shared counter, so a number names one item in the user's whole memory. A row moved from facts to instructions gets a new number — its old one stays with the retired fact — and the proposal shows it | **Rejected:** two parallel numberings, where fact 5 and instruction 5 can both exist and "forget 5" is ambiguous. **Deferred:** none | Asked by the owner: the number is how a user points at something in memory, and item 35o already exists because a number can be read the wrong way. It also means the existing retire filter, which accepts only ids of the user's facts, drops an instruction's id even if the distillation proposed one | — |
| D5 | The distillation answer gains a third section, new instructions, in today's line format; and a fourth, instructions it chose not to create because a similar one exists, which the code writes to the journal. Existing instructions are shown to it for comparison without their numbers. The prompt line that today says to keep nothing about "the rules of the conversation" changes to: rules go to their own section and are not stored as facts too | **Rejected:** a structured (JSON) answer — cleaner, but it rewrites the parsing that works today for what one more section achieves. **Rejected:** showing instructions with their numbers — the distillation needs only the text to compare. **Deferred:** none | Without numbers there is nothing to point a retire at; with D4 the retire filter would drop one anyway — two fences, neither in the model. The skipped section is what makes the similarity judgment visible, as the spec's failure state requires. The prompt line is the instruction in force quoted in the framing, now asking for the right thing | — |
| D6 | An instruction the distillation created is stored as not yet announced; the next reply to that user appends one line per such instruction — exact text, and that it can be changed or removed on request — and marks them announced once the reply was sent | **Rejected:** a flag in the in-memory session, lost on every restart, and the service restarts on every deploy. **Deferred:** none | The database is the only state that survives a deploy | — |
| D7 | **Its lapse and click clauses superseded by D12 (2026-10-01); the proposals table stands.** Proposals are rows in the database: owner, kind (change, removal, move), the texts involved, and a status — pending, applied, cancelled, lapsed. Any new message from the user lapses their pending proposals before the turn runs; if the message was a suggestion, the turn makes a new proposal. A click is honoured only from the proposal's owner, on a pending proposal. The buttons carry the proposal's id, so a click after a restart is still resolved against the database; on anything not pending it answers that the proposal is no longer valid | **Rejected:** proposals held only in memory — a restart would leave buttons that fail with Discord's own error. **Deferred:** none | Lapsing on any new message is spec question 9 made mechanical: no judgment of whether the message "was an answer" | — |
| D8 | Changing an instruction retires it and inserts the new text, which therefore gets a new number; removing retires it. Nothing is edited in place or deleted | **Rejected:** editing the text in place to keep the number. **Deferred:** none | Constitution principle 8 (append-only) applies to instructions as it does to facts: every version stays, retired, which is also what explains a number that changed | — |
| D9 | **Extended by D12 (2026-10-01), which adds `apply_proposal`.** Four tools in the turn: `save_instruction` (subject to D3), `propose_instruction_change`, `propose_instruction_removal` and `review_instructions`. None of them applies a change: the first saves and its executor writes the saved line; the other three create proposals, and the model is told a proposal was sent, never that anything changed | **Rejected:** letting the model apply a change once it believes the user agreed — the pattern of `remember_fact`, where consent is only an instruction. **Deferred:** none | Keeps every applying step in code (constitution principle 1) | — |
| D10 | The review classifies the user's active facts with one `memory`-role call, using the prompt the probe measured. A row classified as an instruction is copied by code, word for word; a mixed row goes to a second call that returns its two parts, shown beside the original; a fact is left alone. One proposal per row | **Rejected:** letting the model rewrite whole rows too — it would put a rewrite where a copy is exact. **Deferred:** none | Mixed rows cannot be moved without a split (spec question 1); only they are exposed to one | 2026-09-30, `probe_kind.py` in the session scratchpad: the owner's 34 active facts, against his reading (4 instructions, 4 mixed, 26 facts), 3 rounds each at temperature 0. `deepseek-chat` 31/34 and identical in all three rounds, 1–2 s, $0.002 a call; all its disagreements over-mark (23 as mixed, 103 and 117 as mixed); no instruction was ever called a fact by any of the three models, in 9 runs. `gpt-oss-120b` 29–31/34, varied, up to 56 s, one empty verdict. `glm-5.2` 30–32/34, varied, $0.007–0.046. Total $0.077 |
| D11 | **Corrected 2026-10-01:** the count and its warning are written whenever an instruction is created, by the one function that writes them (D13) — a save in the turn and a move raise the count as much as a distillation pass, and a pass that keeps failing would otherwise never write it. The system prompt gains a `Standing instructions` block after the persona and before the facts, rendered by the same function as the facts; persona line 5, which already says a stored instruction outranks style defaults, points at it. The memory recital shows that block before the facts. Every distillation pass writes the user's instruction count to the journal, with a warning line past a configured threshold, 20 to start | **Rejected:** mixing instructions into the facts block with a label — the weighting the owner asked for is the separate block. **Deferred:** a cap (spec question 7) | Reuses the renderer the recital already trusts (item 35h) | — |
| D12 | The user answers a proposal in their own words, on every channel alike. The model reads the answer as agreement, an adjustment or neither: agreement is a call to a fifth tool, `apply_proposal`; an adjustment is a new `propose_*` call carrying the adjusted text, which replaces the proposal it answers; neither is no call at all. The code applies only when the proposal is pending and belongs to the asking user, the call comes on the turn right after the proposal was made, in that turn's first round before anything from outside was read, and on a message with no attachment. A proposal neither applied nor replaced on that turn lapses at its end. The line saying what was applied is written by the code, and every application is journaled with the reply that caused it | **Rejected:** Apply / Cancel buttons on Discord and a typed yes/no in the CLI (D2) — two paths for one decision, and a fixed answer the owner does not want to ask of users. **Rejected:** lapsing every pending proposal before the turn runs (D7) — it would discard the very answer the proposal waits for. **Deferred:** none | The owner's call, as memory corrections already work. A reply is open-ended language, which constitution principle 1 leaves to a model; who, which proposal, which turn, which round and whether anything came from outside can be written down, so they stay in code. The cost, stated when it was decided: a reply misread as agreement applies a change the user did not confirm — seen at once in the applied line, undone with one more message, and nothing is deleted (D8). It also drops Discord's message components, the newest concept in the item, and the CLI's separate path | To take before slice 5 is built: real and ambiguous replies to a proposal, in both languages, read by the `general` roster — how often it calls agreement what was not one |
| D13 | D4's shared counter is the facts table's own: the sequence SQLite already keeps for its autoincrement. An instruction takes the next number from it and advances it, in the same locked transaction as its insert, through the one function that writes instructions. `save_fact` does not change | **Rejected:** a new counter table both kinds draw from — the code of an earlier tag does not know it, so after a rollback with `deploy.sh`, which returns the code and not the database, the old `save_fact` hands out a number an instruction already holds, and one number names two things for good. **Rejected:** a counter that recomputes the highest number in both tables on each save — it prevents the next collision but not the one made while the older code was in service. **Deferred:** none | Any version of the code, this one or an earlier tag, counts from the same place, so the collision cannot happen rather than being repaired after it. It also leaves the numbering of existing facts untouched. SQLite documents that sequence as modifiable. The two conditions it rests on — a transaction that holds the write lock from reading the number to the insert, and no instruction written by any path but that function — are each asserted by a test | — |
| D14 | Every line that reports a save or an application starts with 📌 and is written by code, from a `core/strings.py` key in the user's language. Before the reply is sent, any line of the model's own text that starts with 📌 is removed, and only then does the code append its own — the strip item 35h already applies to the facts marker. `prompts/persona.md` says never to claim a save or an application, because that line is added for it | **Rejected:** detecting a false claim in the model's prose — open language, which would take a second model and still miss. **Rejected:** a line with no mark of its own — the model sees the real line in its history and can reproduce it. **Deferred:** none | A false claim in prose cannot be stopped by code (constitution principle 1); what code can make true is that the mark of a real save cannot be imitated. The user learns one rule: no 📌, nothing was saved. Chosen by the owner, the icon included, on 2026-10-01 | — |

## New concepts

- **A shared counter (D4)** — facts and instructions live apart but take their numbers from one
  source, so a number names one thing in the whole memory.
- **A proposal with a life cycle (D7, D12)** — pending until the turn that follows it applies it,
  replaces it with an adjusted one, or ends and lapses it; kept in the database so it outlives a
  restart.
- **A reply read by the model, applied by code (D12)** — the model decides what the user meant; the
  code decides, from facts it can check, whether that may be applied now.

## What this makes stale

- `core/memory_manager.py` — the distillation prompt's line on "the rules of the conversation" (D5).
- `prompts/persona.md` — line 5 points at the new block; line 19, the recital, shows instructions
  first; the new tools need the same one-line guidance the fact tools have.
- `core/db.py` — `delete_user_completely` and `get_user_records` list tables one by one: without the
  new ones, **an erased account would leave its instructions and proposals behind**, and an export
  would omit them (constitution principle 9).
- `CONTRIBUTING.md` — the architecture sketch (the system prompt now carries instructions) and the
  rule that memory writes auto-apply, which instructions no longer do.
- `README.md` — the persistent-memory bullet.
- `CHANGELOG.md`, and `docs/defects.md` DEF-15's status when the item closes.

## Risks

- **Recognising an instruction mid-conversation is unmeasured.** The probe measured the review of
  stored rows (F6), not F1 or F2. Watched, not fenced: every save is shown to the user, the count is
  in the journal, and the deferred periodic review exists for exactly this.
- **A split of a mixed row can drop a part.** Only the user's reading guards it (spec question 1).
- **An instruction may also be kept as a fact** by a distillation that ignores the new prompt line —
  a duplicate, not a loss; a later review would propose moving it.
- **The first-round rule refuses a legitimate save** when the model searches before saving; the
  distillation creates it later and announces it.
- **A review can start without the user asking** (D10, spec question 2). Only the tool's description
  holds it back; the code cannot tell "review my instructions" from "you are not listening to me".
  It costs a message of unwanted proposals, never a move, since nothing applies without agreement
  (D12). Each review is journaled with the message that started it; a tool description changes only
  after a probe (constitution principle 5). A daily cap in code was rejected: it stops a repeat, not
  the first unwanted review, and it limits a user who does want two.
- **The recital of instructions is the model's on most turns** (AC12). The code writes it only when
  `list_facts` runs; the model usually recites without it, faithfully so far. Forcing the code's path
  is item 35h's unbuilt slices 3 and 4, which item 35p decides from the journal — this item adds
  instructions to that count and builds nothing more.
- **An instruction can be saved from a page Tabris quoted in an earlier reply** (D3, AC8). It needs
  the model to save something the user's message did not give, against the persona. Measured before
  slice 3 is built; shown by the 📌 line; removed through F4. Requiring the saved text to appear in
  the user's message was rejected: the model rewords, and legitimate saves would be refused.
- **A voice note transcribed wrongly can save an instruction or agree to a proposal** (D3, D12). The
  owner reports the transcriber as often wrong; nothing has measured it. The net is the line the code
  writes with the exact text saved or applied. Measuring the transcriber is item 39b.
- **A reply misread as agreement applies a change the user did not confirm** (D12). Measured before
  the slice that builds it; seen by the user in the applied line; every application journaled.
