# Plan — 35q · Standing orders survive the distillation

## Approach

Instructions get a store of their own, numbered from the same counter as facts. Three ways in: the
turn saves one when the user gives it (first round, no attachment); the background distillation
creates one it recognizes, never touching those that exist, and the next reply announces it; and a
review the user asks for moves instructions out of the stored facts. Changing, removing and moving
are proposals: code writes them as their own message with Apply / Cancel buttons, the user may
answer in words to get a revised proposal, and only a click applies. Every conversation carries the
user's instructions in a block of their own above the facts, and the memory recital shows them first.

## Coverage

| AC | Where it lives | Notes |
|---|---|---|
| AC1 | `save_instruction` tool in the turn (D9); the saved line appended by code; the instructions block in the system prompt (D11) | |
| AC2 | The saved line is written by the save's own executor, only after the write succeeded (D9) | The model's text is never the source of the line |
| AC3 | Distillation sections (D5); announcement on the next reply (D6) | |
| AC4 | `propose_instruction_change`, proposals and buttons (D2, D7) | Apply is a click, never a model call |
| AC5 | Separate store (D1); the retire filter accepts only fact ids (D4); instructions shown without numbers (D5) | Three fences, none in the model |
| AC6 | `review_instructions` (D10); one proposal per row (D2) | |
| AC7 | Count line on every distillation pass, warning past the configured value (D11) | |
| AC8 | First round only, no attachment (D3); the distillation reads only the user's own text (existing since item 30a) | |
| AC9 | Any new message from the user lapses their pending proposals; a click checks it is the proposal's owner and that it is still pending (D7) | |
| AC10 | The instructions block is prompt text only; every fence that enforces a rule is code and reads no instruction | Persona line 5 already says an instruction never outranks what is true of Tabris |
| AC11 | Every read and write scoped by user; `propose_*` refuses an instruction id that is not the user's; a click by anyone else is refused (D7) | |
| AC12 | The recital renders instructions, then facts, through the shared renderer (D11) | |

## Trust boundaries and assets

What is worth taking: a user's instructions — altering them changes how Tabris answers that user
from then on, in every conversation — and another user's memory.

| Boundary | What enters | What is worth taking | Control | Answers |
|---|---|---|---|---|
| Web page, search result, image, attachment | Text that reads as an order to save an instruction | A persistent instruction planted in the user's memory | Save only in the first round of a turn with no attachment (D3); distillation reads only the user's text | AC8 |
| The user's message, read by the distillation | "Forget all your instructions" | The user's existing instructions | The distillation cannot retire an instruction (D1, D4, D5); removal is a proposal applied by a click | AC5 |
| A model's answer | A tool call claiming consent, or text claiming a save | Applying a change without the user's yes | Tools only create proposals; applying happens in the click handler; the saved line comes from the executor (D7, D9) | AC2, AC9 |
| A button click | A click on a proposal | Approving someone else's change | The clicker must be the proposal's owner, and the proposal pending and not lapsed (D7) | AC9, AC11 |
| Tool arguments from the model | An instruction id | Another user's instruction | Every id is checked against the asking user before a proposal is made (D9) | AC11 |
| The user's own instruction text | "Never search", "ignore your rules" | Switching off a fence | Fences are code and read no instruction | AC10 |
| Distillation output | Many instruction-shaped lines | Flooding the list | Each creation announced (D6), counted, warning past the threshold (D11) | AC7 |

## Decisions

