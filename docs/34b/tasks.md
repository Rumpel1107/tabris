# Tasks — item 34b, image input

## Slices

| # | Slice | Covers | How it is verified | Done |
|---|---|---|---|---|
| 1 | See and answer an image: the Discord adapter recognizing attachments, the size and count limits checked against what the platform reports before anything is downloaded, the bytes read into memory and folded into the call as data URLs, the `attachment` column added by an idempotent migration inside `init_db`, and the `vision` role with its own timeout decided in code by `choose_role`. Persona bullet, `README.md` features and the `CONTRIBUTING.md` rules for migrations and per-role timeouts updated in the same change. | AC1, AC2, AC5, AC6, AC7, AC9, AC10, AC14 | From a phone: a photo with a question is answered about that photo, a photo with no text is answered about itself, and a typed message in the same conversation behaves exactly as before. A message carrying four images is answered on three with the notice saying so, and an image over the size limit is refused without being downloaded. The stored row shows the typed text plus the mark, and no image file exists anywhere. | ✅ verified live 2026-09-01 from a phone, all eight criteria: a screenshot answered with a question, an image sent with no text at all (its row stored zero characters and the mark), a typed message that carried no mark and changed nothing, four images answered on three with the notice naming both numbers, and an oversized one refused with its notice — leaving no row at all, which is the stored half of that criterion. Reading quality varies and the owner accepts it as normal for the tier. Which formats each provider accepts is still unverified: the code accepts anything the platform reports as an image and lets the chain decide, so an unsupported one surfaces as a generic model failure rather than a notice naming the format. |
| 2 | The image stays in view: images held in the `Session` against the position of the message that carried them, folded in when the call is built and dropped in the same step once that message leaves the window. The two places that move positions — the system message inserted on the first turn and `undo_last_turn` — adjust the image positions as they already adjust the distillation watermark. | AC3, AC4 | From a phone: a follow-up question carrying no new image is answered with the image still in view. After enough turns to push the original message out of the window, the same question is answered without claiming to see it. | ⬜ |
| 3 | The four notices: the image is gone after a restart, no model could look at it, and the two registration cases. | AC8, AC11, AC12, AC13 | The restart notice is seen live by restarting the service with a marked message still in the window, and confirmed not to repeat on the following message. The provider failure is covered by tests, optionally confirmed in development with an invalid key. The registration cases are seen on a fresh account: an image sent before registering is not looked at, and one containing written text does not answer the pending question. | ⬜ |

## Notes

- Slice 1 is usable on its own: once it lands a photo is answered. A follow-up about it simply has no image in view, which is today's behaviour, so nothing regresses while slice 2 is missing.
- Slice 2 is alone on purpose. `plan.md` names the position bookkeeping as the piece most likely to break, and it is the only slice whose failure attaches an image to the wrong message — a wrong answer that looks right. It carries tests of its own.
- Slice 3 groups the four notices because none can be triggered on demand from a phone: each needs a failure arranged first — a restart, a dead provider, an unregistered account.
- AC11 is expected to hold from slice 1 by reuse, since a provider chain that raises already reaches the model-error notice through `safe_handle_turn`. Slice 3 verifies it rather than building it; if the verification fails, the work belongs to slice 3.
- Nothing here is verifiable from the command line, which cannot send images. Every live check happens on Discord, from a phone — the same constraint item 34a worked under.
- **Read against the other phase documents.** The spec's sixth open question left the timeout to design; `plan.md` D5 resolved it by making the timeout a property of the role, with `vision` declaring forty seconds. No contradiction remains between the two.
- **Slice 1 holds the image in the `Session` from the start**, indexed by the position of the message that carried it, reading only the current turn's. Slice 2 then adds two things and rebuilds nothing: that the image survives later turns, and that the two operations moving positions adjust the images as well. The alternative — keeping it local to the turn — made slice 1 smaller at the cost of slice 2 moving where the image lives, which is plumbing rebuilt around the one slice already carrying the risk.
- **What item 34l inherits from this, and what it does not.** The adapter plumbing and the `attachment` column carry over whole, which is why `plan.md` D3 stores a word rather than a boolean. `Session.images` does not: an image stays bytes because a model has to look at it again, while a document becomes text — plain text directly, a PDF once extracted — and then lives in the history like any other text, needing no lane beside it. The `vision` role is image-only for the same reason.

---

**Exit gate**

- [x] Slices in execution order
- [x] Each slice states its verification
- [x] No slice leaves code that nothing calls
- [x] The phase documents were read against each other; contradictions resolved or recorded
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
