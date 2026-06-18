# Tabris — Master Plan

> **Purpose of this document:** single source of truth for the Tabris project.
> Any agent (or human) picking up this project should read this file first.
> Conversations with the user happen in **Spanish**; all code, commits and docs are in **English**.
> Working agreement: **one step at a time, wait for user confirmation, explain every command/concept.**

Last updated: 2026-06-17 (Phase 2 started)

---

## 1. Context & Goals

### Who
- User goes by **Rumpel**. Background: Scrum Master. Beginner programmer, learning by building.
- Based in Colombia. Currently without formal employment.

### Why (in priority order)
1. **Income, soon.** Generate income as an independent (freelance / SaaS) before runway ends.
2. **Employability fallback.** If the independent route doesn't sustain in time, the technical skills built here must be enough to get hired as a Dev / FDE / Technical PM.
3. **Learning.** Every task must teach transferable skills, not just produce output.
   Understanding > executing.

**Design consequence:** every hour invested must pay twice — advance the product AND build
portfolio/employable skills. Avoid work that does neither.

### What Tabris is
A personal, always-on, multi-agent AI assistant (JARVIS-style) that acts as **PM, Dev and Tutor**:
helps Rumpel manage and build his software project pipeline while teaching him along the way.
Long-term: serve Rumpel plus a small number of additional users, leveraging data captured by
the pipeline apps (habits, expenses, etc.). Designed to be **replicable**: anyone should be able
to clone the repo, add their own API keys, and run their own Tabris.

---

## 2. Hard Constraints

| Constraint | Implication |
|---|---|
| Minimal budget | Free tiers first; paid services only when clearly justified (< ~$10 USD/mo total) |
| Unstable power & internet at user's location | **No home-server.** Tabris must run in the cloud (cheap VPS or free tier) |
| User is a beginner | Prefer simple, well-documented tech; avoid premature complexity |
| No portfolio exists yet | Everything built must be portfolio-grade before being made public |
| First impressions matter | Repos go public only after passing the "Publishable Checklist" (§7) |

---

## 3. Key Decisions (with rationale)

| # | Decision | Rationale |
|---|---|---|
| D1 | **Migrate from local Ollama to API-based models** | Removes GPU/local dependency, enables cheap cloud hosting, costs are cents/month at current scale. Local Ollama is kept only as an offline lab/fallback. |
| D2 | **DeepSeek as primary brain; Groq + Gemini free tiers as secondary/fallback** | DeepSeek ≈ $0.14/$0.28 per 1M tokens (very cheap, strong quality, no free tier — prepaid). Groq free tier (~14K req/day) and Gemini free tier cover simple tasks and outages at $0. DeepSeek uptime is lower than majors → fallback is required, not optional. |
| D3 | **Provider/role mapping lives in `config.py`; secrets live in `.env`** | Replicability: clone → copy `.env.example` to `.env` → add keys → run. API keys must NEVER be committed (bots scan GitHub for leaked keys within minutes). `.env` is gitignored; `.env.example` documents the required variables. |
| D4 | **Telegram bot as first interface** | Free, unlimited, bot created in minutes via @BotFather, no business verification, works via polling (no public webhook/domain needed). WhatsApp is deferred: requires Meta Business verification, dedicated number, and bills business-initiated template messages from the first send — revisit when there are real Colombian users (WhatsApp is the natural channel there). |
| D5 | **Channel-agnostic core** | Tabris logic (routing, memory, agents) must not know whether input came from CLI or Telegram. Channels are thin adapters. Adding WhatsApp later = adding an adapter, not rewriting. |
| D6 | **Hosting: cheap VPS (Hetzner/Contabo, ~$4–6/mo) or free tier (Oracle Always Free / Fly.io)** | With inference via API, Tabris is a lightweight Python service. Decision on exact provider deferred to Phase 4; develop locally until then. |
| D7 | **SQLite for structured storage** | Free, serverless, file-based, ships with Python. Used for per-user memory/profiles and for the pipeline apps. Skills transfer directly to any SQL job requirement. |
| D8 | **Pipeline focus: 2 active projects max; nothing deleted, everything backlogged** | Two finished projects beat seven half-built ones. See prioritized matrix in §6. |
| D9 | **Portfolio is a roadmap phase, not a side effect** | Public repo + serious README + deployed demo + posts documenting the journey. The "document everything" rule converts into LinkedIn/blog content. |

---

## 4. Target Architecture

### 4.1 Current state (v0 — local CLI)
```
tabris.py (input() loop)
  ├── route_message()      → keyword router → llama3.1:8b | qwen2.5-coder:7b (Ollama)
  ├── memory.md            → single markdown file, injected as system prompt
  └── memory_manager.py    → LLM proposes section updates, human confirms, file overwritten
```

