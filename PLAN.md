# Tabris — Master Plan

> **Purpose of this document:** single source of truth for the Tabris project.
> Any agent (or human) picking up this project should read this file first.
> Conversations with the user happen in **Spanish**; all code, commits and docs are in **English**.
> Working agreement: **one step at a time, wait for user confirmation, explain every command/concept.**

Last updated: 2026-08-12

---

## 1. Context & Goals

### Who
- User goes by **Rumpel**. Background: Scrum Master. Beginner programmer, learning by building.
- Based in Colombia. Currently without formal employment.

### Why (in priority order)
1. **Independent income — the definition of success.** Generate revenue as an independent (SaaS / product / freelance) before runway ends. This is THE goal.
2. **Learning that serves #1.** Every hour learns something transferable, but learning is now subordinate to shipping a sellable product.
3. **Employability — Plan B financing only.** A technical job is a fallback IF the support fund is exhausted, NOT a parallel objective. Do not optimize for it..

### What Tabris is
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
| D4 | **Discord bot as first interface** (updated 2026-07-20) | Rumpel's testers are the community with access to his game servers, who already live on Discord — that's where adoption/usage is. Infra-light like Telegram: the bot connects via the gateway/WebSocket (`discord.py`/`py-cord`), no public webhook/domain needed; enable the Message Content Intent. Telegram stays a supported second channel (Rumpel wants both available; cheap to add via the agnostic core — item 34d). WhatsApp still deferred: requires Meta Business verification, dedicated number, and bills business-initiated template messages from the first send — revisit when there are real Colombian users. |
| D5 | **Channel-agnostic core** | Tabris logic (routing, memory, agents) must not know whether input came from CLI or Telegram. Channels are thin adapters. Adding WhatsApp later = adding an adapter, not rewriting. |
| D6 | **Hosting: cheap VPS (Hetzner/Contabo, ~$4–6/mo) or free tier (Oracle Always Free / Fly.io)** | With inference via API, Tabris is a lightweight Python service. Decision on exact provider deferred to Phase 4; develop locally until then. |
| D7 | **SQLite for structured storage** | Free, serverless, file-based, ships with Python. Used for per-user memory/profiles and for the pipeline apps. Skills transfer directly to any SQL job requirement. |
| D8 | **Pipeline focus: 2 active projects max; nothing deleted, everything backlogged** | Two finished projects beat seven half-built ones. See prioritized matrix in §6. |
| D9 | **Portfolio is a roadmap phase, not a side effect** | Public repo + serious README + deployed demo + posts documenting the journey. The "document everything" rule converts into LinkedIn/blog content. |
| D10 | **Search APIs use the same abstraction + fallback as the model providers** | Internet access is a tool, not a new brain. `core/search.py` mirrors `core/providers.py`: an ordered `SEARCH_PROVIDERS` list in `config.py` (Tavily → Brave → DuckDuckGo), keys in `.env`, one `search(query)` that tries each in order, falls through on error or quota (`429`/`402`), and normalizes every provider's response to a common `{title, url, content}` shape. DDG (no key, no quota, lower quality) is the last-resort backup. Swapping/reordering providers = a one-line config change; zero lock-in. |

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
| M3 (candidate) | Graph / GraphRAG memory: facts stored as entities + relations, retrieval by traversing connections (or plain embeddings-RAG as the cheaper precursor). | **Only if M1/M2 prove insufficient.** Entry criteria for the full graph, ALL must hold: (1) plain embeddings-RAG over `facts` returns disconnected fragments the model can't relate on its own; (2) more than one real user with richly interrelated facts; (3) a need to explain *why* a memory was recalled. Until then this is over-engineering — see §9 scope-creep risk. Cheaper middle ground reachable from M1: a `fact_links(fact_id, related_fact_id, relation)` table = navigable relations on SQLite, no graph DB. **Separate, lower-bar trigger for the embeddings-RAG precursor alone (identified 2026-07-08):** `get_facts()`/`build_system_prompt()` inject every active fact into the system prompt with no cap, unlike conversation history (§4.4). If facts volume alone risks overflowing the context window — regardless of any relational need — that alone justifies moving to embeddings-RAG top-K retrieval, without waiting on the 3 criteria above (those gate the full graph, not this precursor). |

Principles: persistent facts ≠ conversation history (separate tables); every memory write keeps
a backup or is transactional; memory writes auto-apply (2026-07-23) — reversibility (soft-delete +
`retired_at`) and the user-facing `forget_fact` flow replace the blocking confirmation.

**Fact lifecycle rule:** facts are append-only — never edited in place, never hard-deleted.
A fact that becomes false or obsolete is *retired* via soft-delete (`is_active=0`), preserving
history. A change of information = retire the stale fact + insert the corrected one (never an
in-place `UPDATE` of `content`). Only `is_active=1` facts feed the system prompt. Obsolescence is
detected during distillation (the LLM receives known facts *with their `id`* and returns two sets:
new facts to add + `id`s to retire, with reason); additions and retirements auto-apply (2026-07-23,
Hermes-style — the memory-role model is the quality safeguard); the user audits via the numbered
facts list and prunes any fact with the `forget_fact` tool (soft-delete, reversible).

### 4.4 Context window management (applies at every stage)
- History sent to the model must be **bounded**: system prompt + last N exchanges (start N=10).
- Reason: providers/local models truncate silently from the top when context overflows — the
  first thing lost is the system prompt (identity + memory). This is the root cause of past
  "model forgets who it is" issues.

---

## 5. Roadmap

Single consecutive sequence for the whole project. Completed items are marked ✅;
pending ones ⬜. `> Exit criterion` lines define when a phase is done.

> **MVP definition (functional for daily use):** persistent memory (done) + internet
> (`web_search`/`web_fetch`) + Discord + audio input + image input + always-on deploy.

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

### Phase 1 — Stabilize & complete base system  ✅
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

### Phase 2 — API migration (the pivot)  ✅
21. ✅ Create `.env` + `.env.example` + add `python-dotenv`; load keys in `config.py`.
22. ✅ Add `core/providers.py` with the role→provider map and `chat()` abstraction (D2/D3).
23. ✅ Migrate `tabris.py` and `memory_manager.py` to use `chat()` instead of `ollama.chat()`. Keep `ollama` as one more provider in the map (offline fallback). Rename `tabris.py` → `main.py` here (agent name lives in `config.py`; the entry-point file should be generic).
24. ✅ Implement provider fallback on error (try primary → fallback → friendly error).
25. ✅ Update tests; add tests for provider selection and fallback (mock the APIs).
26. ✅ Multilingual UI strings: `core/strings.py` with `es`/`en` dictionary + `LANGUAGE = "es"` in `config.py`; all user-facing strings in `main.py` and `memory_manager.py` use `msg(key, **kwargs)`. Auto-detection deferred to item 30.
> Exit criterion: Tabris runs end-to-end with zero local model dependency.

### Phase 3 — Memory v1 + Internet + Discord
27. ✅ Memory M1: SQLite schema (`users`, `facts`, `messages`); migrate content of `memory.md`. Schema includes `user_id` on every table from day one — Tabris targets up to ~10 users; multi-user readiness is a design constraint, not a future migration.
28. ✅ Memory trigger (hybrid): run `update_memory()` after every 5 exchanges OR after 5 minutes of inactivity — whichever comes first. Both counters reset after each trigger. Replaces the CLI exit-based trigger, which does not exist in Telegram.
28b. ✅ DB layer hardening (do before 28c — it is the foundation under every DB write that 28c adds). Source: deep code review 2026-06-24. Scenarios to satisfy:
   - **FK enforcement.** `PRAGMA foreign_keys = ON` is per-connection and defaults to OFF; today only `init_db` sets it, so every other `core/db.py` function opens a bare connection and the `REFERENCES users(id)` constraints are silently NOT validated (a `fact`/`message` with a non-existent `user_id` inserts cleanly). Fix: a single `_connect(db_path)` helper that always sets the pragma + `row_factory = sqlite3.Row`, used by every db function.
   - **No connection leaks.** Functions use `conn = sqlite3.connect(...)` … `conn.close()` with no `with`/`try-finally`, so an exception mid-function leaks the connection — accumulates in an always-on service. Fix: `with sqlite3.connect(...)` (auto commit/rollback) or the `_connect` helper inside `try/finally`.
   - **Centralize trigger constants.** Move `MEMORY_TRIGGER_EXCHANGES` and `MEMORY_TRIGGER_SECONDS` from `main.py` to `config.py` (one tuning location, consistent with the rest of config).
   - **TDD test:** inserting a fact/message with a non-existent `user_id` must raise `IntegrityError` (today it silently succeeds — that test is the proof the pragma is now live).
