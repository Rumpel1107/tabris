# Plan — 35h · Recite stored memory deterministically

## Approach

A `list_facts` tool joins the others in `core/conversation.py`. It takes no arguments and returns one
instruction — write the marker where the list belongs, do not write the facts — and no fact content.
`core/prompt.py` gains the marker, the one pattern that recognizes it, the renderer that formats a
fact list (extracted from `build_system_prompt`, so both callers share one rule), and the
substitution. `run_with_tools` stops returning a bare string and returns a small result carrying the
reply and the tools the turn ran, so the one place that dispatches tools is the one place that says
what ran. Inside its existing correction branch, beside the address and fresh-data cycles, a reply
from a turn where `list_facts` ran must carry the marker; when it does not, the reply is asked for
once more through the same `continue` the other two use, so every regenerated reply passes every
check again. `handle_turn` substitutes as the last step of its reply cleanup, after the timestamp
strip and the address filter, reading the facts again at that moment.

## Coverage

| AC | Where it lives | Notes |
|---|---|---|
| AC1 | `handle_turn`'s reply cleanup, last step; the renderer in `core/prompt.py` | facts re-read at that moment; the block is inserted after every other check has run, so nothing edits it |
| AC2 | the renderer + a new key in `core/strings.py`, both languages | no active facts renders as that line, not an empty block |
| AC3 | the renderer | every character the standard library recognizes as a line break collapses to a space; bracketed digits inside content become parenthesized. Applies to the system prompt too, since the renderer is shared |
| AC4 | the renderer | the ids come from the rows themselves; what the model does with a number the user names is item 35o's |
| AC5 | `handle_turn` | substitution runs only when the result says `list_facts` ran this turn |
| AC6 | `run_with_tools`, in the branch that already holds the address and fresh-data cycles | one correction through `continue`, journal line either way, the existing last-round guard bounding it |
| AC7 | the pattern and the substitution in `core/prompt.py` | one rule for three consumers — the presence check, the substitution and the strip; all token surgery happens on the model's text before the block exists |

## Trust boundaries and assets

| Boundary | What enters | What is worth taking | Control | Answers |
|---|---|---|---|---|
| A fact's `content`, written by distillation out of the user's own conversation | free text, one field | making one fact show as several entries, or planting a bracketed number the user then cites as an id — `forget_fact` filters by owner, so the harm is bounded to that user's own facts and is reversible, but the wrong fact still goes | in the one shared renderer: collapse every line break the standard library recognizes, and neutralize bracketed digits inside content | AC3 |
| A page reaching the model through `web_search` / `web_fetch` | untrusted text, already wrapped as tool output | inducing a recital where none was asked for, in front of whoever shares the channel | substitution gated on the call having run; a turn that both read a page and substituted gets its journal line. Beyond that, accepted: the facts already travel in the system prompt every turn, and the control for inducement is the existing `fence_tool_output` | AC5 |

## Decisions