### 4.2 Target state (v1 — cloud, API-based)
```
[Telegram adapter]──┐
[CLI adapter]───────┤
                    ▼
              core/agent.py        ← channel-agnostic conversation engine
                    │
        ┌───────────┼────────────────┐
        ▼           ▼                ▼
  core/router.py  core/memory.py   core/providers.py
  (role → agent)  (SQLite-backed)  (DeepSeek | Groq | Gemini | Ollama)
                                       ▲
                              config.py + .env (keys)
```

**Provider abstraction (`core/providers.py`):** one function `chat(role, messages)` that looks up
`config.AGENT_ROLES[role]` → provider + model, calls the right API (all are OpenAI-compatible or
near-identical), and falls back to the next provider on error. Future specialized agents
(research, documents, images) are added as new roles in the same map.

**Config shape (sketch):**
```python
# config.py — structure, committed to git
AGENT_ROLES = {
    "general":  {"provider": "deepseek", "model": "deepseek-chat",   "fallback": "groq"},
    "code":     {"provider": "deepseek", "model": "deepseek-chat",   "fallback": "groq"},
    "router":   {"provider": "groq",     "model": "llama-3.1-8b-instant"},  # cheap/free, fast
    # future: "research", "documents", "images" — added by strength, not all at once
}
# .env — secrets, NEVER committed          # .env.example — template, committed
DEEPSEEK_API_KEY=sk-...                    DEEPSEEK_API_KEY=
GROQ_API_KEY=gsk_...                       GROQ_API_KEY=
GEMINI_API_KEY=...                         GEMINI_API_KEY=
TELEGRAM_BOT_TOKEN=...                     TELEGRAM_BOT_TOKEN=
```

### 4.3 Memory re-architecture
Evolution path — build the step you need, not the whole ladder:

| Stage | Storage | When |
|---|---|---|
| M0 (now) | `memory.md`, single user, whole file as system prompt | Keep during Phase 1–2 |
| M1 | SQLite: `users`, `facts` (persistent profile/preferences), `messages` (recent history). System prompt assembled from facts + last N messages. | Phase 3 — when Telegram lands (Telegram gives you user IDs for free) |
| M2 | Per-user profiles + per-project context; summarization of old history | When a second real user exists. **Do not build before.** |
| M3 (candidate) | Graph / GraphRAG memory: facts stored as entities + relations, retrieval by traversing connections (or plain embeddings-RAG as the cheaper precursor). | **Only if M1/M2 prove insufficient.** Entry criteria, ALL must hold: (1) plain embeddings-RAG over `facts` returns disconnected fragments the model can't relate on its own; (2) more than one real user with richly interrelated facts; (3) a need to explain *why* a memory was recalled. Until then this is over-engineering — see §9 scope-creep risk. Cheaper middle ground reachable from M1: a `fact_links(fact_id, related_fact_id, relation)` table = navigable relations on SQLite, no graph DB. |

Principles: persistent facts ≠ conversation history (separate tables); every memory write keeps
a backup or is transactional; human-in-the-loop confirmation stays for profile-level changes.

### 4.4 Context window management (applies at every stage)
- History sent to the model must be **bounded**: system prompt + last N exchanges (start N=10).
- Reason: providers/local models truncate silently from the top when context overflows — the
  first thing lost is the system prompt (identity + memory). This is the root cause of past
  "model forgets who it is" issues.

---

## 5. Roadmap

Single consecutive sequence for the whole project. Completed items are marked ✅;
pending ones ⬜. `> Exit criterion` lines define when a phase is done.

### Phase 0 — Environment & first prototype  ✅
1. ✅ Ubuntu + Ollama + GPU working
2. ✅ Local models installed (llama3.1:8b, qwen2.5-coder:7b)
3. ✅ Python venv at ~/Projects/tabris
4. ✅ First Python–Ollama connection working
5. ✅ hello_tabris.py with personality and system prompt
6. ✅ memory.md created as system prompt
7. ✅ tabris.py with persistent memory and conversation loop
8. ✅ start_tabris.sh working on native Linux
9. ✅ Project pushed to GitHub (private repo)
10. ✅ config.py created for environment configuration

### Phase 1 — Stabilize & complete base system  🔧 in progress
11. ✅ requirements.txt added
12. ✅ try/except error handling in tabris.py main loop
13. ✅ replace_section() bug fixed in memory_manager.py
14. ✅ Unit tests for replace_section() and route_message()
15. ✅ update_memory() complete — 6-scenario test coverage + fix for silent bug when section is None

Pending fixes (expert code review, 2026-06-10) — small, high-learning-value tasks:

