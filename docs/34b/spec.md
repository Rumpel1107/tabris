# Spec — item 34b, image input

## Purpose and scope

A photograph or screenshot sent to Tabris on Discord is looked at and answered like any other message, so the user can show a screen instead of retyping it. The image stays in view for the rest of the conversation window it arrived in, so follow-up questions about it work. Nothing about a typed message changes.

It deliberately does not generate images, does not accept video, does not exist on the command line, and never writes the image to disk.

## User flow

1. The user sends a message carrying one or more images, with or without text.
2. Whatever the user typed alongside is the question; with nothing typed, the image alone is the message.
3. Tabris looks at the images and answers.
4. The images stay in view for as long as the message carrying them stays in the conversation window — the same window that already bounds the history, with no separate lifetime of their own.
5. While an image is still in view, a follow-up question about it is answered with the image still visible.
6. Once that message falls out of the window, the images go with it.
7. What is stored as the user's message is the text they typed plus a note that an image came with it. The image itself is never stored.

## Failure states

| State | What the system detects | What the user sees | What the user can do |
|---|---|---|---|
| More images than the accepted count | The number of images on the message | The answer covers the first ones, with a notice saying how many were looked at | Send the rest in another message |
| An image larger than the accepted size | The size reported with the message, before anything is downloaded or sent | A notice that the image is too large, stating the limit | Send a smaller one; nothing was spent and nothing was stored |
| No model could look at the image | Every provider in the chain failed | A notice that it was a technical problem, inviting a retry | Send it again, or describe it in words |
| The image is gone after a restart | The stored message says an image came with it, and no image is in view | Told once, on the first message after it happens, that the image can no longer be seen | Send it again if it still matters |
| An image sent before registration is finished | The person has no profile yet | The registration continues on whatever they typed, and they are told the image was not looked at | Answer the pending question in writing |
| The image is read wrongly but plausibly | Nothing — this is not detectable | An answer that sounds confident | Correct it in the next message, before it settles into memory |

A failure in the second or third state stores nothing: no user message, no reply, no memory. The turn did not happen.

## Acceptance criteria

- **AC1** — Given a registered user, when they send an image with text, then Tabris answers the text as a question about that image.
- **AC2** — Given a registered user, when they send an image with no text, then Tabris answers about the image itself.
- **AC3** — Given an image still inside the conversation window, when the user asks a follow-up carrying no new image, then the answer is given with that image still in view.
- **AC4** — Given an image whose message has fallen out of the conversation window, when the user asks about it, then it is no longer in view and Tabris does not claim to see it.
- **AC5** — Given any image in view, when a turn is answered, then it is answered by a model that can see; a turn with no image in view is unaffected.
- **AC6** — Given any image at all, when the turn completes, then the image exists nowhere on disk.
- **AC7** — Given an image, when the user's message is stored, then what is stored is their text plus a note that an image came with it, never the image.
- **AC8** — Given a restart that leaves a stored note whose image is gone, when the user sends their next message, then they are told once that the image can no longer be seen, and later messages do not repeat it.
- **AC9** — Given more images than the accepted count, when the message is sent, then the accepted number are looked at and the user is told how many.
- **AC10** — Given an image over the accepted size, when the message is sent, then it is refused with a notice, without being downloaded or sent to any model, and nothing is stored.
- **AC11** — Given every vision provider failing, when the user sends an image, then they are told it was a technical problem, and nothing is stored.
- **AC12** — Given a person who has not finished registering, when they send an image, then no model looks at it and the registration continues on the text they typed.
- **AC13** — Given a person who has not finished registering, when they send an image containing written text and type nothing, then the pending registration question is asked again and the text inside the image is not used as an answer.
- **AC14** — Given a typed message with no image, when Tabris answers, then nothing about its behaviour changes: no notice, no change of model, no note stored.

## Open questions

| # | Question | Status | Resolution / why deferred |
|---|---|---|---|
| 1 | How long does an image stay in view? | resolved | It has no lifetime of its own: it lives and dies with the message carrying it, inside the window that already bounds the history. Chosen over a separate limit because a new number would have to be guessed, and an image outliving its own message has no meaning. |
| 2 | How many images per message? | resolved | Three. Not a preference — it is the largest number every model in the chain accepts, verified with a real call; a message the primary could serve but a fallback could not would break the fallback exactly when it is needed. |
| 3 | What size per image? | resolved | Five megabytes, derived the same way: the whole request is capped at twenty by one provider in the chain, and encoding inflates it by a third, so three images at this size sit just inside that ceiling. |
| 4 | Is text inside an image ever used to answer a registration question? | resolved | No. Registration by image is not accepted at all, even when the image plainly contains the answer. Only what the person types counts. Revisit if somebody actually asks for it. |
| 5 | Who tells the user the image is gone — the model, or the system? | resolved | The system, once, deterministically. An instruction in the persona competes with thirty-five others and has already lost twice this month; the notice must not depend on the model remembering. Whether a later question depends on the lost image is left to the model, because that is judgement. |
| 6 | Does an image call need a longer timeout than a text call? | deferred | Raised by a real call that took twenty-six seconds against a fifteen-second ceiling, which would silently fall through to the backup. It is a property of the call, so it belongs with the design of the call, not with behaviour seen from outside. |
| 7 | Does this work on Telegram? | deferred | Item 34d reuses whatever this builds; nothing here may assume Discord beyond the channel adapter. |

---

**Exit gate**

- [x] Acceptance criteria in Given/When/Then form
- [x] Failure states enumerated, not implied
- [x] Every open question resolved or explicitly deferred
- [x] No technical decisions leaked into this document
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