28c. ✅ Memory CRUD completion (do before item 29): wire `deactivate_fact` into the distillation flow so Tabris can retire facts that became false/obsolete, closing the read-create-**retire** cycle. `update_memory` proposes additions **and** retirements (`id`s, with reason) in one human-confirmed step; a changed fact = retire stale + insert corrected. No in-place edit, no hard delete. Implements the §4.3 fact-lifecycle rule. Currently `deactivate_fact` exists and is unit-tested but is not wired into any flow. Additional scenarios folded in from the code review 2026-06-24 (this item rewrites `update_memory`, so do them in the same pass — don't touch the function twice):
   - **Dedupe facts.** "Only new facts" is a request to a non-deterministic model, not a guarantee — nothing in the schema stops the same fact being saved twice across sessions, and the "What I know about the user" block degrades over time. Fix: partial UNIQUE index on `(user_id, content)` WHERE `is_active=1`. ✅ Done. Known limitation: the index only catches exact string duplicates — semantically equivalent facts with different wording (e.g. "Trabaja en TaxL" vs "Trabaja en el proyecto TaxL") are not caught; that requires embeddings (M3, deferred).
   - **Analyze the delta, not the whole history (cost).** `conversation_history` grows unbounded in-session (only what is *sent* to the model via `build_messages` is bounded, not the list itself). Re-serializing the FULL history into the distillation prompt every 5 exchanges = growing cost + re-analysis of already-processed messages. Fix: keep a watermark/index of the last analyzed message and distill only the delta since the last trigger. Aligns with the < $10/mo constraint (§2).
   - **e2e test:** retire a fact end-to-end and assert it drops out of the assembled system prompt (covers the `deactivate_fact` e2e gap noted in the review).
29. ✅ LLM-based router (replaces keyword router) using the cheap/free "router" role. Router classifies intent: `code`, `general`, or `exit`. **Resolves F6** (keyword false positives) and the exit-intent part of **F7** (replaces hardcoded exit phrases). Code review 2026-06-24 re-confirmed the substring bug (`"code"` matches inside `"encode"/"decode"`, `"error"` is common in normal chat → over-routes to `code`); the interim word-boundary regex patch is intentionally skipped because this item lands next and replaces the keyword router outright.
30. ✅ Onboarding flow + channel-key identity. Replaces hardcoded `config.USER_NAME`/`config.LANGUAGE`. Identity is a `(channel, key)` pair, not the name: a new `user_channels` table maps each key to a `user_id`; the CLI key is an auto-generated UUID stored in a gitignored `tabris_client_id` file. On startup, look up the key → known key loads the user; unknown key triggers onboarding (ask name, detect language from first message, confirm once, persist). Language lives in `users.language` (a profile column, updatable any time via `update_user_language`), NOT in `facts`. Name is a display label only (drop the `UNIQUE` constraint) — access is by possession of the key, never by name, which structurally prevents impersonation and name collisions. `find_user_by_name`/`get_or_create_user` retired (name-based lookup is insecure in the multi-user model). Extra beyond original scope: `extract_name` uses the router LLM to pull a clean name out of a full sentence reply (e.g. "Mi nombre es Mauricio" → "Mauricio").
30a. ✅ Memory distillation quality — extract only USER facts. `update_memory` feeds the whole conversation (including assistant turns) into the distillation prompt, so it "learns" facts from Tabris's own self-description (observed 2026-06-30: extracted "Tabris has capabilities…", "Tabris has limitations…" — noise about the assistant, not about the user). Fix (both): (1) distill only `role == "user"` turns from the delta; (2) strengthen the prompt to extract only durable facts ABOUT THE USER (preferences, data, projects) and explicitly ignore anything about the assistant or its capabilities. TDD: a conversation containing an assistant self-description yields zero facts about Tabris.
30b. ✅ Facts in the user's language. The `analysis_prompt` never specifies an output language, so facts come back in English even when `config.LANGUAGE == "es"` (observed 2026-06-30). Decision: facts are user-facing content (injected into the system prompt, shown in the si/no confirmation) → store them in the user's language. Fix: add a directive to produce `NEW_FACTS` in `config.LANGUAGE`. TDD: with language "es", a distilled fact comes back in Spanish.
30c. ✅ Persona gives reasoned opinions. The base model injects a generic "I can't make decisions or have personal opinions" disclaimer that is NOT in `persona.md` (observed 2026-06-30). Users do ask for opinions. Fix: rewrote persona.md — removed all coding-session rules (TDD, one-step-at-a-time, etc.), added concise-by-default, natural first-person tone, explicit instruction to give opinions and to not recite capability/limitation lists unless asked. Verified 2026-07-01: small talk is short and natural, opinions given without disclaimer, facts extracted are concrete and in Spanish.
31. ✅ Time awareness: inject current datetime into system prompt context. `build_system_prompt` takes an injectable `now=None` (defaults to `datetime.now()`, kept pure/testable); adds a `## Current context` block with the date/time. `format_datetime(dt, language)` formats it in the user's language via `WEEKDAYS`/`MONTHS` dicts in `strings.py` (locale-independent — `strftime` follows the OS locale, so day/month names are hardcoded es/en; migrate to `babel` if languages > 3). Verified 2026-07-01 in a real session.
31b. ✅ Diagnostic logging. `core/providers.py` uses `logger = logging.getLogger(__name__)`; the fallback print became `logger.warning(...)`. `config.LOG_LEVEL` (default `"INFO"`, from `.env`) + `logging.basicConfig(level=..., format=...)` called once in `main.py`'s `if __name__ == "__main__":` block, before `chat()`. User-facing messages stay on `print`/`msg`. Test: `assertLogs("core.providers", level="WARNING")` on fallback.
31c. ✅ Security/resilience fixes (code review 2026-07-02), done before Telegram (2026-07-02):
   - **IDOR in `deactivate_fact`** (`core/db.py`): `deactivate_fact(db_path, user_id, fact_id)` now filters `WHERE id=? AND user_id=?`. Second layer of defense: `update_memory` (`core/memory_manager.py`) has a new pure `filter_valid_retire_ids(retire_ids, known_facts)` that drops any `retire_id` not actually present in the `known_facts` shown to the LLM, before it's ever displayed for confirmation or passed to `deactivate_fact`. TDD tests on both layers (cross-user isolation in `test_db.py`, filtering in `test_memory_manager.py`).
   - **Provider clients recreated per call, no timeout** (`core/providers.py`): new `_get_client(provider)` builds each `OpenAI(...)` lazily (first use, not at import — avoids crashing on a provider with no key configured) and caches it in a module-level `_clients` dict; `_call_provider` reuses it. `config.PROVIDER_TIMEOUT = 15` (not 30 — with up to 4 providers in a fallback chain, e.g. role `code`, 30s each risked ~90-120s worst case; 15s keeps that under ~60s while still well above the plan's own 2-10s normal-latency estimate). Without this, a hung provider never raised, so the D2 fallback silently never triggered.
   - `chmod 600` on `.env`, `tabris.db`, `tabris_client_id` locally. Note: file permissions are OS-level, not git-tracked — this does NOT carry over to the VPS deploy; folded as an explicit step into item 37.
32. ✅ Refactor into channel adapters (D5): CLI and Telegram both call the same core.
    - Part 1: `config.LANGUAGE` global mutable state eliminated. Per-session state via `core/session.py`'s `Session` dataclass (`user_id`, `language`, `conversation_history`, `exchange_count`, `last_trigger_time`, `last_analyzed_index`), keyed by `(channel, key)`.
    - Part 2: channel-agnostic core extracted into `core/conversation.py` (`handle_turn`, `route_message`, `build_messages`, `should_trigger_memory`). `handle_turn(session, user_input, role, db_path)` returns only the reply string — no `print`/`input`; on a model error it rolls back the session's pending user message and re-raises (the adapter decides what to show). `main.py`'s CLI loop now only handles routing, the `exit` branch, and displaying the reply/error. `main.py` no longer defines any of the moved functions — only CLI-specific concerns (onboarding, language detection I/O, persona loading) remain there.
33. ✅ **Internet access via tool use** (first tool of the tool-use layer). All sub-items 33a–33f done and validated with real runs; the broader file/tracker-CRUD scope was split off to Phase 7 (items 48/49). Build order — one new concept per step:
    - **33a. ✅ (2026-07-10)** Function-calling loop: `providers.chat()` accepts `tools`; `core/search.py` (`web_search` via `ddgs`); `run_with_tools()` loop in `core/conversation.py`, wired into `handle_turn`. Verified with real runs (needed a `persona.md` tool-awareness fix for reliable use). DDG result-quality gap deferred to 33b/33c.
    - **33b. ✅ (2026-07-16)** Generalized behind `core/search.py` + `SEARCH_PROVIDERS` config list + fallback chain + result normalization (D10). `web_fetch` added, wired as a tool, and mentioned in `persona.md`. YouTube-transcript tool deferred (not built). Verified with real runs.
    - **33c. ✅ (2026-07-20, validated with a real run)** Tavily registered as the primary search provider (`_search_tavily` via httpx, Bearer auth, normalized to `{title, url, content}`); `SEARCH_PROVIDERS = ["tavily", "duckduckgo"]` — DDG stays as the last-resort backup. Real run: TRM, Bitcoin, and the 2026 World Cup result came back concrete, sourced, and correct (independently verified) — the DDG quality gap from 33e is closed. Brave deferred: a second paid provider is speculative until Tavily's quality/quota proves insufficient (§9 / item 50).
    - Search is read-only → **no HITL confirmation** (unlike file writes). File/tracker CRUD tools (the original, broader item-33 scope) are deferred to Phase 7 (items 48/49).
33d. ✅ (2026-07-16, validated with a real run) Onboarding friendliness. New `interpret_yes_no` (router LLM) infers affirmation instead of exact string match; `resolve_language` now injects `interpret_fn`/`detect_fn` and stays pure (fallback reuses `detect_language` on free text). Onboarding reordered in `chat()`: greet → detect+confirm language → ask name in that language → echo `onboarding_done`; language-detection block removed from the loop; first message only triggers onboarding (not answered). Real run confirmed a natural affirmative ("Esta perfecto, gracias.") resolves to `es`.
33e. ✅ (2026-07-17, validated with a real run) Timezone. New `users.location` + `users.timezone` columns (idempotent migration); onboarding asks the city, `resolve_timezone` (router LLM) maps it to an IANA id (validated via `ZoneInfo`, falls back to `UTC`); `build_system_prompt` treats `now` as UTC and converts with `astimezone(ZoneInfo(tz))`, and names the city in the prompt. Real run: server UTC (Fri 02:36) rendered as correct local time (Thu 21:36, jueves, UTC-5) with no mental offset or web lookup. Grounding (#2) reframed: the model searches (no fabrication) — the remaining weak/vague answers are DDG result quality → folds into 33c, not a `persona.md` fix. Per-turn `now` refresh stays scoped under item 34 (§ line ~226).
33f. ✅ (2026-07-18, validated with a real run) Normalize stored location. `extract_location` (LLM helper, few-shot + `Location:` cue, no fabrication) cleans the raw city answer before `create_user`; `is_timezone_ambiguous` judges whether the answer pins one timezone and, if not, `onboard_user` re-asks once (`ask_location_clarify`) and combines the answer instead of replacing it; `resolve_timezone` keeps receiving the raw/combined phrase for disambiguation. Real run: "Madrid" → re-ask → stored `Madrid, Cundinamarca`, timezone `America/Bogota`.
34. ✅ (hardening complete 2026-07-30; account linking split out to item 34e, unbuilt) Discord bot via the Discord Developer Portal + `discord.py`/`py-cord` (gateway/WebSocket — no public webhook needed, infra-light like polling). Enable the **Message Content Intent** so the bot reads message text (a toggle for a private server). Discord's numeric `user_id` is the channel key (free, stable) — register it in `user_channels` exactly like the CLI key. **Account linking (same human, multiple channels → one profile/context):** via a short-lived **link-code**, never by name. Flow: on an already-registered channel the user requests a code; entering it on the new channel inserts a `user_channels` row pointing the new `(channel, key)` to the existing `user_id`. The `user_channels` schema (item 30) already supports this with zero migration — multiple rows per `user_id`. Name-based linking is explicitly rejected (impersonation risk). First-real-remote-channel hardening from code review 2026-07-02 (the CLI's `input()` confirmation disappears; all channel-agnostic, reused by any later channel like Telegram):
   - ✅ (2026-07-28) Message length cap + per-user rate limit, both in `safe_handle_turn` before any model call (channel-agnostic): length cap rejects input over `config.MESSAGE_MAX_CHARS` (4000) with `message_too_long`; token-bucket rate limit (`MESSAGE_RATE_MAX`/`MESSAGE_RATE_SECONDS`, state on `Session.rate_tokens`/`rate_last_refill`) rejects with `rate_limited` when the bucket is empty.
   - ✅ (2026-07-23) Delimit user input in the LLM-facing prompts — `fence_user_input` helper in `core/prompt.py` (neutralizes embedded tags, case-insensitive) applied to all 8 LLM-facing prompts: the distillation prompt (memory_manager.py) plus `route_message` (core/conversation.py) and `detect_language`, `extract_name`, `resolve_timezone`, `is_timezone_ambiguous`, `extract_location`, `interpret_yes_no` (main.py), each with a data-not-instructions line. `extract_location`'s few-shot examples are fenced too, for format consistency with the real input. 146 tests passing (7 new, asserting the fenced text reaches the model prompt).
   - ✅ (2026-07-23) Anomaly guard on distillation: `analyze_memory` rejects + logs a pass proposing more than `config.MEMORY_MAX_NEW_FACTS`/`MEMORY_MAX_RETIRE_IDS` (5/5) new facts/retires in one shot — deterministic cap in code, catches mass injection regardless of model obedience. `MemoryChanges.rejected` flag distinguishes "nothing to change" from "rejected anomalous pass" and drives the server-side log line only — the user-facing notice it originally appended was removed on 2026-07-30 (see the bullet below). 150 tests passing (4 new).
   - ❌ Learning transparency (evaluated + dropped 2026-07-28): in-line "here's what I learned" notices after each auto-applied pass break conversational flow (contradict item 30c's concise persona) for low security value — distillation reads only user turns (no external-content vector), facts are user-scoped (self-harm only), and mass injection is already caught by the anomaly guard. Visibility kept via server-side log + on-demand audit (list facts + forget).
   - ✅ (2026-07-23, validated with real runs on CLI + Discord) Memory HITL redesigned as auto-apply: `update_memory` split into pure `analyze_memory` + `apply_memory_changes` (no `print`/`input` in core); `handle_turn` auto-applies and logs. `facts.retired_at` column (idempotent migration) makes `facts` the full ledger — no separate audit table. `forget_fact` core function + conversation tool (model supplies only `fact_id`; `db_path`/`user_id` session-bound in `handle_turn` — security boundary). System prompt lists facts with `[id]`; `persona.md` teaches the flow: numbered list on request, forget only on explicit ask, confirm + reversibility note, correction = forget + re-learn (no edit action).
   - ✅ (2026-07-23) Generic error message to the user on failure, centralized in the core (not per-channel): new `safe_handle_turn` in `core/conversation.py` wraps `handle_turn`, logs the full exception server-side (`logger.exception`) and returns the generic `model_error` message (now stripped of the `{error}` interpolation that leaked the raw exception). `main.py` and `discord_ch.py` both call `safe_handle_turn` instead of `handle_turn` directly — channels no longer duplicate error-handling logic (D5). Found and fixed along the way: `discord_ch.py` had **no** error handling at all around `handle_turn`, so a model failure crashed silently with zero reply to the Discord user — worse than the CLI leak the bullet was originally about. 151 tests passing (1 new for `safe_handle_turn`, plus the discord_ch wiring test).
   - ✅ (2026-07-30, validated on the real DB: reply saved at 02:14:18, distilled fact written at 02:14:20) **Background distillation** — implemented as designed below, with one deviation: launched with a plain non-daemon `threading.Thread` (`run_in_background` in `core/conversation.py`, catch-all `logger.exception` inside), NOT `asyncio.to_thread`. Reason: the split point lives in sync channel-agnostic core, and the CLI has no event loop at all — an asyncio launcher would force the whole chain async and drag asyncio into `main.py` for nothing (`to_thread` runs the work on an executor thread anyway). Non-daemon is Rumpel's explicit choice: the CLI waits for an in-flight pass instead of killing it on exit. Composes with the still-pending `asyncio.to_thread` around `on_message` (a worker thread can spawn a thread). Concurrent DB writes are safe because `_connect` opens a fresh connection per call (never shared across threads) plus WAL + `busy_timeout` from the bullet below. Tests: launcher (runs the work / logs exceptions) and, critically, a non-executing launcher proving the three state lines run in the *foreground* — the sync-runner test alone would still pass if they moved inside the task, which is the anti-stampede guarantee. Design as settled 2026-07-29:
     - **Split point:** the reply returns after the assistant turn is appended and both messages are saved. The DB write and the counter are sub-millisecond — backgrounding them buys no perceptible time and costs out-of-order writes (SQLite orders by completion, not by send) plus loss on crash. Only the distillation LLM call moves.
     - **The background task never touches `Session`.** `analyze_memory`/`apply_memory_changes` already don't; the only shared-state mutations are the three lines closing the trigger block. Those run in the foreground *before* launching: snapshot the pending slice (a copy), advance `last_analyzed_index`, reset `exchange_count`/`last_trigger_time`, then launch with the frozen copy.
     - **Resetting the counter in the foreground is what prevents a stampede.** If it were reset in the background, every turn arriving during the pass would still see the threshold met and launch its own distillation — overlapping LLM calls analyzing the same window, duplicate facts, wasted spend.
     - **Accepted cost:** the watermark advances before the pass is known to succeed, so a failed distillation loses that window permanently. The alternative (roll back on failure) reopens the race and was rejected; memory is best-effort and durable facts recur in conversation.
     - **`asyncio.create_task` over a sync function does not free the event loop** — the distillation is a blocking call, so it needs `asyncio.to_thread`.
     - ✅ (2026-07-30) **Anomaly notice dropped from the user-facing reply** (decided 2026-07-29, implemented 2026-07-30: `memory_anomaly_notice` deleted from both language blocks in `strings.py`, and `handle_turn`'s `if changes.rejected` branch removed entirely — a rejected pass carries empty lists, so the surviving `if not changes.is_empty` already skips the apply. 157 tests green). Distillation failures are plumbing the user cannot act on; surfacing them on Discord/WhatsApp reads as "this is broken" when the reply itself arrived fine, and makes Tabris sound like a system instead of an assistant (contradicts item 30c). `memory_anomaly_notice` is removed from `strings.py`; the `rejected` flag stays and drives the log line only. Same reasoning that dropped learning transparency: distillation reads only user turns, so the only party who can trigger the anomaly is the user, on their own memory. Operator-side visibility moves to item 38 (alerts).
     - **One catch-all around the background task** (`logger.exception`): a fire-and-forget task otherwise swallows its exception entirely.
     - ✅ (2026-07-30) **Duplicate facts fixed at the source, not swallowed by that catch-all.** Handled in `apply_memory_changes` (per-fact `try`/`except sqlite3.IntegrityError` + `logger.info` without the fact text, per 34c), NOT in `save_fact` — `INSERT OR IGNORE` there would have required deleting `test_duplicate_active_fact_raises` (item 28c's proof the dedupe index is live) and would have made `save_fact`'s returned id meaningless. The retire loop stays outside the `try` (only inserts can hit the index). The duplicate branch itself is unit-tested only: a real run cannot force the model to re-propose a known fact on demand. `save_fact` does a bare INSERT against the `idx_facts_active_content` UNIQUE index, so a re-proposed fact raises `IntegrityError` mid-loop in `apply_memory_changes` and every fact after it is dropped. Pre-existing and already visible today: the exception fires *after* the reply is computed and saved, so `safe_handle_turn` returns the generic error and the user loses a perfectly good reply.
   - ✅ (2026-07-30, e2e-tested) Exit flush skipped when nothing is unanalyzed: `main.py`'s exit branch distills only when `last_analyzed_index < len(conversation_history)`. Found while validating the background pass — Rumpel force-quit a CLI session that would not close, and the culprit was this foreground LLM call analyzing an empty window right after a background pass had just covered everything. Opening the CLI and typing `salir` immediately used to burn a model call too.
   - ✅ (2026-07-29, verified on the real DB after a long CLI session: `tabris.db` went from `delete` to `wal`, 72 messages persisted, 156 tests green) **SQLite concurrency — reprioritized here from item 38**: `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout` (`config.py`, `DB_BUSY_TIMEOUT_MS = 5000`) in `_connect`, adopted together. Item 38 filed these as "hundreds of concurrent users" work; backgrounding the distillation makes write-vs-write contention reachable with **one** user (background fact writes against the next turn's `save_message`), and by the bullet above a lost pass is permanent. `busy_timeout` is the essential half (turns a hard `database is locked` into a millisecond wait); WAL reduces how often that wait happens at all. Both live in `_connect` even though WAL persists on the file — splitting pragmas across `init_db`/`_connect` is exactly the item 28b trap. Test asserts the pragma values on a connection: a threaded contention test would be slow and flaky, so this is weaker than 28b's `IntegrityError` proof, accepted knowingly.
   - ✅ (2026-07-28, verified in code) Rebuild the system prompt per turn (not just once at session start): when `handle_turn` receives `persona`, it regenerates the whole system message — fresh facts + fresh `now` (via `build_system_prompt`'s default `datetime.now(utc)`) — and replaces `conversation_history[0]`. Both CLI and Discord pass `persona`, so the `## Current context` datetime refreshes every turn. Broader than the original bullet (rebuilds facts too, not just the datetime block).
34a. ⬜ Audio input (voice messages): transcribe incoming Discord voice messages to text via speech-to-text (Groq Whisper — cheap/fast), then feed the transcript into the normal text flow. Depends on item 34 (the messaging channel carries media; the CLI can't send audio). Read-only preprocessing step → no HITL confirmation.
34b. ⬜ Image input (vision): accept photos sent via Discord and route them to a vision-capable model (Gemini, natively multimodal) so Tabris can "see" and reason about the image. Depends on item 34; add a vision-capable model to the `tools`/multimodal role. Image *generation* is NOT in scope (backlog). Video "seeing" / visual analysis is NOT in scope (backlog — see round-scope note in §5).

34d. ⬜ Telegram as a second channel — a thin adapter (`python-telegram-bot`, polling; @BotFather token) reusing item 34's core untouched: same `handle_turn`, same `(channel, key)` identity, same link-code so a user maps Discord+Telegram to one profile, same hardening. Only new work: the adapter shell + wiring Telegram's voice/photo APIs into the shared media pipeline (34a/b). Low cost by design (D5); Rumpel wants both channels available. Mirrors Hermes's single-gateway/many-platforms model.
34c. ⬜ Data privacy minimums (code review 2026-07-02) — gate before onboarding beta-testers (§6): a retention policy (e.g. delete messages older than N months), a user-facing command to view/delete their own data (`/olvidame`), and confirm nothing ever logs raw message content (only metadata/errors). Not urgent solo; required before inviting anyone who isn't Rumpel.
   - ⬜ **Answer built by code, not by the model.** Today profile visibility depends on the model following a persona instruction — it silently omitted it until the wording was hardened (2026-08-11), and a fallback model may skip it again. Decide here between rendering the answer in the adapter (no generation) and a tool that returns the rendered block for the model to relay; the first removes the risk, the second keeps the conversational tone but still depends on the model calling it.
   - ⬜ **Free intent, not a literal command.** `/olvidame` assumes a magic word nobody knows to type — the same objection that killed keyword matching for `salir` (2026-07-30). Viewing is harmless and can run on intent alone; deleting is irreversible, so it takes intent plus an explicit confirmation before executing.
34e. ✅ Account linking via link-code — split out of item 34 on 2026-07-30 (design unchanged, see item 34's header; `user_channels` already supports it with zero migration). Today the CLI and Discord are two separate users with separate memories: Rumpel's CLI profile holds his real memory (7 facts, 116 messages, `America/Bogota`) while his Discord profile is near-empty and stuck on `UTC`, so Discord reports the wrong local time. Real work beyond the code: a new table for short-lived codes, a re-point (not insert) path for an existing `(channel, key)` row, tools for request/redeem mirroring `forget_fact`'s security boundary (model supplies only the code), and one genuine design decision — what happens to the throwaway profile auto-created on the new channel before linking (discard vs migrate its facts/messages). Rumpel's call 2026-07-30: build it properly rather than take the one-line SQL shortcut for his own account, but not now. Truly needed by 34d (Telegram), where a third channel makes the manual shortcut untenable.
   - **Progress (2026-07-30, TDD, all green — 165 tests):** persistence layer under way. `config.LINK_CODE_TTL_SECONDS` (300s); `link_codes` table (`code` UNIQUE, `user_id`, `expires_at`, `used`, `created_at`; auto-created via `CREATE TABLE IF NOT EXISTS`, no manual migration); `create_link_code(db_path, user_id)` — unique 8-char code via `secrets` from an unambiguous alphabet (no `0/O/1/I/L`), expiry set with SQLite's own clock; `redeem_link_code(db_path, code, channel, key)` returns the `user_id` or `None`, validating `used=0 AND expires_at > datetime('now')`, linking the new channel, then marking the code used. Fixed a latent `+-N seconds` datetime-modifier bug in `create_link_code` surfaced by the expired-code test.
   - **Decision (2026-07-30): Option A + no ghost; re-point dropped.** New channels defer user creation until a "¿nuevo o vincular?" fork, so no throwaway "ghost" user is auto-created. Combined with **wiping the DB before Alpha/Beta**, `redeem` never lands on a pre-existing `(channel, key)` row → the re-point/UPSERT path is dropped as YAGNI (plain INSERT). Production goal: one user record per person, more only by explicit user choice. No legacy-data migration needed (the wipe handles the current Discord ghost).
   - ✅ (2026-07-31) **One active code per user:** `create_link_code` expires the user's prior unused codes (`UPDATE ... SET expires_at = datetime('now') WHERE user_id=? AND used=0`) before inserting the new one, so no schema change and `redeem_link_code`'s existing expiry check does the enforcing. Both new tests validated by mutation. 167 tests passing.
   - **Wiring design agreed 2026-07-31 (no code yet).** ONE onboarding shared by every channel, not one per channel (D5): restructure it from blocking (an `input()` per question) to state-driven ("given where this person is, the next question is X") — the same extraction item 32 did for the conversation, and the piece that refactor left behind. The CLI calls it in its loop; Discord calls it once per incoming message. Pre-user state lives on `Session` (`user_id` nullable + onboarding step), because sessions are already keyed by `(channel, key)` — the only identity that exists before a user does — and already live in `core/`. Rejected: a parallel pending-dict per adapter (re-creates the duplication item 32 removed) and a DB table (persisting state that lasts minutes). First contact skips the yes/no round trip — greet + "paste your link code if you already use Tabris on another channel, otherwise we continue" — so the common case (new user) costs no extra turn. Recognizing a code is a pure function (fixed alphabet, length 8), no model call. An invalid or expired code is reported and retryable, never silently turned into a new account.
   - **Crash safety (analyzed 2026-07-31, no action needed).** Losing the session mid-onboarding leaves **zero residue**: nothing is written until the end, so the next message restarts the flow and the cost is re-asking name and city. Contrast with today's Discord path, which creates the user on the first message and leaves a permanent `en`/`UTC` profile if interrupted — Option A turns a permanent artifact into a repeated question. An unredeemed link code is unaffected: it lives in the DB with its own TTL, and requesting a new one invalidates it.
   - ✅ (2026-08-12) **A user is never created without the channel that reaches them:** `create_user_with_channel` runs both inserts on one connection under a single transaction, so a crash between them now leaves nothing instead of an orphan user row. The onboarding's confirm step is its only caller; `create_user` stays for the tests and the seeding script.
   - ✅ (2026-08-07) **`Session` carries pre-user state:** `user_id` nullable, `language` defaults to `"en"`, new `onboarding_step` holding the step's *name* (`None` = not onboarding). A name over an index so adding or reordering a question renumbers nothing. Field order unchanged, so existing positional calls keep working. 168 tests passing.
   - **Onboarding steps agreed 2026-08-07.** Order: detect language → confirm it → greet + "paste your link code, otherwise what is your name?" → city → clarify if ambiguous → **read back name/city/language and wait for a yes** → only then write to the DB. The language confirmation keeps its own turn deliberately: a short first message detects unreliably, getting it wrong asks every later question in the wrong language, and no path exists today to change language after onboarding. A "no" at the read-back restarts the flow from the name — no separate "which field is wrong" branch, which costs a path to maintain to save a turn few will use.
   - **Burst-typing hazard (found 2026-08-07).** In a messaging channel each incoming message advances one step, so someone answering across three quick messages has the later ones consumed as their name and city — a permanently wrong profile, and today nothing can correct it. Rejected: a debounce window in the adapter (timers only Discord needs, and it covers only bursts). Accepted instead, in layers: the read-back catches it before anything is written, and profile correction covers what slips through — including bad model extraction, which already happened in 33f. Outside onboarding a burst is only noise; nothing is persisted from it.
   - ✅ (2026-08-07) **Onboarding helpers moved to the core:** `detect_language`, `extract_name`, `extract_location`, `resolve_timezone`, `is_timezone_ambiguous` and `interpret_yes_no` left `main.py` for the new `core/onboarding.py`, with their tests. They were never CLI logic — they sat there because the CLI was once the only channel, and `core/` cannot import an adapter, which is half of why Discord creates people in `en`/`UTC`. Model mocks repointed from `main.providers` to `core.providers`. Also covered `detect_language`'s fallback on model error, which no test pinned.
   - ✅ (2026-08-07) **State-driven onboarding complete:** `advance_onboarding(session, user_input, db_path)` in `core/onboarding.py` consumes one message, moves `session.onboarding_step` and returns what to say — no printing, no input. Steps: first contact → `language` → `language_ask` → `link_or_name` (redeem or name) → `location` → `location_clarify` → `confirm` (read-back; yes creates the user and links the channel, no restarts from the name). Pending answers live on `Session` (`pending_name`/`pending_location`/`pending_city`/`pending_timezone`), so nothing reaches the DB before the read-back.
   - ✅ (2026-08-07) **A link code can no longer be read as a name:** `create_link_code` regenerates the rare all-letter draw so every code carries at least one digit, and `find_link_code(text)` (pure, next to the alphabet in `core/db.py`) returns the code found in the message or `None`. Costs 9.2% of the code space and removes the whole class of 8-letter names being redeemed as codes. Recognition needs no model call.
   - ✅ (2026-08-08) **A pasted code survives the sentence around it:** the first live Discord run had "Tengo este codigo XXX" taken as the person's name, because recognition required the code to be the entire message. `find_link_code` now scans the words and trims trailing punctuation. Same run showed the model inventing a code instead of calling the tool and defending it when challenged, so `persona.md` now forbids showing any code that did not come back from the tool in that same turn.
   - ✅ (2026-08-07) **Session carries its own identity:** `channel`/`key` moved onto `Session` (already passed to `get_or_create_session`, previously discarded), so the shared onboarding takes one extra argument instead of three.
   - ✅ (2026-08-07) **CLI uses the shared onboarding; `onboard_user` and `resolve_language` retired** with their tests. `chat()` seeds the system prompt only after the loop leaves onboarding, since no user exists before that.
   - ✅ (2026-08-07) **Onboarding strings de-CLI'd:** dropped the `(si/no)`/`(es/en)` hints — free-form answers have been understood since 33d, so offering two options misrepresents what is accepted — and the trailing colons/spaces that only made sense as an `input()` cursor prompt. New key `ask_name_or_code` (es/en) carries the first-contact greeting and the code-or-name fork; it deliberately has no `{agent}:` prefix because it is sent joined to `language_confirmed`.
   - ✅ (2026-08-11) **Profile visibility:** the linked channels join name and city in the per-turn prompt, by channel name only. `get_user_channels` selects the channel column alone, so the key never leaves the query and no call site can leak it. The profile moved under its own `## Profile` heading so `persona.md` names the section instead of enumerating its fields — a field added later touches one file, not two. Only `handle_turn` passes it: the prompts the two adapters build are overwritten before any model reads them. Language stays out; the user already sees it in every reply.
   - ✅ (2026-08-11) **Two model-side fixes, both found live and neither visible to a test.** The model silently skipped the profile — "what you remember about them" matches the facts heading almost word for word, and the brevity rules outweighed a subordinate clause — until the instruction became "recite the section in full". Then the list carried two competing numbers, position and id, which read as noise today only because nothing has been retired yet; they diverge on the first forget. The id is now the only number, written with a dash rather than markdown list syntax so a renderer cannot renumber it.
   - ✅ (2026-08-11) **`get_facts` breaks `created_at` ties by id.** Facts saved in one distillation pass share a second, and SQLite's sorter is unstable, so a real profile came back shuffled. Reproduced by a 12-row test before the fix — the tie alone was enough to destabilise it.
   - ✅ (2026-08-12) **Profile correction:** `update_profile` tool fixes name, city and language after onboarding, mirroring `forget_fact`'s boundary — the session binds the user, the model sends only the values. Two rejections happen in code before anything is written: a city whose timezone is ambiguous (the model is told to ask for the country) and a language outside `MESSAGES` (which would break every later `msg()` lookup for that user). `persona.md` requires proposing the exact change and waiting for approval, so a city mentioned in passing cannot rewrite a profile. `update_user_profile` in `core/db.py` writes only the fields given and replaces the unused `update_user_language`; `session.language` is now refreshed from the stored row each turn, leaving one writer for a value that lives in two places.
   - ✅ (2026-08-07) **Requesting a code from the chat:** `REQUEST_LINK_CODE_TOOL` + `_run_request_link_code` in `core/conversation.py`, mirroring `forget_fact` — the model supplies no arguments at all and the session binds `user_id`. `persona.md` says when to offer it and to warn that the code is single-use and short-lived. With this the whole link flow runs over two CLI profiles, no Discord needed.
   - ✅ (2026-08-07) **Discord uses the shared onboarding:** `handle_message` no longer auto-creates a profile from the Discord display name in `en`/`UTC` — an unknown `(discord, key)` runs `advance_onboarding` until it has a user, exactly like the CLI. The `name` parameter is gone: the name is asked, not guessed.
   - ✅ (2026-08-12) **Redundant prompt construction removed from the adapters.** Both built a system prompt that `handle_turn` overwrote on the first turn, so its content never reached a model. They now seed the history with past messages only, and `handle_turn` bumps `last_analyzed_index` when it inserts the system message — the shift is corrected where it is caused, so a new channel cannot inherit the off-by-one.
   - ✅ (2026-08-12) **Profile correction confirmed live:** the stored profile moved to a new city and timezone from a chat request alone.

34f. ✅ **Correcting a fact no longer loses it** (found in the first live Discord session, 2026-08-08). The user asked to reword a fact; Tabris retired the old one and said the new wording was "registrado" — but the model can only forget, and distillation reads `user` turns only, so an assistant-authored correction is invisible to it. The fact was simply lost. `REMEMBER_FACT_TOOL` + `_run_remember_fact` mirror `forget_fact` (session binds `user_id`, the model supplies only the sentence) and tolerate a duplicate instead of failing the turn. `persona.md`: propose the wording → wait for approval → forget, then remember; and never claim something is saved unless a tool confirmed it. Deliberate trade-off: the model can now write memory, contained exactly like forgetting — only on an explicit request, and always reversible.

34g. ✅ **A reply too long for Discord is silently lost** (found live 2026-08-11, fixed 2026-08-12). Discord rejects any message over 2000 characters; the adapter sent without splitting, and the reply was already saved, so the user saw silence while the model's history kept an answer they never read. Three parts, all done: `split_message` in `core/text.py` cuts at a line break, then a space, then hard, with the channel's limit passed in (`config.DISCORD_MESSAGE_LIMIT`); `send_reply` stops at the first failed piece, warns the user through `msg("send_failed")` and reports whether it delivered; `undo_last_turn` in `core/conversation.py` retires the turn from the database (`deactivate_message` + `get_messages` now filtering `is_active=1`) and from the session history, using the ids `handle_turn` records on `Session.last_turn_message_ids`. `safe_handle_turn` clears those ids on entry so a rejected message can never undo an older delivered turn. Confirmed live: a 2093-character reply arrived split.

35. ⬜ CLI UX (F7 remainder): handle `Ctrl+C` (KeyboardInterrupt) so memory still saves on exit; enable streaming responses for perceived speed. Belongs with the channel-adapter work in item 32.

35a. ✅ **Response-quality pass** (external analysis 2026-07-21, all claims verified vs real code + web). Root cause of the flip-flopping answers: Gemini's free daily quota gets exhausted by the several-model-calls-per-turn load, then `general` falls back to the weaker Groq llama-3.3-70b. Reality check from Rumpel's real AI Studio account (2026-07-21): the high-end Flash models (2.5 / 3 / 3.5 Flash) are all capped at **20 RPD** on his free tier — the web's "~1,500 RPD" figure does NOT apply here; only `gemini-3.1-flash-lite` gives **500 RPD** (15 RPM, 250K TPM). Fixes, by ROI:
   1. ✅ (2026-07-21) Stop burning Gemini on non-user-facing calls: memory distillation used the `general` role (→ Gemini). Gave it a **dedicated `memory` role** — decoupled from `general` so future chat-model swaps don't silently change how memory is built. Decision (Rumpel): do NOT downgrade the model — memory quality matters, and once distillation is automatic (Hermes-style, no HITL gate) the model is the only safeguard against garbage facts. Primary = **DeepSeek** (`deepseek-chat`: strong at structured extraction, doesn't touch Gemini's free quota, cents/mo) → `gemini-3.1-flash-lite` → ollama. Spaced out: `MEMORY_TRIGGER_EXCHANGES` 5 → 15, `MEMORY_TRIGGER_SECONDS` 300 → 1200 (fewer, larger passes = better distillation). `should_trigger_memory` tests rewritten to derive from config (no more hardcoded thresholds).
   2. ✅ (2026-07-21) [the real fix — prompt, not model] `persona.md` grounding: added two bullets — when `web_search` ran, ground the answer in those results (they outrank training knowledge and earlier turns; don't blend fresh with stale); on contradiction with an earlier turn, the newer result wins and is corrected briefly/explicitly instead of silently flip-flopping. Fixes the 3-different-dates symptom. Current-date injection was ALREADY done (item 33e + per-turn refresh) — only the grounding wording was new. No unit test (system-prompt wording); verify with a real run.
   3. ✅ (2026-07-21) Moved `general`'s primary from `gemini-2.5-flash` to **`gemini-3.1-flash-lite`** (500 RPD, 25× the 20-RPD cap that was the actual bottleneck). Verified with a live run: quality up, 9/500 RPD used. NOTE: the note originally said `gemini-3-flash` @ ~1,500 RPD — wrong for this account (also 20 RPD); the AI Studio table settled it.
   4. ✅ (2026-07-21) Reordered `general` fallback: `gemini-3.1-flash-lite` → **deepseek** (`deepseek-chat`) → groq llama-3.3-70b → ollama. DeepSeek inserted ahead of Groq (better quality in the role that matters most, cents/mo). Kept llama-3.3 as a deeper safety net (only hit if both Gemini and DeepSeek fail) rather than dropping it. Skip Kimi for `general` (~15× DeepSeek for no noticeable gain in Spanish chat).

35b. ✅ **Grounding pass** (from the first live Discord session, 2026-08-08, where Tabris gave three different exchange rates for the same day and claimed to have consulted sources).
   1. ✅ **Temperature per role** in `AGENT_ROLES` (`router` 0.0, `memory` 0.0, `code` 0.2, `general` 0.7), passed through `providers.chat` → `_call_provider`; a role without one keeps the provider default (the key is omitted, never sent as null). Biggest win is `router`: every onboarding helper runs on it, and creativity there is what wrote a model's reasoning into a user's city in 33f. Explicitly NOT a fix for invented data — temperature moves sampling randomness, not truthfulness.
   2. ✅ **Tool use is visible:** `run_with_tools` logs which tools ran per round. Tool messages are ephemeral by design, so until now nothing recorded whether a search happened — an answer could not be told apart from a fabrication after the fact. Feeds the operator alerts already planned in item 38.
   3. ✅ **`persona.md` grounding rules:** never state a figure that changes over time unless it came from a search in the same turn; never claim to have consulted sources when no tool ran; on pushback, search instead of guessing again. Same lever that was added for invented link codes — text, not a lock.
   - ⬜ **Rejected for now:** forcing a search via `tool_choice`. Forcing the right tool requires knowing beforehand that the question needs it, which costs an intent call on every turn for a case that appears occasionally. Revisit if the persona rules prove insufficient.

### Phase 4 — Deploy (always-on)
36. ⬜ Choose host: compare Oracle Always Free vs Hetzner (~$4.5/mo) vs Fly.io free allowance.
37. ⬜ Deploy as a systemd service or Docker container; secrets via environment variables. File permissions are OS-level, not git-tracked — `.env`, the SQLite DB, and `tabris_client_id`-equivalent files get created fresh on the VPS and must be locked down there explicitly, not assumed from local dev: `chmod 600` on all of them as part of the deploy step (code review 2026-07-02, §2.4). Additional VPS hardening from the same review: dedicated system user with no sudo, encrypted disk if the provider offers it, backups of the `.db` also kept at 600. **Permissions are not a one-time task — any copy destroys them** (the new file is created with the system default, not the source's mode). Observed 2026-07-30: `tabris.db` had drifted to 644 and `tabris_client_id` to 664 while `.env`, never copied, kept its 600 — the manual dev-machine↔the server DB sync is what resets them. The `chmod` therefore belongs inside the sync/backup/deploy *procedures*, not in a checklist item marked done once.
38. ⬜ Basic ops: restart-on-failure, weekly SQLite backup. **The backup must use SQLite's own backup command (`.backup` / `VACUUM INTO`), NOT `cp`** — WAL (adopted in item 34) keeps recent writes in a `-wal` sidecar, so copying `tabris.db` alone can capture a file missing the newest facts/messages or caught mid-transaction. The failure is silent: cron reports success and the file looks right until the day it is restored. Scenarios folded in from the code review 2026-06-24:
   - **Operator alerts (Rumpel's ask, 2026-07-29).** With the anomaly notice removed from user replies (item 34), nothing surfaces off-server. Every sensitive path already calls `logger.warning`/`logger.exception`, so this is a logging *handler* added at startup — not new code in `core/`, and no call site changes. Destination: a private Discord channel/DM (Tabris is already connected there; no new infra). **Aggregate, don't emit per event** — "3 anomalies in the last hour" vs "1" is the only distinction that matters ("sporadic = informative, constant = investigate"), and per-event alerts flood the channel and hit Discord's rate limit exactly when something is looping. **No raw message content in an alert**, not even to a private channel (item 34c): user id, counts, timestamps only. Lands here rather than in item 34 because while Tabris runs on Rumpel's PC the log is already on screen — the need is born with always-on. Admin panel deferred to the backlog; it needs events *stored* (a small `events` table) rather than logged, since logs rotate and are lost on redeploy.
   - **Provider retry multiplication (found 2026-07-30; Rumpel's call: leave as is for now).** The `openai` client defaults to `max_retries=2`, so every provider is tried 3× before the chain moves on — `PROVIDER_TIMEOUT = 15` is really up to 45s per provider, and it retries quota/429 errors too, waiting ~30s to be told "no" again. This is what made the pre-fix exit flush hang long enough to force-quit. Harmless while the first provider in the chain answers, which is the normal case. Fix when it bites: `PROVIDER_MAX_RETRIES` in `config.py` passed to `_get_client`; 0 is the right value, since the fallback chain (D2) already *is* the retry mechanism — insisting 3× on a dead provider never helps.
   - **Narrow `except Exception`.** The broad catches in the main loop, `providers.chat` and `update_memory` hide bugs (a `KeyError` in our code looks identical to a network timeout). Log the type/traceback and, where possible, catch provider-specific errors (`openai`/`httpx`). The main loop may stay tolerant, but it must log what it swallowed.
   Additional scenarios from the code review 2026-07-02 (relevant once there are hundreds of concurrent users, not before):
   - **Indexes.** (WAL + `busy_timeout` moved up to item 34 on 2026-07-29 — background distillation makes contention reachable with one user.) Missing indexes `messages(user_id, id)` and `facts(user_id) WHERE is_active=1` — today `get_messages`/`get_facts` full-scan on every session load; invisible with one user, real cost at scale. Also decide whether `messages.is_active` (unused in any query today) becomes real soft-delete history or gets dropped.
   - **Structured logging without PII.** Never log raw message content (only metadata/errors) — content is personal data. Configure spend/quota alerts in each provider console (Groq, Gemini, DeepSeek, OpenRouter) — that's provider-side config, not code.
   - **Async I/O at real scale.** Sync `OpenAI` client + polling loop serialize all users behind each other's LLM latency (2-10s). At hundreds of concurrent users: `AsyncOpenAI` + a webhook (FastAPI) instead of polling. Not worth it at beta-tester scale — only revisit if usage actually gets there. Postgres migration follows the same rule: only when a second process needs to write (e.g. multiple FastAPI workers) — `core/db.py`'s pure functions keep that migration cheap whenever it's actually needed.
38a. ⬜ Minecraft server control (pre-freeze server action — the OpenClaw-style "execute tasks" capability from Rumpel's core vision). Function-calling tool `minecraft_server(action, name)` that runs the start/stop script on the server, dispatched in `_execute_tool_call` like `web_search`/`web_fetch`. No permission system — testers already have server access. HITL confirmation before a stop (kicks connected players) is cheap insurance, optional. Depends on item 34 (Discord) + Tabris running on the server (36-37).
> Exit criterion: Rumpel talks to Tabris from his phone with his PC off.

### Phase 5 — Liquidador de renta (first pipeline product)
39. ⬜ Employment contract liquidator (Colombia): validate logic with Excel prototype first (willingness-to-pay before any code); then CLI + SQLite; then minimal web UI (FastAPI + React). Becomes Tabris's first external tool once the Phase 3 tool layer is in place.

### Phase 6 — Portfolio (starts after first product ships)
40. ⬜ Write a serious `README.md` for Tabris: what/why, architecture diagram, decisions (link this plan), setup guide ("clone → .env → run"), screenshots/GIF of the Discord bot. Also make `start_tabris.sh` portable (code review 2026-06-24): it hardcodes `~/Projects/tabris` and `cd ~/Projects/tabris` (breaks "clone → run" for any other path/user) and runs `sudo systemctl start ollama` (not portable — cloud/VPS without systemd, may prompt for a password). Fix: derive the dir from the script itself (`SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`); drop the sudo/ollama line and document the Ollama-as-fallback requirement in the README instead. Code-quality nits folded in from the code review 2026-07-02 (small, pre-publish polish, bundle in the same pass):
   - Split `requirements.txt` into runtime (`openai`, `ollama`, `python-dotenv`, `pydantic`, ...) and `requirements-dev.txt` (`-r requirements.txt` + `pytest`); add `pip-audit` as a periodic habit for dependency CVEs.
   - Add `.pytest_cache/` to `.gitignore`; always run pytest from the project root.
   - `.env.example`: stray `)` in a comment, missing trailing newline.
   - `core/memory_manager.py`: list-comprehension closing `]` misaligned (valid but confusing); `"HAS_CHANGES: yes" not in raw_response` string match is fragile against model formatting variance (`HAS_CHANGES:yes`, casing) — normalize before comparing.
   - `main.py`: `from datetime import datetime as _datetime` is imported inside a function — move to the top-level imports.
41. ⬜ Security pass: confirm no secrets in git history (if any were ever committed, rotate keys).
   - **Checked 2026-08-11 — no secrets, but personal data is in the history.** `.env` and the client-id file were never tracked, so no key was ever exposed. Two early commits did add `memory.md` and `tabris.db`, and both carry the maintainer's own profile; neither is tracked today, but removing a file does not remove it from history. Purging them means rewriting history, which changes every commit hash — so it belongs before item 42, not after.
42. ⬜ Make repo public **only after passing the Publishable Checklist (§7)**.
43. ⬜ First LinkedIn/blog post: "Building my own JARVIS as a career-change project" — the "document everything" rule becomes content. Target: 1 post per completed phase.
44. ⬜ GitHub profile README + pin Tabris.

### Phase 7 — Integrations, scheduling & multi-agent (candidate, post-freeze / resume point)
45. ⬜ Task scheduler: APScheduler (or similar) so Tabris can fire reminders and timed actions from a persistent server.
46. ⬜ Google Workspace integration: Calendar, Gmail, Drive — via OAuth + function calling.
47. ⬜ Notion integration: read/write pages and databases via Notion API + function calling.
48. ⬜ PM / Dev / Tutor role structure on top of the role→provider map. Multi-agent orchestration — the biggest architectural jump, deferred from the Phase 3 tool layer (not part of the daily-assistant MVP).
49. ⬜ Specialized agents by strength (research/deep-search, documents, images, image generation) as budget allows. Includes video "seeing" / visual analysis. Deferred from the Phase 3 tool layer.
50. ⬜ Multi-provider parallel search aggregation (deferred from Phase 3 item 33b/33c, 2026-07-14). Query 2+ search providers concurrently for the same request and merge/dedupe normalized results, instead of the sequential fallback (one provider at a time, switches only on failure/quota). Value beyond speed: different engines' indexes/rankings surface different pages for the same query, reducing single-source bias — complements the multi-query refinement the model already does within `run_with_tools`. Cost: ~2-3x latency/spend per search + a merge/dedupe step. Revisit only if single-provider search quality proves insufficient in real beta-tester use.
51. ⬜ Add Brave as a second search provider — sequential fallback after Tavily (`_search_brave`, same `{title, url, content}` shape, no rework). Leaning choice as of 2026-07-20. Effectively free at Tabris's volume (Brave enters only as backup); requires registering a payment method.

    Search-provider options (researched 2026-07-20, 2026 agent-search benchmarks):

    | Provider | Strength | Cost / free tier | Fit for Tabris |
    |---|---|---|---|
    | **Tavily** *(current primary)* | Built for LLMs, returns extracted content; "cleanest default" | 1,000 credits/mo free | ✅ In use |
    | **Brave** *(leaning 2nd)* | Own independent index; #1 in 2026 benchmarks (~14.89), fastest (~669ms) | Pay-as-you-go $5/1k; 2,000 queries/mo free + $5 renewing credit | Same adapter, no rework |
    | **Exa** | Semantic / find-similar (different retrieval) | Free tier | Weak fit (semantic, not current-events); different response shape |
    | **Serper** | Google SERP quality, cheap | Free credits | Google index again (no diversity) |
    | **SearXNG** | Self-hosted metasearch, no key | Free (self-host on the server) | Free backup better than DDG; more setup |
    | **DuckDuckGo** *(current backup)* | No key, free | Free | ✅ In use; lower quality/flaky |

    Brave billing: pay-as-you-go (metered, not a flat subscription) — billed only on overage beyond the free allowance at $5/1k.

---

## 6. Project Pipeline — Prioritized Backlog

Scoring 1–5 (higher = better) on: **V**iability (can Rumpel build it soon), **M**onetization
potential, **B**udget fit (cost to build/run), **C**omplexity (5 = simplest). Nothing is deleted.

| # | Project | V | M | B | C | Total | Role in the plan |
|---|---|---|---|---|---|---|---|
| 1 | Employment contract liquidator (Colombia) | 4 | 4 | 5 | 4 | 17 | **Active #1 / flagship.** Local niche, real demand (employees & small employers), little quality competition, shows domain expertise — strongest portfolio piece and best SaaS bet. |
| 2 | Habit & Task Tracker | 5 | 2 | 5 | 5 | 17 | Backlog — learning vehicle: CRUD, SQLite, API. Can become Tabris's first tool once the Phase 3 tool layer is in place. Weak as standalone product (saturated market). |
| 3 | Income tax calculator (Colombia) | 4 | 4 | 5 | 3 | 16 | Backlog — natural sibling of #2 (shared domain & audience). Strong candidate to bundle with #2 into one "Colombian payroll/tax tools" product. Seasonal demand spike (tax season). |
| 4 | Expense & budget tracker | 4 | 2 | 5 | 4 | 15 | Backlog — good second data source for Tabris-as-assistant; weak standalone monetization. |
| 5 | Account reconciliation tool | 3 | 4 | 4 | 2 | 13 | Backlog — monetizable (freelance accountants/SMBs) but needs domain depth and real user input. Revisit after #2 ships and brings contact with that audience. |
| 6 | Reading app | 3 | 2 | 4 | 3 | 12 | Backlog — personal value, crowded market. |
| 7 | Streaming platform | 1 | 2 | 1 | 1 | 5 | On hold (as already agreed) — infrastructure cost and complexity are incompatible with current constraints. |
| 8 | Documentation generator (video→manual) | 2 | ? | 4 | 2 | — | Backlog / UNVALIDATED. Crowded market (Scribe, Tango, Guidde, Docsie). Validate willingness-to-pay with the people who requested it BEFORE any build. Outside the financial-domain edge. |

**Sequence:**
- Tabris: finish Phases 3–4 this round (personal-assistant MVP), then FREEZE. Definition of done
  (functional for daily use): persistent memory + internet (`web_search`/`web_fetch`) + Discord +
  audio input + image input + always-on deploy. Everything beyond = backlog.
- **At the freeze:** beta-testers are onboarded (the multi-user foundation already exists from item
  30, so this costs no rework). The freeze is not "Tabris switched off" — it is feature-frozen for
  development while running in **daily production use** by Rumpel + beta-testers, gathering feedback.
- **During the freeze → Phase 5: Liquidador de renta** as flagship wedge (built mainly with
  Claude/Gemini, with Tabris dogfooded alongside). Start with an Excel prototype (validates logic +
  willingness to pay before any code). Feedback collected on Tabris during this period is reviewed
  and its valuable parts implemented when Tabris is picked back up (next round).
- Then → Phase 6: Portfolio — publish and document with a shipped product to show.
- Tax season makes the liquidador time-sensitive: prioritize accordingly.

---

## 7. Publishable Checklist (gate for making anything public)

A repo/demo goes public only when ALL are true:
- [ ] Works end-to-end for its core use case (no "coming soon" in the main flow)
- [ ] `README.md` complete: what, why, architecture, setup, usage, screenshots
- [ ] No secrets in code **or git history**; `.env.example` provided
- [ ] Tests exist and pass (`python -m unittest` clean)
- [ ] Code in English, reasonably clean (a beginner-honest standard, not perfection)
- [ ] Public functions carry type hints + short docstrings (e.g. `def save_fact(db_path: str, user_id: int, content: str) -> int:`), enough to run `mypy` — beginner-honest, not exhaustive (code review 2026-06-24)
- [ ] If it has a UI/bot: a reviewer can try it in < 2 minutes (demo, GIF, or test bot)

---

## 8. Working Agreements

Binding collaboration and code agreements live in two agent-agnostic files at the repo root:
- **`AGENTS.md`** — collaboration style + dev commands (one step at a time, explain before coding, propose-don't-apply, language convention, test/venv commands).
- **`CONTRIBUTING.md`** — code standards + architecture patterns (TDD, end-to-end at every step, vibe-coding boundary, HITL for destructive actions, code conventions, provider/channel/DB patterns).

Project-level drivers stay here as source of truth: budget constraint (§2); shipping-over-learning priority (§1); replicability / "document everything" (§6, D9).

---

## 9. Known Risks

| Risk | Mitigation |
|---|---|
| DeepSeek outages (~97% uptime) | Provider fallback (D2) is mandatory in `core/providers.py` |
| API price changes | Role→provider map makes switching a one-line change; re-check prices quarterly |
| Scope creep (7 projects, multi-agent dreams) | §6 sequence + "do not build before the second user exists" rule (M2) |
| Leaked secrets | `.env` pattern + history check before going public + key rotation if in doubt. (Verified 2026-06-24: `.env` never in git history — clean.) |
| Prompt injection in memory distillation | Raw conversation text is embedded in the distillation prompt; a user could type `HAS_NEW_FACTS: yes` / `FACTS:` lines to spoof the parser format. The human `si/no` gate was removed by auto-apply (2026-07-23) → this risk is now **live**; mitigation is the item-34 delimiting bullet (fence user turns in the 4 LLM-facing prompts), now higher priority. (Code review 2026-06-24.) |
| Burnout / runway pressure | Portfolio milestones every phase = visible progress even if revenue lags |
