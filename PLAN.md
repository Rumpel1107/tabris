# Tabris — Master Plan

> **Purpose of this document:** single source of truth for the Tabris project.
> Any agent (or human) picking up this project should read this file first.
> Conversations with the user happen in **Spanish**; all code, commits and docs are in **English**.
> Working agreement: **one step at a time, wait for user confirmation, explain every command/concept.**

Last updated: 2026-07-16

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
| D4 | **Telegram bot as first interface** | Free, unlimited, bot created in minutes via @BotFather, no business verification, works via polling (no public webhook/domain needed). WhatsApp is deferred: requires Meta Business verification, dedicated number, and bills business-initiated template messages from the first send — revisit when there are real Colombian users (WhatsApp is the natural channel there). |
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
a backup or is transactional; human-in-the-loop confirmation stays for profile-level changes.

**Fact lifecycle rule:** facts are append-only — never edited in place, never hard-deleted.
A fact that becomes false or obsolete is *retired* via soft-delete (`is_active=0`), preserving
history. A change of information = retire the stale fact + insert the corrected one (never an
in-place `UPDATE` of `content`). Only `is_active=1` facts feed the system prompt. Obsolescence is
detected during distillation (the LLM receives known facts *with their `id`* and returns two sets:
new facts to add + `id`s to retire, with reason); additions and retirements are confirmed together
by the user before any write.

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
> (`web_search`/`web_fetch`) + Telegram + audio input + image input + always-on deploy.

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

### Phase 3 — Memory v1 + Internet + Telegram
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
33. ⬜ **Internet access via tool use** (first tool of the tool-use layer). Build order — one new concept per step:
    - **33a. ✅ (2026-07-10)** Function-calling loop: `providers.chat()` accepts `tools`; `core/search.py` (`web_search` via `ddgs`); `run_with_tools()` loop in `core/conversation.py`, wired into `handle_turn`. Verified with real runs (needed a `persona.md` tool-awareness fix for reliable use). DDG result-quality gap deferred to 33b/33c.
    - **33b. ✅ (2026-07-16)** Generalized behind `core/search.py` + `SEARCH_PROVIDERS` config list + fallback chain + result normalization (D10). `web_fetch` added, wired as a tool, and mentioned in `persona.md`. YouTube-transcript tool deferred (not built). Verified with real runs.
    - **33c.** Register Tavily/Brave keys; DuckDuckGo stays as the last-resort backup.
    - Search is read-only → **no HITL confirmation** (unlike file writes). File/tracker CRUD tools (the original, broader item-33 scope) are deferred to Phase 7 (items 48/49).