| # | Fix | Detail | Status |
|---|---|---|---|
| 16 (F1) | **f-string bug in `tabris.py`** | `print(f"\n" + config.AGENT_NAME + " ({model}): {reply}\n")` — only the first literal is an f-string, so `{model}` and `{reply}` print literally. Fix: `print(f"\n{config.AGENT_NAME} ({model}): {reply}\n")`. | ✅ |
| 17 (F2) | **Backup before memory writes** | `update_memory()` overwrites `memory.md` directly → data-loss risk if the model output is malformed and the user confirms. Before writing, copy current file to `memory.md.bak` (e.g. `shutil.copy2`). | ✅ |
| 18 (F3) | **Bound conversation history** | `conversation_history` grows without limit → silent truncation drops the system prompt (see §4.4). Keep system prompt + last N messages when calling the model. Done via pure `build_messages()` helper (`history[:1] + history[1:][-MAX_HISTORY*2:]`); `num_ctx` now passed to `ollama.chat`; new config `MAX_HISTORY=10`, `NUM_CTX=8192`. Full history still saved at exit. 3 tests added. **Note:** rolling-summary memory deferred to Phase 2/3 (depends on summarizer reliability — weak on local 8b; viable on API models + fits M1). | ✅ |
| 19 (F4) | **Use `config.MEMORY_PATH` everywhere** | `load_memory()` hardcodes `"memory.md"` default instead of `config.MEMORY_PATH`. | ✅ |
| 20 (F5) | **Harden `parse_memory_update()`** | Only supports one section per session; breaks if the model proposes 2+ sections or adds text outside the format. Minimum: detect and reject malformed responses with a clear message instead of corrupting parsing. Add tests for malformed inputs. | ✅ |

> F6 (router false positives) and F7 (graceful exit + streaming) were relocated to Phase 3, where they are naturally resolved (see items 29 and 31). All Phase 1 fixes above are ✅.

### Phase 2 — API migration (the pivot)
23. ✅ Create `.env` + `.env.example` + add `python-dotenv`; load keys in `config.py`.
24. ⬜ Add `core/providers.py` with the role→provider map and `chat()` abstraction (D2/D3).
25. ⬜ Migrate `tabris.py` and `memory_manager.py` to use `chat()` instead of `ollama.chat()`. Keep `ollama` as one more provider in the map (offline fallback). Rename `tabris.py` → `main.py` here (agent name lives in `config.py`; the entry-point file should be generic).
26. ⬜ Implement provider fallback on error (try primary → fallback → friendly error).
27. ⬜ Update tests; add tests for provider selection and fallback (mock the APIs).
- ⬜ **Multilingual UI strings:** create `strings.py` with message dictionary (`es` / `en`) + `LANGUAGE = "auto"` in `config.py`. Replace all hardcoded user-facing strings in `main.py` and `memory_manager.py` with `MESSAGES[lang][key]` lookups. Language defaults to `config.LANGUAGE`; auto-detection by first message deferred to Phase 3.
> Exit criterion: Tabris runs end-to-end with zero local model dependency.

### Phase 3 — Telegram + memory v1
28. ⬜ Telegram bot via @BotFather + `python-telegram-bot` (polling mode — no webhook needed).
29. ⬜ Refactor into channel adapters (D5): CLI and Telegram both call the same core.
- ⬜ **CLI UX (F7 remainder):** handle `Ctrl+C` (KeyboardInterrupt) so memory still saves on exit; enable streaming responses for perceived speed. Belongs with the CLI adapter work above.
30. ⬜ Memory M1: SQLite schema (`users`, `facts`, `messages`); migrate content of `memory.md`.
31. ⬜ LLM-based router (replaces keyword router) using the cheap/free "router" role. Router classifies intent: `code`, `general`, or `exit`. **Resolves F6** (keyword false positives) and the exit-intent part of **F7** (replaces hardcoded exit phrases).
32. ⬜ Session TODO list + onboarding flow for new users (reads/writes `facts`). Detect language from first user message and store as a `fact` — replaces the hardcoded `LANGUAGE` config from Phase 2; Tabris remembers language preference between sessions.

### Phase 4 — Deploy (always-on)
33. ⬜ Choose host: compare Oracle Always Free vs Hetzner (~$4.5/mo) vs Fly.io free allowance.
34. ⬜ Deploy as a systemd service or Docker container; secrets via environment variables.
35. ⬜ Basic ops: logs, restart-on-failure, weekly SQLite backup (cron + copy).
> Exit criterion: Rumpel talks to Tabris from his phone with his PC off.

