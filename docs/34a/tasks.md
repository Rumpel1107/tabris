# Tasks — item 34a, audio input

## Slices

| # | Slice | Covers | How it is verified | Done |
|---|---|---|---|---|
| 1 | Speak and be answered: `core/transcribe.py` with its provider list, the Discord adapter recognizing a voice message, the duration limit checked before anything is downloaded, and the transcript line opening the reply. Persona sentence and the `CONTRIBUTING.md` provider pattern updated in the same change. | AC1, AC3, AC4, AC7, AC8, AC9 | A voice message sent from the owner's phone is answered, and a recording over four minutes is refused without being transcribed. | ✅ verified live from a phone (2026-08-28). The over-four-minutes refusal was not exercised — filling the limit proved impractical — and the owner accepted that risk knowingly; the notice itself is covered by tests. |
| 2 | The two failure notices: transcription unavailable, and a recording with no speech. | AC5, AC6 | A recording made in silence is answered with the "nothing was heard" notice, live. The technical failure is covered by tests, optionally confirmed in development with an invalid key. | 🔶 built 2026-08-29; the live check ran 2026-08-31 against the deployed build and failed — two silent recordings came back transcribed as "Gracias", so the notice never fired. A density rule was added the same day and verified live at eleven and five seconds; a three-second silence still slipped through, so the floor below which density is not judged dropped to two seconds. That case is checked on the next deployment. |
| 3 | The reply quotes the voice message, falling back to an ordinary send when quoting fails. | AC2 | Seen on the phone: the answer hangs off the voice message. The fallback is exercised in tests. | ❌ cancelled 2026-08-29, never built — see AC2 in `spec.md`. |

## Notes

- Slice 1 is usable on its own: after it lands the feature works, with failures showing as the generic error the adapter already sends today.
- Slice 3 was last and alone because it is the only one touching the path every reply takes, typed ones included. It was cancelled before being built, so that path was never touched.
- Nothing here can be verified from the command line, which cannot send audio. Every live check happens on Discord, from a phone.
- **Divergence found reading the spec against the plan, resolved here.** The spec's third open question leaves the duration limit "with the shared module"; the plan places the check in the Discord adapter. Settled: the limit's *value* lives in `config.py`, shared, and the *comparison* stays in each channel, because only the channel knows what its platform reports. Telegram repeats one comparison rather than inheriting a function wrapping `>`.
