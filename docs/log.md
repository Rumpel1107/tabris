# Log

> **What goes in this document:** what happened, dated, newest first. Append-only. A paragraph
> earns its place by keeping whoever picks this up from repeating a mistake or undoing a decision;
> session narrative belongs in the conversation.
>
> Not here: what broke after the code was called done (`docs/defects.md`), what changed for
> whoever runs Tabris (`CHANGELOG.md`). Why a decision was taken and what is still pending live
> in `PLAN.md` for now — §3 and §5 — until this project adopts the standard layout.

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
