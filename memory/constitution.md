# Constitution

What this project never negotiates. Principles only — how the project is run is
`CONTRIBUTING.md`, what is pending is `docs/roadmap.md`, what phase follows which is the
`/method` skill.

This project builds a personal, always-on AI assistant. Its differential is not raw reasoning —
it is persistent memory, ownership, availability, and the input modalities the owner actually
uses.

1. DETERMINISTIC FIRST: when an answer is defined by a rule that can be written down — a format,
   a bounded set, a comparison — it is written in code. A model call is reserved for open-ended
   language, where enumerating the cases breaks instead of scaling. Every model output that
   reaches stored data passes a deterministic check on the way in: ids are filtered against what
   was actually shown, counts are capped, formats are parsed rather than trusted.
2. CHANNEL-AGNOSTIC CORE (D5): `core/` never knows which channel — CLI, Discord, a future one —
   the input came from. Channels are thin adapters that call the core; adding a channel is
   writing an adapter, never touching `core/`.
3. PROVIDER ABSTRACTION AND FALLBACK (D2/D10): model providers, search providers and
   transcription providers share one shape — an ordered list, tried in order, falling through to
   the next on error or quota, every response normalized to a common shape. Adding a provider
   means mirroring the existing structure, never special-casing a call site.
4. A MODEL ENTERS A ROSTER ONLY AFTER BEING PROBED: never on the strength of documentation, which
   has twice named a model that does not exist or a rate limit that does not apply to this
   account. A live probe with a turn-shaped payload is the only trustworthy source for whether a
   candidate answers, how fast, and whether it reads an image or honours a forced tool call.
5. A MODEL'S BEHAVIOUR IS MEASURED BEFORE IT CHANGES, NEVER REWORDED ON A HUNCH: a prompt or a
   roster changes only after a probe has run against the new wording or model, because a clause
   that reads as an improvement has already been measured here to move noise rather than
   behaviour. Every real miss becomes a case in the probe's lot, which grows from production, not
   from imagination.
6. SECRETS NEVER ENTER THE REPOSITORY: structure and non-secret configuration live in `config.py`
   (committed); every key and credential lives in `.env` (gitignored), documented by
   `.env.example`. A secret is read from a file only — never a service definition, a command
   line, or a log line.
7. A SCHEMA CHANGE IS ADDITIVE: a new column, table or index, guarded so it is safe to run on
   every start. Anything that drops or renames ships in its own change, after the code that used
   it is already in service — a destructive migration cannot be undone by returning to an earlier
   tag, only the daily backup can.
8. FACTS ARE APPEND-ONLY: a fact that becomes false or obsolete is retired by soft-delete
   (`is_active = 0`, scoped by `user_id`), never edited in place, never hard-deleted. A change of
   information is a retirement plus an insertion.
9. TWO DELIBERATE EXCEPTIONS TO APPEND-ONLY, BOTH PRIVACY DELETIONS: erasing a whole account and
   erasing conversation past its retention window are real deletes, because the point of each is
   that the data stops existing. Both are reachable only from the operator tool, never from any
   chat path — adding a third exception is a decision, not a detail.
10. A USER'S DATA NEVER DERIVES FROM THE CODE CHECKOUT: the database, the channel identity file
    and every export hang off `config.DATA_DIR`, never `BASE_DIR`. A deployment keeps its data
    beside the clone, not inside it, so replacing the checkout — a redeploy, a rollback — never
    touches what a user owns.
11. PERSONAL DATA IS CREATED LOCKED DOWN: the database, `.env`, the channel identity file and
    every export are owner-only from the moment they are created, not by a later sweep — a copy
    or a sync recreates a file at the system default, so permissions set after the fact do not
    survive.
12. THE HISTORY SENT TO A MODEL IS BOUNDED, ON TWO AXES: a message count and a combined character
    budget, whichever runs out first. A count alone is blind to size — an image, a document's
    extracted text, or a long message riding along for many turns — so one deterministic rule
    covers every kind of attachment instead of each needing a lifetime of its own.
13. NOTHING COMMITTED IDENTIFIES THE MAINTAINER OR A TESTER: no real machine name, host layout,
    mount path, real name or real location enters code, tests or docs — this repository is
    public. The general mechanism is documented instead; it leaks nothing and serves anyone who
    clones the project.
