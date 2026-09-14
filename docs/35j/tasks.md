# Tasks — 35j · Fresh data outranks what the model remembers

## Slices

| # | Slice | Covers | How it is verified | Done |
|---|---|---|---|---|
| 1 | The verdict and the forced first round. The classification prompt moves from `tools/probe_freshness.py` into `core/`, and the probe imports it from there, so the measured prompt is the deployed one. `handle_turn` asks the verdict through the `router` role after the role is known — text turns and image turns alike, never on `exit` — and logs `freshness: fresh` / `stable` / `no verdict`. On `fresh` (or no verdict) `run_with_tools` sends the first round with `tool_choice` naming `web_search`; `providers.chat` passes the parameter through. On `stable` nothing changes. `CONTRIBUTING.md` gains the probe rule and `CHANGELOG.md` its line, in the same change. | AC1 (forcing), AC3, AC4, AC6, AC7, AC8 | Live on Discord with yesterday's report still in the window: a question about today's rate shows `freshness: fresh` followed by `tools: … web_search` in the journal and a reply with today's value and date; a translation shows `freshness: stable` and no `tools:` line; the same question sent as a voice note and beside a photo take the same path. Tests: the prompt reaches the model with the message wrapped as data; a verdict other than the two words is `no verdict`; `tool_choice` is present on the first round on `fresh` and absent on `stable` and on later rounds. | ⬜ |
| 2 | The net beneath the forcing. A `fresh` turn that ends with no executed `web_search` goes back to the model once with a correction, in the shape of the link correction; if the retry also ends without one, the reply is withheld and the user reads the notice that the value could not be obtained now, in both languages. Journal lines `freshness: forced search missing, corrected` and `… withheld`. | AC1 (net), AC2 (chain failure) | Tests only, with the model double ignoring the forcing: one correction then the withheld notice, and the notice also when every search provider raises. It cannot be provoked live on demand — the three `general` models obeyed 3/3 under the defect's condition — so it stands on tests and on the correction cycle 35i already runs in production. Declared as such here rather than found out later. | ⬜ |
| 3 | Close. `docs/defects.md` DEF-11 corrected — the figures were real values of another year and the trigger is the window's state, not invention; the third live case is already in `framing.md`. `PLAN.md` item marked, `v0.1.19` cut (a fix and a fence, not a capability). The two persona rules stay until the journal of two weeks in service says whether the first can go. | — | The tag in service, the journal of the first days read for `freshness:` lines, every real miss added to the probe's lot. | ⬜ |

## Notes

- Slice 1 goes first because it is the one that can invalidate the rest: if the forcing does not happen live, slices 2 and 3 have nothing to stand on.
- Slice 1 is usable alone. Without slice 2 a model that ignores the forcing gets today's behaviour — the stale answer — which is no worse than before; slice 2 closes that hole, it does not enable the feature.
- Slice 2's verification is honest about its limit: the failure it handles could not be reproduced on demand with the current rosters. Its live proof arrives only if a provider stops honouring `tool_choice`, and the journal line is what would show it.
- Image turns are included in slice 1 on measurement: the `vision` primary (`gpt-5-nano`) honoured the forcing 3/3 with an image in the call, at 23.6 s median inside the role's 40 s. The dead second link found in the same probe is item 35m, not this one. What the classifier cannot do on an image turn is read the image — "what is this?" with a photo and nothing else classifies as `stable`, rightly, since the text carries nothing that changes; searching *after* looking is another mechanism and is not in this item.
- Voice notes need nothing: the transcription becomes the text of the turn before the router runs.
- **Read against the other phase documents.** Spec open question 4 (can a cheap call classify?) is answered by the plan's D1 measurement; question 5 (how many seconds?) by 0.3 s median for the verdict, with the search itself costing what it costs today. The spec's failure row "fresh results arrived and the reply still came from memory" stays invisible, as declared there, and no slice claims it. The plan's D8 defers the unification of the two correction cycles to item 35k; slice 2 therefore adds a second cycle beside the first, on purpose.

---

**Exit gate**

- [x] Slices in execution order
- [x] Each slice states its verification
- [x] No slice leaves code that nothing calls
- [x] The phase documents were read against each other; contradictions resolved or recorded
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
