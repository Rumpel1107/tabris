# Decisions

> **What goes in this document:** why something already settled was settled, with the alternative
> that was rejected. Append-only.
>
> Not here: what is still pending (`docs/roadmap.md`), what happened (`docs/log.md`), how the
> project is built (`CONTRIBUTING.md`).

**A row is never edited or deleted once accepted.** Changing your mind adds a new row and flips
the old row's status. Ids are stable and never reused.

| Status | Meaning |
|---|---|
| `accepted` | In force |
| `superseded by Dnn` | Replaced by a later decision |
| `deprecated` | Stopped applying, with nothing replacing it |

Moved from `PLAN.md` §3 on 2026-09-23. D8 and D9 are not missing: they described the owner, the
portfolio and the publishable gate, none of which is Tabris's to hold, and were renumbered P1/P2 in
the workspace `PLAN.md` on 2026-09-07. The gap stays rather than being closed, so no reference to
an id written before that date points at the wrong row. Where the original record did not preserve
the rejected alternative, the cell says **not recorded** rather than a reconstruction.

| # | Date | Decision | Rejected alternative | Why | Status |
|---|---|---|---|---|---|
| D1 | — | Migrate from local Ollama to API-based models | not recorded | Removes the GPU/local dependency, enables cheap cloud hosting, costs cents a month at this scale. Local Ollama is kept only as an offline lab fallback | `accepted` |
| D2 | — | DeepSeek as primary brain; Groq and Gemini's free tiers as secondary/fallback | not recorded | DeepSeek is cheap and strong but has no free tier and lower uptime than the majors, so a fallback is required, not optional. Free tiers cover simple tasks and outages at $0, but their ceilings are low: measured 2026-08-18 at Groq 1K requests/day per chat model, OpenRouter `:free` 1K/day (50/day below $10 lifetime credit), Gemini flash-lite ~500/day | `accepted` |
| D3 | — | Provider/role mapping lives in `config.py`; secrets live in `.env` | not recorded | Replicability: clone → copy `.env.example` to `.env` → add keys → run. Keys must never be committed — bots scan GitHub for leaked keys within minutes | `accepted` |
| D4 | 2026-07-20 | Discord bot as the first interface | WhatsApp first — deferred, not rejected outright: it requires Meta Business verification, a dedicated number, and bills business-initiated template messages from the first send | Rumpel's testers already live on Discord through his game servers, so that is where adoption is. Infra-light like Telegram: connects via the gateway/WebSocket, no public webhook or domain needed. Telegram stays a supported second channel, cheap to add through the channel-agnostic core (D5) | `accepted` |
| D5 | — | Channel-agnostic core | not recorded | Tabris logic (routing, memory, agents) must not know whether input came from the CLI or a messaging channel. Channels are thin adapters, so adding one later is an adapter, not a rewrite | `accepted` |
| D6 | 2026-08-18 | Tabris runs as a system service on one always-on host, and the deployment stays host-agnostic by design | Paying for a rented host — evaluated and deferred, not rejected: it buys uptime the project owed no one at the time | With inference via API, Tabris is a lightweight service that needs a machine that stays on, not a particular provider. The unit definition, the data directory and the deploy procedure assume nothing about who owns the machine, so moving to a rented one is re-running the procedure, not a rewrite. The deferral on paying for a host is superseded by D13; the host-agnostic design itself still stands | `accepted` |
| D7 | — | SQLite for structured storage | not recorded | Free, serverless, file-based, ships with Python. Used for per-user memory/profiles. Skills transfer directly to any SQL job | `accepted` |
| D10 | — | Search APIs use the same abstraction and fallback shape as the model providers | not recorded | Internet access is a tool, not a new brain. `core/search.py` mirrors `core/providers.py`: an ordered list in `config.py`, tried in order, normalized to a common `{title, url, content}` shape. Swapping or reordering providers is a one-line config change | `accepted` |
| D11 | 2026-08-18 | Groq stays: it is the router's primary and the speech-to-text engine, not a spare | Dropping Groq entirely — evaluated and rejected: a replacement exists for each of its three jobs (router, audio, deep fallback) and each replacement is worse at that job | The router runs on every message and needs the lowest time-to-first-token in the roster (~1s). Speech-to-text is far cheaper on Groq than the alternatives measured at the time. Revisit when a Groq model actually returns an error, not on every market review | `accepted` |
| D12 | 2026-09-02 | A roster is chosen by probing real calls, and reliability is bought by leaving the free tier, not by paying more | Adding direct provider accounts instead of routing through OpenRouter — evaluated and rejected: OpenRouter passes provider rates through untouched and charges 5.5% on credit, so a direct key saves cents while adding a secret to manage in every environment | Every failure found in a day of real use was a quota ceiling, not a model limitation. `general`, `code` and `memory` moved to paid entries on a key the project already holds; the whole assistant costs about US$3/month at 30 turns a day against the owner's US$10 ceiling. Paid does not mean unlimited, which is why `tools/probe_models.py` exists and a model never enters a roster without it | `accepted` |
| D13 | 2026-09-13 | Production moves to a rented host the owner already pays for | Staying on the home host — evaluated and rejected: it keeps outages that hit one to three times a week for no gain, and the only argument for staying (memory headroom for another project) is answered by moving that project, not this one | The home host's network, not its hardware, is what takes Tabris down, and it has once failed to bring a service back after a reboot. A rented host was already being paid for by another project, so this costs nothing extra. D6's host-agnostic design is what makes this a move and not a rewrite; supersedes D6's deferral on paying for hosting | `accepted` |
| D14 | — | Memory scales one rung of a ladder at a time — M1 (SQLite: users/facts/messages) is today's rung, M2 (per-user + per-project context, summarized history) and M3 (graph/GraphRAG, or plain embeddings-RAG as its cheaper precursor) are not built ahead of need | Building M2 or M3 now, on the reasoning that memory will eventually need them | M2 waits for a second real user; the full M3 graph waits for all three to hold at once: plain embeddings-RAG over `facts` returns fragments the model cannot relate on its own, more than one user has richly interrelated facts, and there is a real need to explain *why* a memory was recalled — until then it is over-engineering against the workspace plan's scope-creep risk. The embeddings-RAG precursor alone has a lower, separate trigger: facts volume alone overflowing the system prompt's uncapped block, regardless of any relational need. A `fact_links(fact_id, related_fact_id, relation)` table is the cheaper middle ground reachable from M1 before any of this, if navigable relations are ever needed without a graph engine | `accepted` |
