# Plan — item 34b, image input

## Approach

An image never becomes part of the conversation history. The history stays what it is today, a list of text turns, and the live images travel beside it inside the `Session`, each one remembered against the position of the message it arrived with. They meet the text only at the moment a call is built: the images belonging to a message still inside the window are folded into that message as base64 data URLs, and the ones whose message has scrolled out are dropped in the same step. Nothing about a turn's shape changes for the five readers that already assume text — memory distillation, the time stamp, saving, fencing and trimming.

The channel recognizes the attachments, refuses what is too large or beyond the accepted count before downloading anything, and reads the accepted bytes into memory. What reaches the database is the user's text exactly as typed, plus a mark in a new `attachment` column; the note the model reads is reconstructed when the history is built, in the same place the date stamp already is. When any image is in view the turn is answered by a new `vision` role, decided in code rather than by the router, with a longer timeout of its own.

## Coverage

| AC | Where it lives | Notes |
|---|---|---|
| AC1 | `channels/discord_ch.py` collects the attachments; `core/conversation.py` folds them into the user message when the call is built | The typed text is the question, unchanged |
| AC2 | Same path with empty text | The message carries only the image parts |
| AC3 | `Session.images`, keyed by the position of the message that carried them | A follow-up with no new image still sees the old one |
| AC4 | The same fold step drops entries whose position fell outside the window | The image has no lifetime of its own |
| AC5 | `choose_role(session, user_input)` in `core/conversation.py`, called by the adapters in place of `route_message` | Deterministic: images in view → `vision`, otherwise the router as today |
| AC6 | The adapter reads the attachment into memory and encodes it; no path writes a file | Nothing in the feature opens a file for writing |
| AC7 | `save_message(..., attachment="image")` writes the new column | The stored text is what the user typed |
| AC8 | A flag on `Session`, raised when rehydration finds a row carrying an attachment, lowered when the notice goes out with the next reply | Notice prepended by the code, in the shape the voice echo already uses |
| AC9 | The adapter keeps the first `IMAGE_MAX_COUNT` and prepends a notice naming how many were looked at | |
| AC10 | The adapter compares the size the platform reports before calling `read()` | Same shape as item 34a's duration check |
| AC11 | The provider chain raises, `handle_turn` pops the pending user message, `safe_handle_turn` returns the existing model-error notice | Nothing is stored, because the save happens after a successful reply |
| AC12 | `handle_message` drops the images when `session.user_id is None` and prepends a notice to the onboarding answer | No model looks at the image |
| AC13 | Same branch: onboarding only ever reads typed text | The pending question is asked again |
| AC14 | Every step above is conditional on an image being present | A typed message takes exactly today's path |

## Decisions

| # | Chosen | Rejected | Why |
|---|---|---|---|
| D1 | The history stays text; live images travel beside it in the session and join the text only when the call is built | A turn becomes "text + image" throughout the system | Five readers already assume a turn is text, and this project has twice been burned by changing how a turn looks — the `[1]` id prefix and the date stamp both leaked into replies |
| D2 | A core function decides the role: images in view → `vision`, otherwise the router | An override inside `handle_turn`; teaching the router a `vision` role | The router only sees text, so a follow-up about an image it cannot see would be misrouted. An override would make `role` a parameter that is sometimes ignored, which reads as a bug later. In the core, both channels inherit it and an image turn saves the router call |
| D3 | An `attachment` text column on `messages`, holding `"image"` | A marker inside the stored `content`; a boolean `has_image` | A marker in the content puts the adornment in the database, where exports, distillation and rehydration all meet it, and would need a third deterministic stripper. The text column costs the same `ALTER TABLE` as a boolean and does not shut the door on item 34l, which needs the same mark for documents |
| D4 | A flag on the session remembers the "image is gone" notice was sent | Persisting it so it is said exactly once ever | The flag costs no schema and no second write per turn. Its consequence is accepted: after another restart, a marked message still inside the window makes the notice repeat, which is true but repetitive. The cheap refinement, if it annoys, is to require the marked message to be recent |
| D5 | The timeout becomes a property of the role in `AGENT_ROLES`; `vision` declares 40 seconds | Raising `PROVIDER_TIMEOUT` for everyone; a separate constant consulted when a call carries images | A real call took 26 seconds against today's ceiling of 15, so the primary would lose almost every image turn and fall to the backup in silence. Raising it globally slows every fallback chain, which is why it was cut from 30 to 15. Tying it to the payload rather than to the role invites two roles to disagree about the same call |
| D6 | One bullet in `prompts/persona.md`: it sees images the user sends, it cannot watch video, generate images or reach a screen, and it never offers those | Leaving the persona untouched; deriving the whole self-description from the code | Three times this month the model filled a silence with what generic assistants claim, most recently offering a tester to look at his screen. What the code can derive is only the half that exists; absence has no list to derive from. The derived half became item 35e |

## New concepts

- **Rehydration** — refilling the in-memory session from the database. The conversation lives in a dictionary inside the process, so it is empty when the service starts; the first message from each person reads their last messages back and rebuilds it. It happens on a restart, on a first-ever message, and on the first message since the last start — not on the gateway reconnections the journal shows every 40-60 minutes, which leave the process untouched.
- **Data URL** — the way an image travels inside an ordinary chat call: the bytes encoded as base64 text inside the message, with no file and no upload of its own. It is why encoding inflates the payload by about a third, which is where the size limit comes from.
- **Schema migration** — the database is created by `CREATE TABLE IF NOT EXISTS`, which does nothing to a table that already exists, so a new column needs an explicit `ALTER TABLE` guarded by a check of `PRAGMA table_info`. Idempotent, so it is safe on every start, and it is the first one this project has needed.

## What this makes stale

- `prompts/persona.md` — the new bullet, in the same change as the capability, never before it: until the feature is deployed the sentence is false.
- `README.md` — the Features list, which today mentions neither voice nor images. One bullet covers both, closing an omission item 34a left.
- `CONTRIBUTING.md` — the database section gains the rule that a schema change is an additive, idempotent step inside `init_db`; the provider section gains the per-role timeout.
- `PLAN.md` item 34b — its text still promises "a vision-capable model in the `tools`/multimodal role", a role that never existed. It is replaced by the `vision` role.
- New user-facing strings in `core/strings.py`, both languages: image too large, images beyond the accepted count, the image can no longer be seen, and the image was not looked at during registration.
- New constants in `config.py`: `IMAGE_MAX_COUNT`, `IMAGE_MAX_BYTES`, and the `vision` role with its own timeout.

## Risks

- **Position bookkeeping.** Images are keyed to a message's position in the history, and two places move positions: the system message inserted at the front on the first turn of a session, and `undo_last_turn`, which removes the last two entries. Both already adjust the distillation watermark; both must adjust the image positions too, or an image silently attaches to the wrong message. This is the piece most likely to break and it is covered by tests of its own.
- **Latency.** The 26 seconds measured were not proportional to the number of images, so 40 is a ceiling and not a prediction. Falling through to the backup will show in the log as the ordinary provider warning; if it becomes common, the number moves.
- **A free link in the chain.** The second provider runs on a shared free pool, which is what refused a candidate outright during the framing. The third link exists precisely so the chain does not end at a free tier.
- **A screenshot read wrongly but plausibly** is not detectable by the system and is named in the spec as such. The mark stored with the message says an image came, so a wrong reading is correctable in the next turn before it settles into memory.

---

**Exit gate**

- [x] Every acceptance criterion has a home
- [x] Decisions record the rejected alternative
- [x] New concepts explained and understood
- [x] Stale artifacts listed
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
