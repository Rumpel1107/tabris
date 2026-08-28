# Plan — item 34a, audio input

## Approach

A new `core/transcribe.py`, built like `core/search.py`: one adapter per provider, a registry mapping name to adapter, and an ordered list in `config.py` the dispatcher walks. It takes the bytes of an audio file and the user's language, and returns text. It knows nothing about Discord.

The Discord adapter gains a step in front of the existing one: when the incoming message is a voice message, it checks the reported duration, reads the audio, asks for the transcript, and hands that text to the same `handle_message` a typed message goes through. Everything downstream — routing, tools, memory, storage — is untouched.

The reply for a voice message differs from a typed one in two visible ways: it opens with a line stating the transcript, and it is sent quoting the voice message.

## Coverage

| AC | Where it lives | Notes |
|---|---|---|
| AC1 | `channels/discord_ch.py` (`on_message`) + `core/transcribe.py` | The transcript enters `handle_message` as the user input; the opening line is prepended by the adapter. |
| AC2 | `channels/discord_ch.py` (`send_reply`) | The first piece quotes the original message; failure to quote falls back to an ordinary send. |
| AC3 | `channels/discord_ch.py`, using the limit in `config.py` | Checked against the duration Discord reports, before reading or sending anything. |
| AC4 | `channels/discord_ch.py` (`on_message`) | Only a message flagged by Discord as a voice message takes the new path. |
| AC5 | `core/transcribe.py` (dispatcher returns nothing) + adapter notice | Nothing reaches `handle_message`, so nothing is stored. |
| AC6 | `core/transcribe.py` (empty-speech check) + adapter notice | Same: the turn never starts. |
| AC7 | `channels/discord_ch.py` | Transcription happens before `handle_message`, which is what routes to registration. |
| AC8 | Existing `handle_turn` | No change: the transcript is the user input, stored and distilled like any other. |
| AC9 | `channels/discord_ch.py` | The quoting and the opening line are inside the voice branch only. |

## Decisions

| # | Chosen | Rejected | Why |
|---|---|---|---|
| D1 | Transcription as a shared module with its provider list in `config.py` | Transcribing inside the Discord adapter | Item 34d states it reuses this pipeline; the effort is the same today and duplicating it later is not. Same call taken for `split_message` in item 34g. |
| D2 | `whisper-large-v3-turbo` | `whisper-large-v3`; transcription on Gemini | Fixed by decision D11 and unchallenged by anything found now: the large model costs roughly three times more and Gemini 17–27×, for accuracy that does not change what a personal assistant does with the sentence. |
| D3 | Pass the user's stored language to the transcriber | Letting it auto-detect | Auto-detection works, but the scenario that justifies this item is noisy — street, traffic, driving — and a short noisy clip is where language detection fails and returns nonsense. |
| D4 | The audio travels in memory, from Discord to the provider | Writing it to a temporary file first | A voice note is personal data; not touching the disk means there is nothing to clean up, nothing to leak if cleanup fails, and no permissions to get right. |
| D5 | Decide "no speech" by whether the transcript holds any letter once spacing and punctuation are ignored | The provider's own no-speech probability | Measured on 2026-08-27: for a mute test tone, the model we use reported that probability as zero while the larger model reported 0.98. The field would mislead precisely on the chosen model. |
| D6 | The transcript line and the three notices are `msg()` strings the adapter prepends or sends | Building them inside the core | `core/` never knows UI text; `handle_turn` returns a reply and each channel decides what to show. Established in item 32. |
| D7 | The transcript line is the microphone sign followed by the text itself | Prefixing it with a word such as "Understood:" | Chosen 2026-08-28: in the street the line has to be read at a glance, and the sign carries the meaning with nothing to read. |
| D8 | Quote only the first piece of a split reply | Quoting every piece | Discord shows a quote block per message; repeating it down a long answer is noise. |

## New concepts

- **Sending a file without saving it.** Discord hands the audio over as raw bytes, and the provider accepts an upload from memory, so the recording never becomes a file on the machine. The alternative — save it, send it, delete it — adds a step that can fail and leaves a copy of someone's voice on disk in the window between.

## What this makes stale

- `prompts/persona.md` — the sentence stating what Tabris can actually do: it now understands voice messages. Folded into the existing sentence, not added as a new rule.
- `config.py` — new limit and new provider list. `.env` is unchanged: the Groq key already exists and is already loaded.
- `CONTRIBUTING.md` — the provider-abstraction pattern names models and search; transcription becomes the third instance of the same shape.
- `PLAN.md` item 34a — marked done at close.
- `README.md` — only if it enumerates what a user can send; checked at close.

## Risks

- **A wrong transcript that reads plausibly.** Undetectable by construction; the opening line is the whole mitigation, and it only works if it stays short enough to actually be read.
- **The quoting path is the one piece touching code that every reply already goes through.** A mistake there breaks typed conversation too, not just audio — which is why the fallback to an ordinary send is an acceptance criterion and not a nicety.
- **Live verification needs a phone.** Nothing in this item can be exercised from the command line, so a green suite proves less here than usual.