33d. ✅ (2026-07-16, validated with a real run) Onboarding friendliness. New `interpret_yes_no` (router LLM) infers affirmation instead of exact string match; `resolve_language` now injects `interpret_fn`/`detect_fn` and stays pure (fallback reuses `detect_language` on free text). Onboarding reordered in `chat()`: greet → detect+confirm language → ask name in that language → echo `onboarding_done`; language-detection block removed from the loop; first message only triggers onboarding (not answered). Real run confirmed a natural affirmative ("Esta perfecto, gracias.") resolves to `es`.
33e. ⬜ Timezone + real-time grounding gaps (found 2026-07-16, real run, after wiring `web_fetch` + user name into the system prompt). Two issues seen in the same session: (1) `build_system_prompt`'s `## Current context` block always uses server-local time (`datetime.now()`, server runs UTC) — there is no timezone handling anywhere in the code, so the model tries to mentally offset to the user's real timezone and gives inconsistent, self-contradicting dates across turns, even after "user is in Bogota" was saved as a fact. (2) For time-sensitive queries the model may fabricate instead of calling `web_search`. Update 2026-07-16 (33d validation run): grounding actually behaved — a "TRM de hoy" query triggered a real `web_search`, no fabrication — so #2 is lower priority than #1. #1 reproduced cleanly: first date/time answer returned server UTC (22:12) as if it were the user's local time, no timezone qualification; only corrected to Bogotá (17:12) when explicitly asked, and via a web search for the offset. Needs design before fixing: where timezone lives (new per-user fact vs a `users` column) and how/where `now` gets converted before formatting. Note: per-turn refresh of the `now` block is already scoped under item 34 (§ line ~226) — coordinate. Optionally stronger `persona.md` language for #2.
34. ⬜ Telegram bot via @BotFather + `python-telegram-bot` (polling mode — no webhook needed). Telegram's `user_id` is the channel key (free, stable) — register it in `user_channels` exactly like the CLI key. **Account linking (same human, multiple channels → one profile/context):** via a short-lived **link-code**, never by name. Flow: on an already-registered channel the user requests a code; entering it on the new channel inserts a `user_channels` row pointing the new `(channel, key)` to the existing `user_id`. The `user_channels` schema (item 30) already supports this with zero migration — multiple rows per `user_id`. Name-based linking is explicitly rejected (impersonation risk). Additional scope from code review 2026-07-02 (Telegram removes the CLI's `input()` confirmation, so these land here):
   - Message length cap (~4000 chars) + basic per-user rate limit (in-memory counter is enough at this scale).
   - Delimit user input in the 4 LLM-facing prompts (`route_message`, `detect_language`, `extract_name`, memory analysis) — e.g. wrap in `<user_message>...</user_message>` and instruct the model to treat it as data only. Mitigates prompt injection now that a malicious message could reach real other users.
   - Redesign memory HITL for Telegram: no more blocking `input()` — use inline buttons for confirm/reject, or auto-apply with an audit log + a command to review/delete facts.
   - Generic error message to the user on failure; full exception detail goes to the log only (not stdout/chat) — today `model_error` echoes the raw exception, which is fine in a personal CLI but leaks internals to strangers on Telegram.
   - Fire `update_memory`'s distillation as a background task (`asyncio.create_task`) instead of blocking the reply — natural once the bot is async.
   - Rebuild the system prompt's `## Current context` datetime block per turn (not just once at session start) — cheap, and sessions on Telegram live much longer than a CLI run.
