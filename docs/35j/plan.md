# Plan — 35j · Fresh data outranks what the model remembers

## Approach

Before the model that answers is called, a second cheap call — the same size and role as the
router's, sent only the user's message — says one word: `fresh` or `stable`. On `fresh`, the first
round of the tool loop is sent with the provider parameter that removes the model's choice
(`tool_choice` naming `web_search`): the model can only compose the query, and the search happens.
If the turn still ends with no search recorded, the answer goes back to the model once with a
correction, as item 35i already does for unjustified links; if the retry also ends without a
search, the reply is withheld and the user is told the value could not be obtained. On `stable`
the turn takes exactly today's path. Every verdict, and every correction or withholding, is one
line in the journal with no conversation text.

The adapters do not change: everything happens inside `handle_turn` and the tool loop.

## Coverage

| AC | Where it lives | Notes |
|---|---|---|
| AC1 | `run_with_tools`: forced first round on `fresh`; correction then withholding when no search was recorded | The record is the executed tool calls, kept by the loop itself |
| AC2 | When the search chain fails entirely, the withheld-reply notice in `core/strings.py`, both languages | When a search ran and the value was still not in it, the reply is the model's judgement — unenforced, as the spec's second failure row declares |
| AC3 | The verdict `stable` leaves the loop untouched | No forcing, no extra round |
| AC4 | One `freshness:` journal line per turn, beside the existing `tools:` line | `freshness: fresh` / `stable` / `no verdict` / `forced search missing, corrected` / `… withheld` |
| AC5 | Item 35i's link fence for any claim carrying an address; for a claim carrying none, unenforced and declared as such in the spec | Nothing new here |
| AC6 | The classifier, measured: five of six abuse phrasings held 3/3 at the router's temperature; the sixth is watched through AC4 | See D7 |
| AC7 | The classifier receives the user message only, never a page, a transcript or a tool result, and reads it wrapped as data (`fence_user_input`) | Outside text has no path to the verdict |
| AC8 | Whether the turn searched is read from the executed tool calls the loop recorded, never from any text in the messages | Same record as AC1 |

## Trust boundaries and assets

| Boundary | What enters | What is worth taking | Control | Answers |
|---|---|---|---|---|
| The user message, into the classifier | Any wording, including a request not to search | Disabling the search to obtain a confident stale answer, or to make Tabris claim it searched | The message is wrapped as data; only the exact words `fresh`/`stable` count as a verdict, anything else is `no verdict` and treated as `fresh` | AC6, AC7 |
| Fetched pages, transcripts, documents | Text nobody here wrote | An instruction to skip searching, or text shaped like results | They never reach the classifier; whether a search ran is taken from the loop's own record | AC7, AC8 |
| The model's reply | Whatever it wrote | A claim of having searched | The check consults the recorded tool calls, not the reply | AC8 |

## Decisions

