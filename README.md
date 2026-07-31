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

- **Persistent memory** — facts about each user are distilled from conversation into SQLite and injected into later sessions. Memory is append-only and reversible: facts are retired, never deleted, and users can ask what is stored and have it forgotten.
- **Multi-user by design** — identity is `(channel, key)`, never a name. Each user gets their own memory, language, location and timezone.
- **Web access** — the assistant searches the web and reads pages when a question needs current information.
- **A model per task** — each request is routed to a role, and every role runs on the model picked for that job: a small fast one classifies intent, a code-strong one answers programming questions, a dedicated one distills memory in the background, and general chat gets its own. Roles and their models are plain data in `config.py`.
- **Automatic fallback** — each role carries an ordered list of providers. On error or exhausted quota the next one takes over, ending with a local model as the last resort.
- **Channel-agnostic core** — channels are thin adapters over shared logic, so a new one is an adapter rather than a rewrite.

---

## 🚀 Quick start

```bash
git clone https://github.com/Rumpel1107/tabris.git
cd tabris
./setup.sh
```

`setup.sh` finds a suitable Python, creates the virtualenv outside the repo, installs dependencies, locks down file permissions, and verifies the install by running the test suite. It is safe to re-run and never overwrites an existing `.env`.

On its first run it creates `.env` from `.env.example`. Add your API keys there — **one model provider is enough to start**; search and Discord keys are optional.

Then run it:

```bash
~/.venvs/tabris/bin/python main.py          # command line
~/.venvs/tabris/bin/python discord_ch.py    # Discord bot
```

> **Requirements:** Python 3.13+ and at least one model provider API key.

---

## 💬 CLI vs Discord

| | Command line | Discord |
|---|---|---|
| **Start** | `python main.py` | `python discord_ch.py` |
| **Identity** | local id file (`tabris_client_id`) | Discord user id |
| **Onboarding** | asks for name, language and city | taken from the Discord profile |
| **Ending a session** | say that you want to exit | the bot stays online |
| **Extra setup** | none | bot token + **Message Content Intent** enabled in the Discord Developer Portal |

Each channel is a separate profile today, with its own memory. Linking several channels to one profile is on the roadmap.

---

## 🧩 Project layout

```
core/           channel-agnostic logic: conversation, memory, providers, search, prompts, database
main.py         command-line adapter
discord_ch.py   Discord adapter
config.py       structure and non-secret configuration (roles, providers, limits)
persona.md      the assistant's identity, loaded into the system prompt
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
| [`AGENTS.md`](AGENTS.md) | How to collaborate on this repository, for humans and AI agents |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Code conventions, testing rules and architecture patterns |

---

## 📄 License

[MIT](LICENSE)
