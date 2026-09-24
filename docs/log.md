# Log

> **What goes in this document:** what happened, dated, newest first. Append-only. A paragraph
> earns its place by keeping whoever picks this up from repeating a mistake or undoing a decision;
> session narrative belongs in the conversation.
>
> Not here: what broke after the code was called done (`docs/defects.md`), what changed for
> whoever runs Tabris (`CHANGELOG.md`). Why a decision was taken is `docs/decisions.md`; what is
> pending is `docs/roadmap.md`.

## 2026-09-24 — The old deployment is retired, closing 37b

Item 37b, slice 5, the last piece of the move to the rented host (D13). M3's seven-day window from
the 2026-09-13 cutover closed on 2026-09-20; the retirement itself ran four days after that. On the
homelab host: the four units (`tabris`, `tabris-backup`, `tabris-probe`, `tabris-purge` — service
and timer) were confirmed `disabled` and unloaded before their unit files were deleted, then
`/opt/tabris`, the `tabris` system user and `/var/backups/tabris` were removed. `id tabris` and
`ls -d` on both paths came back not-found, which is the item's own exit condition — nothing of the
old install is left on that host, and Tabris keeps answering from the new one, unaffected.

## 2026-09-15 — The vision chain had one working link

Items 35n and 35m, in that order. The roster probe gained `--tool-choice`, the call a fresh turn
makes since 35j, and its first run on the `vision` roster showed what the journal could not: the
second link answered 404 to everything, and the third obeyed the forcing half the time and took
four to eight minutes to answer, past the forty seconds the role waits. For a photo the primary
could not serve there was no answer at all, and nothing but the ordinary provider warning said so.

Five candidates went through `--grid` and `--tool-choice`. One read nothing, one ignored the
forcing — each caught by the probe the other would have passed — and three tied on both. The owner
chose by price and family over a three-second difference: `glm-5.3-flash` second,
`seed-1.6-flash` third, which puts a fourth model family in the system. A tie on the property that
decides is a tie; what separated the three was what the probes do not measure.

## 2026-09-15 — A fresh question is searched before it is answered

Item 35j, slice 1, in service as `v0.1.19`. A router-sized call reads the user's own words and says
`fresh` or `stable`; on anything but `stable` the first tool round is sent with `tool_choice`
naming `web_search`, so the search is no longer the model's choice. Verified live under the
defect's own condition — today's report already in the window — by text, by voice note and beside
a photo: `freshness: fresh` followed by `tools: … web_search` on the rate question, `stable` and no
tool line on a translation and on "what is this?" with a picture. The verdict costs 0.3 s; the
image turn skips the router and pays only the classifier.

Two things the build found that the documents did not say. The classifier consumes one model reply
inside `handle_turn`, so every test that scripts the replies in sequence had to pin the verdict —
six went red and were pinned, three stayed green with their tool never running, and only the first
review caught them (DEF-13). And a captionless photo reaches the classifier as an empty string,
which is now `stable` in code without a call, against D6's default, because there is nothing in it
that can have changed.

The review itself changed shape this week: three models outside the author's family, chosen by
measuring eight on commits that had broken in production, run from `method/tools/review.py`. Its
first two runs each found one defect no test would have — the three rotted tests above, and a
second shape of DEF-6 in the DEF-12 fix. The tag was cut at slice 1 rather than at close, because
the live verification needs code in service; slice 3 cuts the next one.

## 2026-09-13 — Production moves to a rented host

Item 37b, slices 1–4, in one evening: the deployment procedure of item 37 re-run on a machine the
owner already pays for, the database carried by `tools/backup.py`, the old service stopped before
the new one started, and a real reboot that put Tabris back on Discord five seconds after the unit
started. Counts matched on both sides — 2 users, 28 active facts, 718 messages — and the first two
replies from the new host, one of them a forced search, closed the cutover. The old deployment stays
installed and disabled for seven days as the way back (M3); slice 5 removes it.