| # | Chosen | Rejected | Why | Measurement |
|---|---|---|---|---|
| D1 | Instructions live in a store of their own, apart from the facts. The distillation reads and retires facts only; instructions never reach it as something it can retire | **Rejected:** facts with a kind label. Every reader of facts would have to remember the filter, and one that forgot would put an instruction back in a merge's reach — DEF-15 again. **Deferred:** none | The protection is in how the code is shaped, not in a rule each caller keeps. DEF-6, DEF-12 and DEF-15 are three fences that each saw one shape of the problem | — |
| D2 | Consent by button, negotiation by conversation. Every proposal (change, removal, review) is sent as its own message with the exact text and Apply / Cancel buttons; in the review, each proposed row carries its own. The user can answer in words instead — "yes but not 103", "make it 3 news items" — and Tabris sends a new proposal with that change, whose buttons replace the previous one's; the old buttons stop working. Only a click by the user the proposal belongs to applies anything. The CLI, which has no buttons, keeps a typed yes/no | **Rejected:** a model reading the next message as yes or no — a judgment at the very point a change applies, where a misread yes changes an instruction without consent. **Rejected:** a fixed list of yes-words — brittle, and exact phrases were already turned down (spec question 2). **Deferred:** none | The owner asked for partial acceptance and suggestions, as correcting a fact already allows (`remember_fact`, `update_profile`). There the consent is only in the tool's description — an instruction to the model; here it is enforced by code. Buttons are a new concept in the project: Discord's message components, which report who clicked and which button | — |
| D3 | The turn may save an instruction only in its first round, and only when the message carries no attachment. A turn runs in rounds: the model asks for a tool, gets its result, goes on. Search results and fetched pages never enter the stored history — only the user's text and Tabris's replies do — so the first round has seen nothing from outside, unless the message brought an image or a file, which arrives with it. A save asked for later, or in a turn with an attachment, is refused by the code; the instruction can still be created by the distillation, which reads only the text the user wrote, and is announced (spec questions 5 and 6) | **Rejected:** relying on the saved-instruction line alone — by the time the user reads it, the instruction is active. **Deferred:** none | Answers abuse case 1 (AC8) with a check that does not depend on the model. Edge case that still works: "search X and save as an instruction that…" — both are asked for in the first round. What remains: a previous reply of Tabris's that quoted a page is in the history; the saved-instruction line is the net for that | — |
| D4 | One numbering across facts and instructions: both draw their ids from a single shared counter, so a number names one item in the user's whole memory. A row moved from facts to instructions gets a new number — its old one stays with the retired fact — and the proposal shows it | **Rejected:** two parallel numberings, where fact 5 and instruction 5 can both exist and "forget 5" is ambiguous. **Deferred:** none | Asked by the owner: the number is how a user points at something in memory, and item 35o already exists because a number can be read the wrong way. It also means the existing retire filter, which accepts only ids of the user's facts, drops an instruction's id even if the distillation proposed one | — |
| D5 | The distillation answer gains a third section, new instructions, in today's line format; and a fourth, instructions it chose not to create because a similar one exists, which the code writes to the journal. Existing instructions are shown to it for comparison without their numbers. The prompt line that today says to keep nothing about "the rules of the conversation" changes to: rules go to their own section and are not stored as facts too | **Rejected:** a structured (JSON) answer — cleaner, but it rewrites the parsing that works today for what one more section achieves. **Rejected:** showing instructions with their numbers — the distillation needs only the text to compare. **Deferred:** none | Without numbers there is nothing to point a retire at; with D4 the retire filter would drop one anyway — two fences, neither in the model. The skipped section is what makes the similarity judgment visible, as the spec's failure state requires. The prompt line is the instruction in force quoted in the framing, now asking for the right thing | — |
| D6 | An instruction the distillation created is stored as not yet announced; the next reply to that user appends one line per such instruction — exact text, and that it can be changed or removed on request — and marks them announced once the reply was sent | **Rejected:** a flag in the in-memory session, lost on every restart, and the service restarts on every deploy. **Deferred:** none | The database is the only state that survives a deploy | — |
| D7 | Proposals are rows in the database: owner, kind (change, removal, move), the texts involved, and a status — pending, applied, cancelled, lapsed. Any new message from the user lapses their pending proposals before the turn runs; if the message was a suggestion, the turn makes a new proposal. A click is honoured only from the proposal's owner, on a pending proposal. The buttons carry the proposal's id, so a click after a restart is still resolved against the database; on anything not pending it answers that the proposal is no longer valid | **Rejected:** proposals held only in memory — a restart would leave buttons that fail with Discord's own error. **Deferred:** none | Lapsing on any new message is spec question 9 made mechanical: no judgment of whether the message "was an answer" | — |
| D8 | Changing an instruction retires it and inserts the new text, which therefore gets a new number; removing retires it. Nothing is edited in place or deleted | **Rejected:** editing the text in place to keep the number. **Deferred:** none | Constitution principle 8 (append-only) applies to instructions as it does to facts: every version stays, retired, which is also what explains a number that changed | — |
| D9 | Four tools in the turn: `save_instruction` (subject to D3), `propose_instruction_change`, `propose_instruction_removal` and `review_instructions`. None of them applies a change: the first saves and its executor writes the saved line; the other three create proposals, and the model is told a proposal was sent, never that anything changed | **Rejected:** letting the model apply a change once it believes the user agreed — the pattern of `remember_fact`, where consent is only an instruction. **Deferred:** none | Keeps every applying step in code (constitution principle 1) | — |
| D10 | The review classifies the user's active facts with one `memory`-role call, using the prompt the probe measured. A row classified as an instruction is copied by code, word for word; a mixed row goes to a second call that returns its two parts, shown beside the original; a fact is left alone. One proposal per row | **Rejected:** letting the model rewrite whole rows too — it would put a rewrite where a copy is exact. **Deferred:** none | Mixed rows cannot be moved without a split (spec question 1); only they are exposed to one | 2026-09-30, `probe_kind.py` in the session scratchpad: the owner's 34 active facts, against his reading (4 instructions, 4 mixed, 26 facts), 3 rounds each at temperature 0. `deepseek-chat` 31/34 and identical in all three rounds, 1–2 s, $0.002 a call; all its disagreements over-mark (23 as mixed, 103 and 117 as mixed); no instruction was ever called a fact by any of the three models, in 9 runs. `gpt-oss-120b` 29–31/34, varied, up to 56 s, one empty verdict. `glm-5.2` 30–32/34, varied, $0.007–0.046. Total $0.077 |
| D11 | The system prompt gains a `Standing instructions` block after the persona and before the facts, rendered by the same function as the facts; persona line 5, which already says a stored instruction outranks style defaults, points at it. The memory recital shows that block before the facts. Every distillation pass writes the user's instruction count to the journal, with a warning line past a configured threshold, 20 to start | **Rejected:** mixing instructions into the facts block with a label — the weighting the owner asked for is the separate block. **Deferred:** a cap (spec question 7) | Reuses the renderer the recital already trusts (item 35h) | — |

## New concepts

- **A shared counter (D4)** — facts and instructions live apart but take their numbers from one
  source, so a number names one thing in the whole memory.
- **Message buttons (D2)** — Discord lets a bot attach buttons to a message; a click reaches the bot
  saying who clicked and which button, with no text to interpret.
- **A proposal with a life cycle (D7)** — pending until clicked, cancelled, or lapsed by the user's
  next message; kept in the database so it outlives a restart.

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
- **Buttons are new to the project.** A slice verifies them live on Discord before anything depends
  on them.