| # | Chosen | Rejected | Why | Measurement |
|---|---|---|---|---|
| D1 | The tool call is the intent signal and the marker is the placement; both exist | Only the marker, with the instruction in `persona.md` | Without a call nothing says a list was owed, so a miss is unmeasurable and the forcing question could never be decided. The call also leaves the turn its existing `tools:` line | — |
| D2 | The tool returns the instruction alone, never the facts | Return the rendered block with the instruction | Handing the model the exact text it is told not to write is the pull DEF-2 established. The facts still reach it through the system prompt, so nothing it needs is withheld | — |
| D3 | The facts are read again at the moment of substitution | Render from the set loaded for this turn's system prompt | That set predates the turn's tool calls, so "olvida el hecho 12 y dime qué recuerdas" would list 12 in the same reply that confirms it was retired, and the ids shown would not be the ones the next request acts on. One extra read, only in turns that recite | `DB_BUSY_TIMEOUT_MS = 5000`, WAL on: a read is not blocked by the background distillation's write |
| D4 | Substitution is the last step of the reply cleanup, after the timestamp strip and the address filter | Substitute earlier and declare the block's addresses as seen | A fact may hold a URL the turn never searched; substituting earlier lets the address filter cut the block or bounce the reply for a correction that can lose the marker. Declaring them seen is worse: a stored address would then authorize the rest of the reply, which the turn never verified. The filter judges what the model writes, and the block is not that | — |
| D5 | `run_with_tools` returns the reply and what the turn ran | A tracker the caller owns and passes in, written by the executor closure | Both remove the desync, but a parameter a future caller forgets fails silently — the shape behind DEF-7, DEF-13 and the `conftest.py` lesson. A changed return fails loudly: the ~30 test call sites that read it say so immediately. A small result object rather than a tuple, so 35k's unification extends it without touching them again | — |
| D6 | The `- [id] content` formatting moves into one shared function, used by the system prompt and the recital | Keep the format where it is and write a second copy for the tool | Two copies drift — DEF-1 and DEF-3 were exactly that, a rule that knew one shape. Sharing also neutralizes a fabricated id against the model, not only against the user, which is why the system prompt's rendering changes on purpose | — |
| D7 | Every line-breaking character collapses to a space, taken from what the standard library recognizes; bracketed digits in content become parenthesized | Collapse `\n` and `\r` only; or escape them visibly | A hand-written list of separators is how a fence ends up seeing one shape: `U+2028` breaks a line and is neither. A visible escape leaks an implementation artifact into what the user reads, for no extra safety | — |
| D8 | One pattern decides everywhere: presence check, substitution and strip | A criterion per site, kept "equivalent" | Two copies drift, and a third category — matching the strip but not the check — is where a mangled marker is removed in silence instead of counted as a miss | — |
| D9 | All marker surgery happens on the model's text before the block is inserted | Scan the whole reply afterwards and exempt the block's range | A fact's own content may hold something marker-shaped, which a later scan would cut from inside the block. Exempting a range means tracking positions in text, the bookkeeping 34b already identified as the risky part | — |
| D10 | The marker check joins the branch that already holds the address and fresh-data cycles, correcting through the same `continue` | A correction outside the loop, in `handle_turn` | The existing cycles re-apply every check on each pass; a correction outside the loop produces a reply nothing re-checks, so a regenerated answer could carry a fresh unjustified address past the DEF-10 fence. It also lands where item 35k's unification already has to work | — |
| D11 | The tool takes no arguments and lists every active fact | Accept a topic or date filter | Not what the problem evidenced; searching stored material by topic or date is item 35f's | — |

## New concepts

- **A marker the code substitutes.** The model writes a fixed token where the list belongs and the
  code replaces it before the reply leaves. `core/prompt.py` line 12 already does this for
  `{{AGENT_NAME}}`; the difference is that ours is written by the model, so it needs a pattern that
  tolerates variation rather than a literal replace.

## What this makes stale

- `prompts/persona.md` line 19 — reciting the facts by hand is replaced by: call `list_facts` and
  place the marker.
- `prompts/persona.md` line 33 — the hand-written list of what reaches beyond the conversation gains
  listing what is remembered. Keeping that line true by hand is item 35e's subject.
- `core/strings.py` — the no-facts line, in both languages.
- `CHANGELOG.md` — one line under added.
- The ~30 test call sites that read `run_with_tools`'s return, from D5.

## Risks

- **The model writes the marker and its own list too.** Only the marker is substituted, so the reply
  would carry the block plus a paraphrase. Nothing detects it; declared in the spec's failure table.
  What lowers it is D2.
- **The system prompt's rendering changes on every turn of every user** (D6), which is a wider blast
  radius than a recital. It is a rendering change inside free text — a space for a line break,
  parentheses for brackets — and it gets its own test.
- **A marker mangled past what the pattern tolerates** is counted as a miss and corrected once; if
  the correction fails, the user reads a reply with no list rather than one with a raw token.
- **The refactor of D5 and the new behaviour are separate changes**, and mixing them in one review is
  what the method's size rule forbids; the tasks document splits them.

---

**Exit gate**

- [x] Every acceptance criterion has a home
- [x] Trust boundaries named, with a control answering each abuse case from the spec
- [x] Decisions record the rejected alternative
- [x] New concepts explained and understood
- [x] Stale artifacts listed
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