Two things the procedure did not say and the move needed. A shell glob in front of `sudo` expands
as the caller, who cannot read `/opt/tabris`, so it reaches the command unexpanded — run the whole
line as root or as the service user. And the engine's backup call is the only copy that is whole:
the `-wal` file exists only while a connection is open, so a listing without it proves nothing
about what a plain copy would have caught mid-write.

The connectivity probe moves with everything else and stays on. Its reason — counting a home
network's outages — is gone; it stays because the new host's uptime is so far an expectation, and
a month of its log turns that into a number before anyone decides to retire it.

## 2026-09-09 — An answer rests on what was actually read

Item 35i, the shape DEF-10 and DEF-11 both belong to, closed on three parts, each measured before
it was built. A search now hands over the page instead of a snippet (`include_raw_content`, no
extra credit, half a second; capped at 4000 characters per page and 16000 for the whole turn — the
full text of five pages ran to 126632 characters, three times the window). An address the answer
cites must appear in what the turn actually received — the results, the conversation, the user's
own message. And an answer that cannot justify an address goes back to the model, told which ones
failed, rather than being silently cut: on a clean topic the first draft invented five addresses
under five real domains before searching once; after the correction, three searches produced five
that open what they describe. Rejected: a source list rendered by code (the owner: unreferenced
links at the end read as disruptive) and a second model judging the answer (a cost on every turn,
and another model able to be wrong). Left open: an invented claim with no address is untouched
(DEF-11, closed later by item 35j), and a real address differing only in tracking parameters is
refused, since for some sites the query string *is* the page.

## 2026-09-07 — What was never Tabris's leaves the plan

Sections 2, 6 and 7 moved to the workspace plan one level up: the owner's constraints, the
eight-project pipeline and the gate any repository passes before going public. D8 and D9 went with
them and were renumbered there, because `D8` already names a different decision in three of this
repo's own phase documents.

The pipeline in §6 turned out to already be the cross-project view the owner was considering
building a tool for. What was missing was never the tool — it was that the file lived inside one
project, and a public one.

Section numbering keeps its gaps on purpose: `CONTRIBUTING.md` and the phase documents reference
§3, §4, §4.3 and §4.4, and this layout changes again when the roadmap, the decisions and this log
get files of their own. What left is no longer under version control, so it has no history until it
finds a repository.

A canonical `AGENTS.md` and a one-line `CLAUDE.md` importing it were added a level up. The second
is not redundant: Claude Code reads `CLAUDE.md` and not `AGENTS.md`, so without it nothing loads
and the method applies only when the owner remembers to mention it.

## 2026-09-07 — The web stops being a way into the network

`web_fetch` requested whatever URL the model handed it and followed redirects blindly, on a machine
sharing a segment with the router and answering through Discord. It now takes `http(s)` only,
requires every address a host resolves to be public, and checks each redirect hop rather than only
the first.

What the web tools return reaches the model inside `<tool_output>` tags, declared in the system
prompt as material to report on and never instructions to follow. Only what comes from outside is
fenced: `update_profile` answers an ambiguous city with an instruction the model must obey, so
fencing every tool result would have broken that flow. The rule is not which tool, but who wrote
the text.

Neither was a defect — nothing broke in production — which is why they are here and not in
`docs/defects.md`.

## 2026-09-01 — The history window doubles, and gains a second bound

Both testers hit the same wall: a topic takes 20 to 30 exchanges to finish, and answers started to
slip once its opening left the ten-message window. `MAX_HISTORY` went from 10 to 30, but a message
count alone is blind to size, so a second bound was added — a combined character budget, whichever
of the two runs out first. Measured before deciding: sixty typical messages ran to 31,486
characters against a budget set at 40,000, so the new bound stays silent in ordinary use and exists
for what a count cannot see — an image riding along for thirty exchanges instead of ten, or a
document's extracted text arriving as one message the size of the whole window. The newest message
is always kept even alone over budget, and the system prompt is never counted against either
bound — one deterministic rule, so a new kind of attachment never needs a lifetime rule of its own.

## 2026-09-01 — Audio in closes, and vision opens on its first slice