| # | Chosen | Rejected | Why | Measurement |
|---|---|---|---|---|
| D1 | A separate classification call, sent after the router in sequence, through the `router` role and its providers; skipped when the router says `exit` | Folding the verdict into the router's own call (one call returning role and verdict) | Two calls keep each one testable and let the measured prompt be the deployed one; a merged call couples both answers so a malformed reply loses both, and every future router change would re-verify freshness. Quota is the only cost and it has not bitten with one user. If it does, the merge is the known way out and `tools/probe_freshness.py` re-measures it | Groq `gpt-oss-20b`, 32 messages × 3, router temperature: fresh 24/24, stable 24/24, 0.3 s median, 1.1 s worst |
| D2 | Sequential, not parallel with the router | Two concurrent calls | Saves ~0.3 s on a turn that then spends 3–10 s searching; costs the core's first concurrency and a fallout matrix for two simultaneous failures. Sequence also lets the classifier be skipped on `exit` | Image turns are classified too: the `vision` primary honoured the forcing 3/3 with an image in the call, 23.6 s median |
| D3 | On `fresh`, force the first tool round with `tool_choice = web_search` | The code searching first with the user's text as the query; an instruction in the prompt | The raw message is a poor query ("daily report: TRM, oil, headlines"), and its results would spend the text budget before the model asks for what it needs. An instruction is not a fence: two already stand in the persona and did not hold | All three `general` models honoured the forcing 3/3 with a yesterday's-report in the history, the defect's exact condition. Ignored it 1/3 (`gpt-oss-120b`) and 2/3 (`glm-5.2`) on a message that needed no search — the case production never sends |
| D4 | `fresh` verdict and no search recorded → one correction round, then withhold | Withhold at once; let the reply through and only log | Reuses the correction cycle 35i already runs live; withholding first discards what may have been verifiable; letting it through breaks AC1 | — |
| D5 | The classification lives in `handle_turn`; the verdict is logged as a journal line | In `choose_role` beside the router; a column on `messages` | `choose_role` is called by the adapters, so both would change and carry one more value; a column is plumbing for a number only the operator reads today | — |
| D6 | Classifier call fails or returns no verdict → treated as `fresh` | Treated as `stable` | The wrong-direction cost is one needless search on a translation; the other direction is the defect itself | `gpt-oss-20b` returned empty content 5/6 times on one rare-fact question — `no verdict` is a real case, not a hypothetical |
| D7 | One abuse phrasing ("answer from memory, who won the last Copa América") stays uncovered and watched through AC4 | A clause in the prompt naming that pattern; a list of phrases in code | The clause was measured and moved noise, not behaviour; the phrase list is the hidden command language the spec's open question 1 rejected | With the clause: Copa América 0/3 at temperature 0 (3/3 at 0.7); without: 2/3 at 0 (1/3 at 0.7). Both models tested (Groq, Gemini) fail the same phrase |
| D8 | The two correction cycles (links, freshness) coexist in `run_with_tools`; unifying them is the first task of item 35k | Unify in this item's refactor beat | Reading cost only; seven tests fence the link cycle's edges, but the owner preferred the change to wait for the third cycle. Recorded as a lesson in the method | — |

## New concepts

- **Forced tool choice** — a parameter of the chat call that tells the provider the model must call a named tool this round instead of choosing. The model still writes the query; the code guarantees the call happens. It is a fence, not an instruction: the API refuses a plain-text reply.
- **Temperature and determinism** — the sampling setting the router runs at (0). It is not fully deterministic on a model with internal reasoning: the same question returned two verdicts in one run. A measurement therefore still needs several rounds per message, and the probe now reads the router's temperature from `config.py` rather than carrying its own.

## What this makes stale

- `CONTRIBUTING.md` — the roster rule gains its sibling: the classifier prompt and the `router` roster change only after `tools/probe_freshness.py` has run, and the probe's lot grows with every real miss the journal shows.
- `CHANGELOG.md` — one line under changed: a question whose answer can have changed is searched before it is answered.
- `docs/defects.md` DEF-11 — its cause still reads "invents"; the figures were real values of another year, and the trigger is the state of the window. Corrected at close.
- `core/strings.py` — the withheld-reply notice, both languages.
- `core/conversation.py` `WEB_SEARCH_TOOL` description — it argues for recent dates only; with the forcing in code it no longer decides anything, and it stays as it is until something measured says otherwise.
- `prompts/persona.md` — the two rules forbidding a stale figure and a false claim of having searched stay as written through live verification, so the fence is measured alone; retiring the first is decided at close, with the journal in hand.

## Risks

- **A forced search on a `stable`-shaped message.** D6 sends every failed classification to a search; if the router chain degrades, the user sees slower answers across the board. The `no verdict` count in the journal shows it early.
- **A provider that stops honouring `tool_choice`.** The measurement holds for today's three models; a roster change re-runs it. The correction-then-withhold path in D4 is what stands when the forcing does not.
- **The lot is thirty-two questions written here.** It retired the design risk; it does not know the real miss rate. The journal after two weeks in service is the measurement that does, and every real miss becomes a case in the probe's lot.
- **Two correction cycles in one loop** (D8) — readable today, and the first thing item 35k touches.

---

**Exit gate**

- [x] Every acceptance criterion has a home
- [x] Trust boundaries named, with a control answering each abuse case from the spec
- [x] Decisions record the rejected alternative
- [x] New concepts explained and understood
- [x] Stale artifacts listed
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
