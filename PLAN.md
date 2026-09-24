# Tabris — Master Plan

> **What goes in this document:** what Tabris is, who it is for, and what it deliberately is not.
>
> Not here: what is pending (`docs/roadmap.md`), why something was decided (`docs/decisions.md`),
> what happened (`docs/log.md`), the principles this project does not negotiate
> (`memory/constitution.md`), how it is built (`CONTRIBUTING.md`). Who this is built for, the
> constraints every project inherits, and the gate a repository passes before going public are
> not Tabris's to hold — they live in the workspace `PLAN.md`, one level above this repository.
>
> Owner: Rumpel · Last updated: 2026-09-24

---

## 1. What Tabris is

A personal, always-on AI assistant (JARVIS-style) for Rumpel's **day-to-day** (plus a small number
of beta-testers). **Not** primarily a tool to build the liquidador — Claude/Gemini are more robust
for heavy development and remain the tools for that. Tabris's differential is **not raw reasoning**
but: persistent personal memory, being **his** (owned, multi-user, replicable), always available on
his phone, and the input modalities he actually uses (text, voice, images, links). The
liquidador-building phase is Tabris's **dogfooding ground**: it runs in daily use there and gathers
feedback (Rumpel's own + beta-testers') to be refined from in the next round.
Long-term: serve Rumpel plus a small number of additional users, leveraging data captured by
the pipeline apps (habits, expenses, etc.). Designed to be **replicable**: anyone should be able
to clone the repo, add their own API keys, and run their own Tabris.

---

## 2. Phases

What is pending, item by item, is `docs/roadmap.md`. This table is the outcome each phase is
for, at a glance.

> **MVP definition (functional for daily use):** persistent memory + internet + Discord + audio
> input + image input + always-on deploy. Met except for the two open slices of image input and
> the always-on items still in `docs/roadmap.md`.

| Phase | Outcome | Status |
|---|---|---|
| 0 — Environment & first prototype | A local CLI assistant on Ollama, with a persistent-memory loop | ✅ |
| 1 — Stabilize & complete base system | Early bugs fixed; conversation history bounded for the first time | ✅ |
| 2 — API migration | Zero local-model dependency; provider fallback (D1, D2) | ✅ |
| 3 — Memory v1 + Internet + Discord | SQLite memory, web search, Discord as the first real channel | 🔶 — `docs/roadmap.md` #1–10 |
| 4 — Always-on | Deploy as a system service; Tabris speaks first | 🔶 — `docs/roadmap.md` #11–19 |
| 5 — Portfolio (Tabris's part) | Public repo, README, a git history clean of personal data | ✅ — further presentation is the workspace `PLAN.md`'s "Portfolio site" |

> Freeze exit criterion (Phase 4): Rumpel talks to Tabris from his phone with his PC off, and
> Tabris reaches him at an agreed hour without being asked.

---

## 3. Known Risks

| Risk | Mitigation |
|---|---|
| DeepSeek outages (~97% uptime) | Provider fallback (D2) is mandatory in `core/providers.py` |
| API price changes | Role→provider map makes switching a one-line change; re-check prices quarterly |
| Leaked secrets | `.env` pattern + history check before going public + key rotation if in doubt. (Verified 2026-06-24: `.env` never in git history — clean.) |
| Prompt injection in memory distillation | Raw conversation text is embedded in the distillation prompt; a user could type `HAS_NEW_FACTS: yes` / `FACTS:` lines to spoof the parser format. The human `si/no` gate was removed by auto-apply (2026-07-23) → this risk is now **live**; mitigation is the item-34 delimiting bullet (fence user turns in the 4 LLM-facing prompts), now higher priority. (Code review 2026-06-24.) |
