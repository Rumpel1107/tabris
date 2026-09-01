<div align="center">

# Tabris

**A personal, always-on AI assistant that remembers you.**

[![Python](https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-in%20development-orange)](PLAN.md)
[![Channels](https://img.shields.io/badge/channels-CLI%20%7C%20Discord-5865F2?logo=discord&logoColor=white)](#-cli-vs-discord)

Self-hosted · Multi-user · Provider-agnostic

</div>

---

Tabris does not try to out-reason the large chat assistants. Its value is elsewhere: it **remembers you** across conversations, it is **yours** — self-hosted and multi-user — and it stays available on the channels you already use.

Under the hood, each kind of request runs on a model chosen for that job rather than one model doing everything — and if a provider is down or out of quota, the next one takes over automatically.

---

## ✨ Features

- **Persistent memory** — facts about each user are distilled from conversation into SQLite and injected into later sessions. Memory is append-only and reversible: facts are retired, never deleted. Users stay in control of it from the conversation itself: ask what is stored, have something forgotten or remembered, and correct their own profile.
- **Multi-user by design** — identity is `(channel, key)`, never a name. Each user gets their own memory, language, location and timezone.
- **One profile across channels** — a short-lived code issued on one channel and pasted on another links both to the same profile, so the memory follows the person rather than the account.
- **Web access** — the assistant searches the web and reads pages when a question needs current information.
- **Voice and images** — a voice message is transcribed and answered like any other message, and a photo or screenshot is looked at and answered. Neither is ever written to disk: what is stored is the text, plus a note that something came with it.
- **A model per task** — each request is routed to a role, and every role runs on the model picked for that job: a small fast one classifies intent, a code-strong one answers programming questions, a dedicated one distills memory in the background, and general chat gets its own. Roles and their models are plain data in `config.py`.
- **Automatic fallback** — each role carries an ordered list of providers. On error or exhausted quota the next one takes over, ending with a local model as the last resort.
- **Channel-agnostic core** — channels are thin adapters over shared logic, so a new one is an adapter rather than a rewrite. Onboarding, abuse limits and memory are written once and inherited by every channel.
- **Guarded by default** — every incoming message passes a length cap and a per-user rate limit before it reaches a model, on any channel.

---

## 🚀 Quick start

```bash
git clone https://github.com/Rumpel1107/tabris.git
cd tabris
./tools/setup.sh
```

`tools/setup.sh` finds a suitable Python, creates the virtualenv outside the repo, installs dependencies, locks down file permissions, and verifies the install by running the test suite. It is safe to re-run and never overwrites an existing `.env`.

On its first run it creates `.env` from `.env.example`. Add your API keys there — **one model provider is enough to start**; search and Discord keys are optional.

Then run it:

```bash
~/.venvs/tabris/bin/python -m channels.cli          # command line
~/.venvs/tabris/bin/python -m channels.discord_ch   # Discord bot
```

> **Requirements:** Python 3.13+ and at least one model provider API key.

---

## 💬 CLI vs Discord

| | Command line | Discord |
|---|---|---|
| **Start** | `python -m channels.cli` | `python -m channels.discord_ch` |
| **Identity** | local id file (`data/tabris_client_id`) | Discord user id |
| **Ending a session** | say that you want to exit | the bot stays online |
| **Extra setup** | none | bot token + **Message Content Intent** enabled in the Discord Developer Portal |

Both channels run the same onboarding — language, name and city, asked in conversation — and a channel starts as its own profile. To join them, ask Tabris on a channel it already knows you for a link code and paste it as the first message on the new one: from then on both share one profile and one memory.

---

## 🔐 Leaving, and taking your data with you

Any account can be exported, suspended, restored and erased. None of it is reachable from a chat — whoever runs the server does it from the operator tool:

```bash
python -m tools.admin export 3        # write everything stored about user 3 to a JSON file
python -m tools.admin deactivate 3    # export first, then stop the account from conversing
python -m tools.admin reactivate 3    # bring the account back and destroy the export
python -m tools.admin purge-auto      # the daily pass: accounts past their grace window, conversation past the retention window
python -m tools.admin purge-force 3   # erase one account now (--skip-grace to not wait out the window)
```

A suspended account stops conversing immediately and keeps everything for a grace window (14 days, `ACCOUNT_GRACE_DAYS`), so it can still be restored intact. When the window ends the account is erased for good, and the export file lives exactly as long as the window does.

Conversation is not kept forever either: the same daily pass erases every message older than the retention window (30 days, `MESSAGE_RETENTION_DAYS`). It is a real delete, not a flag, and it takes retired messages with it. What survives is what was distilled into facts, which is the layer meant to last — and the prompt only ever loads the most recent exchanges anyway. One honest caveat, the same one that applies to erasing an account: daily backups rotate over seven days, so a message deleted today can still exist in a copy for up to a week more.

---

## 🛰️ Running it always-on

A deployment keeps data and keys **outside** the checkout, so an update can never touch them:

```
/opt/tabris/
  repo/         the checkout, parked on a tag
  data/         database and exports
  .venvs/       the virtualenv
  tabris.env    the keys, as KEY=value — no quotes, no spaces
  deploy.sh     the deploy script, kept outside the checkout it rewrites
```

The keys file is read by the service manager, which does **not** apply dotenv rules: a quoted value arrives with its quotes attached and fails as if the key were wrong.

Four units live in `deploy/`, installed into the system and enabled:

| Unit | What it does |
|---|---|
| `tabris.service` | the Discord channel, restarted on failure and started with the machine |
| `tabris-purge.timer` | daily: erases accounts past their grace window, and conversation past the retention window |
| `tabris-backup.timer` | a dated copy of the database into `/var/backups/tabris`, keeping the last seven |
| `tabris-probe.timer` | every five minutes, records whether the outside was reachable |

The erasure runs an hour before the backup, so the day's copy is taken without what was just erased.

Putting a version in service, and going back, are the same command:

```bash
sudo /opt/tabris/deploy.sh v0.2.0    # put this tag in service
sudo /opt/tabris/deploy.sh v0.1.9    # go back to the previous one
sudo journalctl -u tabris | grep "starting Tabris" | tail -1   # the version now running
```

Tabris writes its version into the log as it starts, which is the answer to "what is running" that cannot
be wrong: it is the process itself reporting what it loaded. Asking the checkout instead
(`sudo -u tabris git -C /opt/tabris/repo describe --tags`) says what is *on disk*, which is the same
thing only while nobody has touched the checkout without restarting — editing files never changes a
running process.

It records what is in service, checks out the tag, installs dependencies only if they changed, verifies the keys file declares every variable `.env.example` does, runs the whole suite **inside the deployment**, and only then restarts. If any step fails it returns the checkout to the tag that was running and leaves it serving. A tag already fetched deploys and rolls back with no internet at all.

> Run it from `tools/deploy.sh` in a checkout the first time; each successful deploy refreshes the copy at `/opt/tabris/deploy.sh`, which is the one to use from then on.

---

## 🧩 Project layout

```
core/           channel-agnostic logic: conversation, onboarding, memory, providers, search, prompts, database
channels/       thin adapters, one per channel: cli.py, discord_ch.py
tools/          operator scripts: setup.sh, admin.py (export, suspend, restore, erase),
                backup.py, probe.py and deploy.sh
deploy/         the service and timer definitions for an always-on host
config.py       structure and non-secret configuration (roles, providers, limits)
prompts/        persona.md — the assistant's identity, loaded into the system prompt
data/           SQLite database, local identity file and data exports — gitignored, created on
                first run; override its location with TABRIS_DATA_DIR
.env            API keys — gitignored, created from .env.example
```

---

## 🧪 Tests

```bash
~/.venvs/tabris/bin/python -m pytest
```

---

## 📚 Documentation

| File | What it covers |
|---|---|
| [`PLAN.md`](PLAN.md) | Goals, decisions, architecture and roadmap — the single source of truth |
| [`AGENTS.md`](AGENTS.md) | Entry point for AI agents — holds no rules, points at the files that do |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How the project is run: setup, tests, code conventions, architecture patterns |

---

## 📄 License

[MIT](LICENSE)