34a. ⬜ Audio input (voice messages): transcribe incoming Telegram voice notes to text via speech-to-text (Groq Whisper — cheap/fast), then feed the transcript into the normal text flow. Depends on item 34 (Telegram is the media channel; the CLI can't send audio). Read-only preprocessing step → no HITL confirmation.
34b. ⬜ Image input (vision): accept photos sent via Telegram and route them to a vision-capable model (Gemini, natively multimodal) so Tabris can "see" and reason about the image. Depends on item 34; add a vision-capable model to the `tools`/multimodal role. Image *generation* is NOT in scope (backlog). Video "seeing" / visual analysis is NOT in scope (backlog — see round-scope note in §5).
34c. ⬜ Data privacy minimums (code review 2026-07-02) — gate before onboarding beta-testers (§6): a retention policy (e.g. delete messages older than N months), a user-facing command to view/delete their own data (`/olvidame`), and confirm nothing ever logs raw message content (only metadata/errors). Not urgent solo; required before inviting anyone who isn't Rumpel.
35. ⬜ CLI UX (F7 remainder): handle `Ctrl+C` (KeyboardInterrupt) so memory still saves on exit; enable streaming responses for perceived speed. Belongs with the channel-adapter work in item 32.

### Phase 4 — Deploy (always-on)
36. ⬜ Choose host: compare Oracle Always Free vs Hetzner (~$4.5/mo) vs Fly.io free allowance.
37. ⬜ Deploy as a systemd service or Docker container; secrets via environment variables. File permissions are OS-level, not git-tracked — `.env`, the SQLite DB, and `tabris_client_id`-equivalent files get created fresh on the VPS and must be locked down there explicitly, not assumed from local dev: `chmod 600` on all of them as part of the deploy step (code review 2026-07-02, §2.4). Additional VPS hardening from the same review: dedicated system user with no sudo, encrypted disk if the provider offers it, backups of the `.db` also kept at 600.
38. ⬜ Basic ops: restart-on-failure, weekly SQLite backup (cron + copy). Scenarios folded in from the code review 2026-06-24:
   - **Narrow `except Exception`.** The broad catches in the main loop, `providers.chat` and `update_memory` hide bugs (a `KeyError` in our code looks identical to a network timeout). Log the type/traceback and, where possible, catch provider-specific errors (`openai`/`httpx`). The main loop may stay tolerant, but it must log what it swallowed.
   Additional scenarios from the code review 2026-07-02 (relevant once there are hundreds of concurrent users, not before):
   - **SQLite concurrency + indexes.** `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` in `_connect` (reads no longer block writes). Missing indexes `messages(user_id, id)` and `facts(user_id) WHERE is_active=1` — today `get_messages`/`get_facts` full-scan on every session load; invisible with one user, real cost at scale. Also decide whether `messages.is_active` (unused in any query today) becomes real soft-delete history or gets dropped.
   - **Structured logging without PII.** Never log raw message content (only metadata/errors) — content is personal data. Configure spend/quota alerts in each provider console (Groq, Gemini, DeepSeek, OpenRouter) — that's provider-side config, not code.
   - **Async I/O at real scale.** Sync `OpenAI` client + polling loop serialize all users behind each other's LLM latency (2-10s). At hundreds of concurrent users: `AsyncOpenAI` + a webhook (FastAPI) instead of polling. Not worth it at beta-tester scale — only revisit if usage actually gets there. Postgres migration follows the same rule: only when a second process needs to write (e.g. multiple FastAPI workers) — `core/db.py`'s pure functions keep that migration cheap whenever it's actually needed.
> Exit criterion: Rumpel talks to Tabris from his phone with his PC off.

### Phase 5 — Liquidador de renta (first pipeline product)
39. ⬜ Employment contract liquidator (Colombia): validate logic with Excel prototype first (willingness-to-pay before any code); then CLI + SQLite; then minimal web UI (FastAPI + React). Becomes Tabris's first external tool once the Phase 3 tool layer is in place.

### Phase 6 — Portfolio (starts after first product ships)
40. ⬜ Write a serious `README.md` for Tabris: what/why, architecture diagram, decisions (link this plan), setup guide ("clone → .env → run"), screenshots/GIF of the Telegram bot. Also make `start_tabris.sh` portable (code review 2026-06-24): it hardcodes `~/Projects/tabris` and `cd ~/Projects/tabris` (breaks "clone → run" for any other path/user) and runs `sudo systemctl start ollama` (not portable — cloud/VPS without systemd, may prompt for a password). Fix: derive the dir from the script itself (`SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`); drop the sudo/ollama line and document the Ollama-as-fallback requirement in the README instead. Code-quality nits folded in from the code review 2026-07-02 (small, pre-publish polish, bundle in the same pass):
   - Split `requirements.txt` into runtime (`openai`, `ollama`, `python-dotenv`, `pydantic`, ...) and `requirements-dev.txt` (`-r requirements.txt` + `pytest`); add `pip-audit` as a periodic habit for dependency CVEs.
   - Add `.pytest_cache/` to `.gitignore`; always run pytest from the project root.
   - `.env.example`: stray `)` in a comment, missing trailing newline.
   - `core/memory_manager.py`: list-comprehension closing `]` misaligned (valid but confusing); `"HAS_CHANGES: yes" not in raw_response` string match is fragile against model formatting variance (`HAS_CHANGES:yes`, casing) — normalize before comparing.
   - `main.py`: `from datetime import datetime as _datetime` is imported inside a function — move to the top-level imports.
41. ⬜ Security pass: confirm no secrets in git history (if any were ever committed, rotate keys).
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
  (functional for daily use): persistent memory + internet (`web_search`/`web_fetch`) + Telegram +
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
| Prompt injection in memory distillation | Raw conversation text is embedded in the distillation prompt; a user could type `HAS_NEW_FACTS: yes` / `FACTS:` lines to spoof the parser format. Mitigated today by the human `si/no` confirmation before any `save_fact` (single-user → low real risk). Becomes real with multi-user or auto-confirmation — revisit then: fence/escape user turns or separate them from the instruction block. (Code review 2026-06-24.) |
| Burnout / runway pressure | Portfolio milestones every phase = visible progress even if revenue lags |