### Phase 5 — Portfolio (transversal: starts during Phase 2)
36. ⬜ Write a serious `README.md` for Tabris: what/why, architecture diagram, decisions (link this plan), setup guide ("clone → .env → run"), screenshots/GIF of the Telegram bot.
37. ⬜ Security pass: confirm no secrets in git history (if any were ever committed, rotate keys).
38. ⬜ Make repo public **only after passing the Publishable Checklist (§7)**.
39. ⬜ First LinkedIn/blog post: "Building my own JARVIS as a career-change project" — the "document everything" rule becomes content. Target: 1 post per completed phase.
40. ⬜ GitHub profile README + pin Tabris.

### Phase 6 — First pipeline project
41. ⬜ Habit & Task Tracker (see §6): CLI + SQLite first, then minimal API (FastAPI), then it becomes Tabris's first **tool** (Phase 7 preview: Tabris reads/writes the tracker on your behalf).

### Phase 7 — Multi-agent & tools (deferred)
42. ⬜ Tool use with human-in-the-loop (CRUD on project files, tracker access).
43. ⬜ PM / Dev / Tutor role structure on top of the role→provider map.
44. ⬜ Specialized agents by strength (research, documents, images) as budget allows.

---

## 6. Project Pipeline — Prioritized Backlog

Scoring 1–5 (higher = better) on: **V**iability (can Rumpel build it soon), **M**onetization
potential, **B**udget fit (cost to build/run), **C**omplexity (5 = simplest). Nothing is deleted.

| # | Project | V | M | B | C | Total | Role in the plan |
|---|---|---|---|---|---|---|---|
| 1 | Habit & Task Tracker | 5 | 2 | 5 | 5 | 17 | **Active #1.** Learning vehicle: CRUD, SQLite, API. Becomes Tabris's first tool. Weak as standalone product (saturated market) — its value is skills + integration. |
| 2 | Employment contract liquidator (Colombia) | 4 | 4 | 5 | 4 | 17 | **Active #2 / flagship.** Local niche, real demand (employees & small employers), little quality competition, shows domain expertise — strongest portfolio piece and best SaaS bet. |
| 3 | Income tax calculator (Colombia) | 4 | 4 | 5 | 3 | 16 | Backlog — natural sibling of #2 (shared domain & audience). Strong candidate to bundle with #2 into one "Colombian payroll/tax tools" product. Seasonal demand spike (tax season). |
| 4 | Expense & budget tracker | 4 | 2 | 5 | 4 | 15 | Backlog — good second data source for Tabris-as-assistant; weak standalone monetization. |
| 5 | Account reconciliation tool | 3 | 4 | 4 | 2 | 13 | Backlog — monetizable (freelance accountants/SMBs) but needs domain depth and real user input. Revisit after #2 ships and brings contact with that audience. |
| 6 | Reading app | 3 | 2 | 4 | 3 | 12 | Backlog — personal value, crowded market. |
| 7 | Streaming platform | 1 | 2 | 1 | 1 | 5 | On hold (as already agreed) — infrastructure cost and complexity are incompatible with current constraints. |

**Sequence:** #1 (fast, foundational) → #2 (flagship) → re-evaluate with real data.
**Income reality check:** SaaS revenue is a months-long bet. The faster income paths this plan
feeds are (a) freelance gigs enabled by a visible portfolio, and (b) Dev/FDE employability.
Treat #2's launch as a learning+portfolio milestone first, revenue second.

---

## 7. Publishable Checklist (gate for making anything public)

A repo/demo goes public only when ALL are true:
- [ ] Works end-to-end for its core use case (no "coming soon" in the main flow)
- [ ] `README.md` complete: what, why, architecture, setup, usage, screenshots
- [ ] No secrets in code **or git history**; `.env.example` provided
- [ ] Tests exist and pass (`python -m unittest` clean)
- [ ] Code in English, reasonably clean (a beginner-honest standard, not perfection)
- [ ] If it has a UI/bot: a reviewer can try it in < 2 minutes (demo, GIF, or test bot)

---

## 8. Working Agreements (unchanged — binding for any agent on this project)

- One step at a time; wait for user confirmation before the next step.
- Always explain what each command/concept does (the user is learning — that's the point).
- Code and documentation in English; conversation in Spanish.
- Minimal budget; prefer free/local tools; flag any cost before incurring it.
- Never assume — confirm context first. Cite sources or mark inferences as such.
- Document everything for future replication.
- Human-in-the-loop for anything destructive (memory writes, file changes, deletions).

## 9. Known Risks

| Risk | Mitigation |
|---|---|
| DeepSeek outages (~97% uptime) | Provider fallback (D2) is mandatory in `core/providers.py` |
| API price changes | Role→provider map makes switching a one-line change; re-check prices quarterly |
| Scope creep (7 projects, multi-agent dreams) | §6 sequence + "do not build before the second user exists" rule (M2) |
| Leaked secrets | `.env` pattern + history check before going public + key rotation if in doubt |
| Burnout / runway pressure | Portfolio milestones every phase = visible progress even if revenue lags |