Item 34a, audio input, closed after a live miss: silence sent as a voice note came back
transcribed as "Gracias" — a stock phrase the letters-only check read as speech — and got answered
as if it had been said. Fixed with a density rule in `core/transcribe.py` comparing characters
against duration, with a floor below which density is not judged at all; the floor moved from four
seconds to two after a three-second silence still slipped through, verified live at both ends. A
third slice — quoting the voice message back — was cancelled from live use entirely: Discord's
typing indicator already makes the sender wait, and four minutes is a generous ceiling for one
recording, so nothing about it needed clearing up.

The same week, item 34b's first slice: photos answered by a model that can see, through a `vision`
role decided in code rather than by the text-only router. Verified live from a phone on all eight
of its criteria. The image never touches disk and never enters the stored history — it travels
beside the session and meets the text only when the call to the model is actually built. Slices 2
and 3 (staying "in view" across the window, and saying when it leaves) are still open — see
`docs/roadmap.md`.

## 2026-08-28 — Memory consolidation, and a report that would not fire on time

Two passes closed the same week, both from the first days of real production use (2026-08-19).
Distillation (35c) wrote one more fact per pass on any subject a conversation kept developing —
a new angle is neither false nor a correction, so nothing retired while something new was always
added. One ordinary day produced 23 facts; 16 were retired in a single sweep the user asked for
after reading the list back, the five survivors covering what eighteen had. The fix lived in the
prompt, not the model: read the known list first, and where a new fact overlaps propose the merged
wording and retire what it replaces, and leave momentary states out of it entirely. Closed on
measured production data — 12 facts in three days against 23 in one, every retirement matched to
the fact that replaced it — not on impression, and only after production was wiped clean once to
discard the noise already accumulated.

