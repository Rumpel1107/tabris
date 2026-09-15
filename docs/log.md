# Log

> **What goes in this document:** what happened, dated, newest first. Append-only. A paragraph
> earns its place by keeping whoever picks this up from repeating a mistake or undoing a decision;
> session narrative belongs in the conversation.
>
> Not here: what broke after the code was called done (`docs/defects.md`), what changed for
> whoever runs Tabris (`CHANGELOG.md`). Why a decision was taken and what is still pending live
> in `PLAN.md` for now — §3 and §5 — until this project adopts the standard layout.

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
