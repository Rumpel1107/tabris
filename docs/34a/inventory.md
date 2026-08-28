# Inventory — item 34a, audio input

## What exists

| Artifact | What goes in it (one sentence) | Verdict |
|---|---|---|
| `PLAN.md` item 34a | The roadmap line for this item: transcribe incoming Discord voice messages and feed the transcript into the normal text flow. | keep |
| `PLAN.md` item 34d | The roadmap line for Telegram, which states it will reuse the media pipeline this item builds. | keep |
| `PLAN.md` decision D11 | Why Groq stays in the roster, speech-to-text being one of its three jobs. | keep |
| `channels/discord_ch.py` | The Discord adapter, today reading only `message.content`. | keep |
| `core/search.py` | The shape a shared capability takes here: adapters in a registry, provider order in `config.py`, fall through on failure. | keep |

## Inherited claims

| # | Claim | Where it came from | Verdict | Note |
|---|---|---|---|---|
| 1 | Whisper is reachable on the existing Groq key, no new account | session 2026-08-17 | verified 2026-08-27 | `whisper-large-v3-turbo` and `whisper-large-v3` both answered 200 to a generated test file. |
| 2 | Speech-to-text on Groq costs about $0.04 per hour of audio | D11 (2026-08-18) | verified | Confirmed against current published pricing. |
| 3 | The free tier covers this use comfortably | this item | verified | 2,000 requests/day and 7,200 audio-seconds/hour, billed with a 10-second minimum per request. Not read as a ceiling: a voice message is seconds long, so growth in testers moves request count, not audio volume per message. |
| 4 | A file may not exceed 25 MB | provider docs | verified | Discord caps a free-account attachment at the same 25 MB, so no message can arrive that the transcriber must refuse for size. |
| 5 | No new dependency is needed | this item | verified 2026-08-27 | Checked in the installed environment, not in documentation: `discord.py` 2.7.1 exposes `MessageFlags.voice` and an attachment's `duration`, `content_type` and bytes; the `openai` client already in use carries the transcription endpoint, which Groq serves on its OpenAI-compatible URL. |
| 6 | The transcription response carries the detected language and the duration | probe 2026-08-27 | verified | Returned without asking for anything beyond `verbose_json`. |
| 7 | The command line cannot participate: it has no way to send audio | item 34a | verified | Live verification for this item therefore happens on Discord only. |

## Contradictions between artifacts

| # | What disagrees | With what | Resolution |
|---|---|---|---|
| 1 | Item 34a describes only Discord and says nothing about a shared piece. | Item 34d states it will reuse "the shared media pipeline (34a/b)" untouched. | Resolved in conversation 2026-08-27: 34a builds transcription as a shared module with its provider list in `config.py`; the Discord adapter only calls it. Same reasoning accepted for `split_message` in item 34g — the effort is identical either way, and the second channel is already on the roadmap rather than hypothetical. |

## Moves

None. This item inherits no document to relocate; the inherited material is roadmap lines and verified facts.

## What the roadmap says now

Item 34a is unbuilt and unblocked. Its one hard dependency, a channel that carries media, has been live since item 34. The engine, the account and the libraries are all in place and verified today, so what remains is entirely design and build: where transcription lives, what the user sees, and what happens when it fails.