Separately, the daily report (item 39's forerunner) did not fire on the first message of the day,
and once asked about a past message Tabris gave four different wrong times for it (35d). Two
independent causes: a deterministic "first message of the day" line stated a condition without
telling the model what to do with it, so three imperative style rules outweighed it — fixed by a
persona rule that a stored instruction outranks style defaults; and rehydrated history carried no
timestamps at all, fixed by stamping every message `[YYYY-MM-DD HH:MM]` in the user's own timezone
on the way in and stripping the mark on the way out, so it never reaches a reply, storage, or an
echo. The model copied the stamp into its own answers on the first live reply anyway — ten stamped
history turns were a stronger pull than the rule — so only the user's turns are stamped, halving
the added weight and closing the loophole in code instead of asking the prompt not to copy it.

## 2026-08-23 — Data privacy minimums close the gate before beta-testers

Item 34c, the gate the workspace plan's sequence places before onboarding anyone else: export,
suspend, restore and erase, all from `tools/admin.py` and unreachable from any chat. A suspension
exports first, a 14-day grace window can undo it with everything intact, and conversation older
than 30 days is erased by the same daily pass that clears accounts past their window — a real
delete, retired messages included. "View my data on request" was decided against on purpose: the
profile and every active fact already ride in the system prompt every turn, so a dedicated
rendering path would only duplicate it.

Two things learned the hard way while building it. A copy taken by hand before a delicate
operation must not share a name with the day's scheduled backup — rotation is by date alone, one
per day, and the copy taken before wiping the first production database was very nearly destroyed
by exactly that collision. And an erasure is honest only when stated with its real margin: daily
backups on a seven-day rotation mean a copy made before someone's data was erased still holds it,
so the promise is "gone within seven days," not "gone now."

## 2026-08-23 — The process reports its own version, and a retry chain stops tripling delays

Asked how to tell what production was actually running, the honest answer needed two commands and
a caveat — `README.md`'s one-liner read the checkout on disk, not what the running process had
loaded, and the two can disagree after a deploy that did not restart cleanly. Each adapter now
writes the tag it loaded as it starts, via `git describe` with a fallback to the bare commit and
then to "unknown" — a version it cannot read is a warning, never a failed start. Separately, and
found three weeks earlier while chasing a Discord latency bug: the `openai` client retried every
provider three times on its own before the fallback chain could act at all, tripling every timeout
in a role with several providers in its chain. `max_retries=0` fixed it — the ordered provider
list already is the retry policy, and a client retrying underneath it only delays reaching the
fallback that was supposed to happen immediately.

## 2026-08-21 — Deploy becomes a real service, in four sittings

Item 37, the four slices that took Tabris off a terminal for good. Data paths moved behind
`config.DATA_DIR`, a daily backup script uses SQLite's own backup API rather than a plain file
copy (a WAL sidecar can hold the newest writes, and a plain `cp` can catch a transaction
mid-flight), and the deployment runs under its own system user with no sudo and secrets in a keys
file the service manager reads unquoted. `deploy/tabris.service` restarts always with bounded
backoff and starts at boot — verified live three ways: a `SIGKILL` answered by an automatic
restart one second later, a real reboot that had Tabris back on Discord three seconds after the
unit started, and logs that carry ids and tool names but never message text. A five-minute
reachability probe writes to the system log, successes as information and failures as warnings, so
"when was it down" became one filtered query instead of a memory. And `tools/deploy.sh` puts a tag
in service or returns to an earlier one with the same command — the suite runs inside the
deployment first, and any failed step restores whatever tag was already serving, exercised for
real in both directions including a rollback past the script's own most recent version.

## 2026-08-21 — Four small nits, each closed with its reason instead of just deleted

Item 40, the code-quality nits from an earlier review. Splitting `requirements.txt` into a
runtime and a dev file was rejected outright, not deferred: the deploy script and the setup
script both install `requirements.txt` alone, so a split either breaks the deploy or has
production install the dev file anyway. `.pytest_cache/` needs no `.gitignore` entry — pytest
already writes its own `*` ignore file inside that directory. `.env.example` gained a trailing
newline: cosmetic until the deploy script began reading it with a shell `while read` loop, which
silently skips a final line with no newline at its end — the missing variable was
`DISCORD_BOT_TOKEN`, without which Tabris does not start. And the distillation header parser
became tolerant of spacing and casing, because an unmatched `HAS_CHANGES:yes` read as "nothing to
change" and silently discarded a whole pass with no error anywhere.

## 2026-08-20 — A repository goes public out of order, and the history it carried

The repo went public on 2026-08-18 (item 42) before the publishable checklist had fully passed and
before a security pass had purged what was in its history (item 41) — the exact sequence the
checklist exists to prevent. No secret was ever exposed: `.env` and the channel identity file were
never tracked. What was there was personal — two early commits carrying `memory.md` and a database
with the maintainer's own profile, and 36 commits naming the maintainer's own machine inside this
file. Both purged with `git filter-repo` in two passes, files by path and the name by text
replacement, then force-pushed; the deployment was re-cloned onto the new history since a clone
keeps the old objects in its own `.git` regardless of what the remote now shows. The personal data
in the history was public for two days before the purge landed. Caveat recorded rather than
hidden: a host does not garbage-collect immediately, so the old objects stay reachable by their
exact hash until it does — with no forks and nobody holding those hashes, the practical risk was
judged low.

## 2026-08-16 to 2026-08-19 — A string of bugs found in the first live sessions

Four defects, each found in real use within one week of Tabris going live, each fixed at its root
rather than patched at the symptom. A profile correction asked whether a place *could* be
elsewhere — a question that always admits yes — so the model retried the ambiguity check seven
times until one bare city name slipped through and saved the wrong time zone for a Colombian user
(34h); the question became a sufficiency check instead, and a retry loop gained a hard cap
(`MAX_TOOL_ROUNDS`) that had never existed. Days later a city and its time zone disagreed outright
— "Madrid" came back paired with `Europe/Madrid` for the same user — because three separate model
calls decided city, country and time zone independently, with nothing forcing them to agree
(34i); the fix collapsed them into one call that returns all three together, so they cannot
disagree by construction. A whole sentence answering the name question was once stored verbatim as
someone's name (34j): the name helper was the only onboarding helper asking its task in the
abstract, and it silently fell back to raw text on failure instead of admitting it could not tell.
That fallback turned out to be shared by five other helpers, each inventing a quiet default —
English, UTC, "not ambiguous," "said no" — on a failure a person never sees (34k); every one of
them now says "I could not tell" and holds the step instead.

## 2026-08-11 to 2026-08-12 — A lost correction, a reply cut at 2000 characters, and a frozen bot

Three defects from the first days on a real channel. Asked to reword a stored fact, Tabris retired
the old wording and claimed the new one was saved — but distillation reads only `user` turns, so
an assistant-authored correction was invisible to it and the fact was simply gone (34f); the model
gained a `remember` tool mirroring `forget`, so a correction is now propose-then-write instead of
a claim nothing backs. Discord silently drops any message over 2000 characters: a 2093-character
reply vanished mid-send while the model's own history kept an answer the user never saw (34g); the
adapter now splits at a line break, then a space, then hard, and unwinds the turn from both the
database and the session if delivery fails partway, so a rejected message can never undo an older
one. And a slow model call froze the whole bot for everyone: the OpenAI client retried three times
on its own before the fallback chain could act, and the blocking call ran straight on Discord's
event loop, stalling its heartbeat past the point the gateway warns about dropping the connection.
Both fixed together — `max_retries=0` (the fallback chain already is the retry policy) and the
call offloaded to a thread behind a per-user lock, which also replaced the accidental
serialization the frozen loop used to provide.

## 2026-07-30 to 2026-08-12 — Account linking, and a shared state machine for onboarding

Item 34e: the CLI and Discord were two separate users with two separate memories, linked only by a
short-lived code, never by name (impersonation risk). The harder half was not the link-code table
— it was that onboarding itself had to stop being CLI-shaped. `advance_onboarding` became a pure
state machine, one message in, one reply out, with pre-user state living on `Session` because a
session is the only identity that exists before an account does; the CLI calls it in a loop,
Discord once per incoming message. Rejected: a parallel pending-dict per adapter, which would have
re-created the duplication the channel-agnostic refactor (item 32) had just removed. A burst of
quick messages during onboarding — three answers landing as one before anyone reads them — was
named as a real hazard and left to the read-back to catch rather than solved with a debounce timer
only one channel would need. Two bugs surfaced live and fixed the same week: a pasted link code
read as someone's name when a sentence surrounded it ("Tengo este codigo XXX"), and the model
once invented a code instead of calling the tool for one — `persona.md` now forbids showing a code
that did not come back from the tool in that same turn.

## 2026-08-08 — Grounding, after three exchange rates for one day

The first live Discord session produced three different answers for the same day's exchange rate,
each claiming sources that were never consulted (35b). Temperature became a property of the role
rather than one global value — `router` dropped to 0, since every onboarding helper runs on it and
sampling randomness had already written a model's own reasoning into a stored city (item 33f).
Tool use became visible in the log for the first time, closing a real gap: an answer could not be
told apart from a fabrication after the fact, because tool messages are ephemeral by design.
`persona.md` gained the grounding rule directly: never state a figure that changes over time
without a search in the same turn, never claim to have consulted sources when no tool ran. Forcing
a search with `tool_choice` was considered and rejected for now — it needs knowing beforehand that
a question needs it, which costs a call on every turn for a case that was still occasional; the
question returned later as item 35j once the persona rule alone stopped being enough.

## 2026-07-23 to 2026-07-30 — Hardening the first real channel

Discord removed the CLI's `input()` confirmation, so several defenses had to exist for the first
time (item 34's early sub-items). A length cap and a token-bucket rate limit, both ahead of any
model call. Every LLM-facing prompt — eight of them — had user input fenced against embedded tags,
with a data-not-instructions line, closing a prompt-injection path that had never been named
before. Distillation gained a deterministic anomaly guard: a pass proposing more than five new
facts or five retirements at once is rejected and logged, a cap in code that holds regardless of
whether the model obeys anything. And the human-in-the-loop confirmation on memory was redesigned
as auto-apply — `update_memory` split into a pure `analyze_memory` plus `apply_memory_changes`,
with every change reversible by soft-delete and a `forget_fact` tool the model can only call with
an id the user actually saw. In-line "here's what I learned" notices after each pass were
evaluated and dropped: they broke the concise persona for a security value already covered by the
anomaly guard and the on-demand audit.

Days later, distillation stopped running on the reply's own critical path (item 34's background
distillation design). The split point is narrow on purpose: only the model call moves to a thread,
never the database write or the counters that decide whether the next trigger fires, because
resetting those in the background would let every turn arriving mid-pass launch its own overlapping
analysis. The accepted cost is real — the watermark advances before a pass is known to have
succeeded, so a failed pass loses that window for good — chosen over the alternative, which
reopens the exact race it was meant to close. The same week, SQLite moved to WAL plus a
`busy_timeout`, reprioritized out of the "hundreds of users" backlog once backgrounding distillation
made write-versus-write contention reachable with a single user.

## 2026-07-21 — A quota ceiling, not a bad model, behind the flip-flopping answers

An external review of response quality sent Tabris's flip-flopping and low-quality replies back to
one root cause: Gemini's free daily quota was exhausted by several model calls per turn, and
`general` silently fell back to a weaker model (35a). The real number, checked against the actual
account rather than documentation, was 20 requests a day on the high-end Flash models — the figure
the web quoted, "~1,500 RPD," did not apply to this tier at all; only `flash-lite` gave 500. Memory
distillation moved off `general` entirely into its own dedicated role so a future chat-model swap
could never silently change how memory gets built, and grounding rules were added to `persona.md`
the same day: when a search ran, its results outrank training knowledge and earlier turns, and a
contradiction with an earlier turn is corrected explicitly rather than blended in silence.

## 2026-07-10 to 2026-07-20 — Internet access, the first tool Tabris ever called

Item 33, built one new concept at a time. A function-calling loop first (`run_with_tools`), one
search provider (DuckDuckGo, no key, no quota) so the mechanism could be proven before it was
generalized. Then the abstraction: `core/search.py` mirrors the model-provider shape exactly — an
ordered list, normalized results, fallback on error or quota (D10) — and Tavily became the primary
once real runs showed DuckDuckGo's quality was the actual gap, not the mechanism. A real run
confirmed it: the exchange rate, a Bitcoin price and a World Cup result all came back concrete,
sourced and independently correct. Search stayed read-only, so no confirmation gate was needed,
unlike the file-write tools this item's broader original scope deferred to later. A freshness
problem was investigated and deliberately left alone: sites publish a daily figure titled "today"
on every page, so a generic query returns four different days under the same word, and the model
— correctly refusing to state an unconfirmed figure — says so. The fix is writing the actual date
into the query, which only the model can decide while asking; not built, to keep the persona's
instruction count down, since the failure announces itself and asking again resolves it.

## 2026-07-04 to 2026-07-07 — The channel-agnostic core is extracted for real

Item 32, in two parts. First, `config.LANGUAGE` — a global mutable — was eliminated in favor of a
`Session` dataclass keyed by `(channel, key)`, closing a bug that would have broken the moment two
users talked to Tabris at once. Second, the actual conversation engine (`handle_turn`,
`route_message`, `build_messages`) moved out of `main.py` into channel-agnostic `core/`, returning
only a reply string with no `print` or `input` anywhere in it — on a model error it rolls back the
pending user message and re-raises, leaving the adapter to decide what the user sees. `main.py`
afterward held only CLI-specific concerns: routing, the `exit` branch, and displaying a reply.
Discord, the next channel, would call the same functions unchanged.

## 2026-07-02 — A security review, acted on before the first real channel

An external code review named three real gaps, fixed the same day, ahead of Discord going live.
`deactivate_fact` had no ownership check at all — any user's id could retire any other user's
fact — closed with a `WHERE user_id=?` filter plus a second layer that drops any retire-id the
model proposes that was not actually shown to it. The `OpenAI` client was being recreated on every
call with no timeout, so a single hung provider could stall a turn for the full length of every
fallback in the chain; a lazily-built, cached client plus a 15-second timeout bounded the worst
case to roughly a minute instead of two. And the local `.env`, database and channel-identity file
were locked to owner-only permissions — a fix that would need repeating on every future deployment,
since file permissions are not git-tracked.

## 2026-07-01 — Tabris knows what time it is

Item 31: the system prompt gained a `## Current context` block with the date and time, formatted
in the user's own language through hardcoded weekday/month dictionaries rather than `strftime`,
which silently follows the server's OS locale instead of the user's. The same week, diagnostic
logging replaced a bare `print` on provider fallback — a `logging.getLogger` per module, configured
once at the real entry point so importing a module for a test never triggers it.

## 2026-06-29 to 2026-06-30 — Onboarding gets an identity, and memory a few quality fixes

Item 30 replaced a single hardcoded user with real identity: a `(channel, key)` pair, never a name
— access is by possession of the key, which structurally rules out impersonation and name
collisions before a multi-user model could exist at all. The CLI's key became an auto-generated
UUID in a gitignored file; an unknown key triggers onboarding, a known one loads straight in. The
same week, three quality bugs surfaced in the first real conversations: distillation was reading
the whole conversation including Tabris's own turns, and had "learned" facts about the assistant
from its own self-description — fixed by reading only user turns and telling the prompt explicitly
what to ignore; facts came back in English regardless of the user's language, because the prompt
never said which language to answer in; and the base model's generic "I can't have opinions"
disclaimer leaked through a persona that never said otherwise, fixed by rewriting the persona to
give reasoned opinions and stop reciting its own limitations unless asked.

## 2026-06-24 to 2026-06-26 — The router stops matching keywords, and the database gets a foundation

Two changes the same week, one built on the other. `core/db.py` gained a single `_connect` helper
that always turns on foreign-key enforcement and sets the row factory — before it, only `init_db`
set that pragma, so every other function opened a bare connection and silently accepted a fact or
message pointing at a user that did not exist (28b). `deactivate_fact` was then wired into the
distillation flow for the first time, closing the retire half of the fact lifecycle, with a
partial `UNIQUE` index catching exact-duplicate facts (semantically-equivalent duplicates with
different wording stayed an open, accepted gap) (28c). Separately, the router stopped matching
substrings — `"code"` inside `"encode"`, `"error"` in ordinary chat — and became a small LLM call
instead (29), the same lever that would later replace hand-written checks across the project
whenever enumerating the cases stopped scaling.

## 2026-06 — Zero local-model dependency (the pivot away from Ollama)

Items 21–26, Phase 2. Tabris started as a CLI talking to a local Ollama model with `memory.md` as
its whole system prompt (Phase 0–1, items 1–20: local install, a persistent-memory loop, and a
handful of small bug fixes — an f-string that printed literally, no backup before a memory write,
history growing unbounded). None of that survives in the code today; `memory.md` itself was
retired in Phase 3. The real turn was moving to API-based providers: `core/providers.py` with a
role→provider map and a fallback chain (D1, D2), multilingual UI strings, and tests mocking the
APIs instead of touching them. The exit criterion — Tabris running end-to-end with zero local
model dependency — is the line this project has not crossed back since.

The architecture sketched for this pivot was met, with names that drifted from the plan: the
planned `core/agent.py` became `core/conversation.py`, `core/router.py` never became its own
module (`route_message` stayed inside `core/conversation.py`), and `core/memory.py` split into
`core/memory_manager.py` (distillation) and `core/db.py` (storage) once the two turned out to be
separate concerns. Worth knowing only when an older document names one of the planned files.

## Before 2026-06-24 — Memory becomes a real database

Items 27 and 28, the start of Phase 3. `memory.md` — one file, one user, the whole thing sent as
the system prompt every turn — was replaced by SQLite: `users`, `facts` and `messages`, every table
carrying `user_id` from day one even though Tabris had exactly one user at the time, because
multi-user readiness was a design constraint from the start rather than a migration to do later.
Distillation gained a hybrid trigger — after five exchanges or five minutes of inactivity,
whichever came first — replacing the CLI's own exit-based trigger, which had no equivalent in a
channel that never really "exits."
