# Tasks — 37b · Move production to the rented host

Phase 4 of the method. Framing, spec and design are item 37's, re-run on another machine: every
acceptance criterion in `docs/37/spec.md` must hold on the new host exactly as it held on the old
one, and the decisions in `docs/37/plan.md` are not reopened. This file records only what a move
has and an install did not, then the slices in execution order.

## Decisions new to the move

| # | Chosen | Rejected | Why |
|---|---|---|---|
| M1 | **The database travels as a copy taken by `tools/backup.py`**, the same mechanism as the daily backup | A plain file copy of `tabris.db` | The database runs in write-ahead mode: part of the data sits in the `-wal` file until a checkpoint, so a copy of the main file alone can miss the last writes and look complete. The engine's backup call produces one consistent file; it is also what item 37 already uses and verifies by reading the copy back (AC16) |
| M2 | **The old service stops, and is disabled, before the new one starts** — minutes of downtime, accepted | Start the new host first for zero downtime; or regenerate the channel token so the old host is cut off | Both hosts hold the same token, and two processes on one token answer every message twice. A new token would also cut the old host off, but it means editing the keys file in the middle of the cutover; stopping the service does the same with one command and leaves the old deployment intact as the way back |
| M3 | **The old deployment stays installed but stopped for seven days, then is removed entirely** — units, directory, user and backups | Remove it on cutover day; or keep it indefinitely as a spare | Removing it at once leaves no way back if the new host misbehaves in its first days, and the first days are when it would. Keeping it is a second copy of the testers' conversations and facts on a machine that no longer serves them, which the privacy stance of item 34c does not allow. Seven days is the backup rotation window, so nothing the old host holds outlives what the new one already has |

## Slices

| # | Slice | Covers | How it is verified | Done |
|---|---|---|---|---|
| 1 | **Prepare the new host** — system user without a shell or sudo, `/opt/tabris` layout, clone parked on the tag the old service reports in its log, virtualenv, keys file copied from the old host (`KEY=value`, owner-only), `deploy.sh` in place | 37 slice 3: AC4, AC13–AC16 | The whole suite runs green inside the deployment as the service user; nothing is running or enabled yet | ✅ 2026-09-13 |
| 2 | **Install the four units** without enabling or starting any of them | 37 slices 4–6, install half | The service manager lists all four, every one inactive and disabled | ✅ 2026-09-13 |
| 3 | **The cutover** — on the old host: stop and disable the service and the three timers, take a backup, and hand it over together with the channel identity file and the seven dated backups; on the new host: place the copy as the database, owner-only, then enable and start the service and the timers | M1, M2; 37: AC1, AC5, AC6, AC15, AC16, AC17 | Tabris answers on Discord; the start line in the log names the tag; the count of users, active facts and messages matches the source; the log carries no message text; the keys appear in no unit, process list or log | ✅ 2026-09-13 (2 users, 28 active facts, 718 messages on both sides; first reply and a forced search answered from the new host) |
| 4 | **Reboot the new host for real** | 37: AC2, AC3, AC9 | The service is back on Discord without anyone touching it; the three timers show a next run | ✅ 2026-09-13 (on Discord 5 s after the unit started; probe fired at boot + 2 min) |
| 5 | **Retire the old deployment**, seven days after slice 3 — units, `/opt/tabris`, the system user, `/var/backups/tabris` | M3 | Nothing of it is left on the old host, and Tabris is still answering from the new one | ⬜ |

## Notes

- **Slice 3 is the milestone**, and the only one with downtime: from stopping the old service to
  the first reply from the new one. Everything before it can be done, checked and redone with the
  old host still serving.
- **Between slice 3 and slice 5 the old host is the way back.** Returning is the reverse of the
  cutover — stop here, start there — with the data the new host accumulated in between carried back
  by the same backup mechanism. Nothing else is needed, which is why M3 keeps it.
- **Nothing in this file names a machine.** The repository is public; which two hosts these are
  lives outside it.
- **The backup file name comes from the host clock** (item 37, notes). Slice 1 checks the new host's
  time zone before anything is scheduled, so an evening backup does not carry tomorrow's date.
- **The connectivity probe moves too, and stays on** (owner's decision, 2026-09-13). Its reason
  — counting a home network's outages — is gone, but it is the one instrument that would show the
  new host's uptime as a number instead of an expectation. Retiring it is a roadmap decision to
  take with a month of its log in hand, not here.
- **Every step is run by the owner and confirmed before the next**, as in item 37.

---

**Exit gate**

- [x] Slices are in execution order
- [x] Each slice states its verification
- [x] No slice leaves code that nothing calls
- [x] The phase documents were read against each other (`docs/37/spec.md`, `docs/37/plan.md`, PLAN D6/D13, item 37b); no contradiction found
- [x] Every claim here was confirmed in conversation before it was written down
