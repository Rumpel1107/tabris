# Spec — item 34a, audio input

## Purpose and scope

A voice message sent to Tabris on Discord becomes text and is answered like any other message, so the user can reach it while driving, walking or with their hands otherwise busy. The transcript is shown back before the answer, and the answer hangs off the voice message it belongs to.

It deliberately does not speak its answer (item 53), does not accept audio that is not a voice message recorded in Discord, and does not exist on the command line, which cannot send audio.

## User flow

1. The user records a voice message in Discord and sends it.
2. Tabris recognizes it as a voice message and checks its length before doing anything else.
3. The audio is turned into text.
4. Tabris answers as it would to that same sentence typed, opening with a short line stating what it understood.
5. The answer arrives quoting the voice message, so the transcript and the reply sit visibly attached to the audio they came from.
6. The transcript is stored as the user's own message: it joins the conversation history and is read by the memory pass, exactly as typed text is.

## Failure states

| State | What the system detects | What the user sees | What the user can do |
|---|---|---|---|
| Audio longer than the accepted length | The duration reported with the message, before anything is downloaded or transcribed | A notice that the audio is too long, stating the limit | Record a shorter one; nothing was spent and nothing was stored |
| Transcription service unavailable, out of quota, or erroring | The call fails or returns no result | A notice that the audio could not be processed for a technical reason, inviting a retry | Send the same audio again, or type it |
| Audio carries no speech | The returned text holds no letters once spacing and punctuation are ignored | A notice that nothing was heard in the recording | Record it again — retrying the same file would fail identically |
| The answer cannot be attached to the voice message | Quoting fails, for instance because the original message is gone | Nothing unusual: the answer arrives as an ordinary message | Nothing; the reply was delivered |
| The transcript is wrong but plausible | Nothing — this is not detectable | The opening line states what Tabris understood | Correct it in the next message, before it settles into memory |

A failure in any of the first three states stores nothing: no user message, no reply, no memory. The turn did not happen.

## Acceptance criteria

- **AC1** — Given a voice message under the length limit, when it is sent, then Tabris answers it as if the same words had been typed, and the answer begins by stating what it understood.
- **AC2** — Given a voice message, when Tabris answers, then the answer quotes that voice message; and given quoting fails, then the answer is delivered anyway as an ordinary message.
- **AC3** — Given an audio longer than four minutes, when it is sent, then Tabris says so immediately, without transcribing it, and nothing is stored.
- **AC4** — Given an ordinary audio file attached to a message rather than a voice message recorded in Discord, when it is sent, then it is treated as it is today and no transcription happens.
- **AC5** — Given the transcription service fails, when the user sends a voice message, then they are told it was a technical problem and invited to retry, and nothing is stored.
- **AC6** — Given a recording holding no speech, when it is transcribed, then the user is told nothing was heard, and nothing is stored.
- **AC7** — Given a person who has not finished registering, when they send a voice message, then the registration receives its text as though they had typed it.
- **AC8** — Given a successful transcription, when the turn completes, then the transcript is stored as the user's message and is visible to the memory pass like any typed text.
- **AC9** — Given a typed message, when Tabris answers, then nothing about its appearance changes: no quoting and no opening line.

## Open questions

| # | Question | Status | Resolution / why deferred |
|---|---|---|---|
| 1 | Which of the provider's two transcription models is used | deferred | A technical choice with no user-visible difference beyond speed; belongs in the plan. |
| 2 | Whether the user's stored language is passed as a hint to the transcriber | deferred | Same reason: it changes accuracy, not the flow. Decided in the plan, where the trade-off with someone speaking a second language can be weighed. |
| 3 | Where the four-minute limit is enforced if a future channel reports duration differently | deferred | Telegram is item 34d; the limit lives with the shared transcription module and each channel supplies the duration it knows. |
