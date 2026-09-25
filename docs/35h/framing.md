# Framing — 35h · Recite stored memory deterministically

## Research

- **The project already has this pattern.** `forget_fact`, `remember_fact` and `request_link_code`
  all leave the model deciding *when* to act and the code deciding exactly what happens and what
  the result looks like — the model never composes the outcome itself. Item 35j applied the same
  principle to searching: the model is told what to do, the code guarantees it. A tool whose output
  is rendered by code, not narrated by the model, is the established way this project keeps an
  instruction from being one among forty that can lose (`persona.md` already tries the instruction
  route for this exact case, at line 19, and it does not hold).

## Problem

Asked what it remembers, Tabris lists the user's stored facts with a numbering of its own —
resummarized, renumbered — instead of reciting each fact's real id, even though `persona.md`
already forbids exactly this. It cost twice in the same real session: first, while checking whether
a stored instruction had been lost, the incomplete/resummarized recital made it look like data had
gone missing, when the only way to know for certain is to see the facts exactly as stored; second,
`forget_fact` acts on a fact's real id, so a user replying "number 3" against the model's own
numbering can make the model retire a different real fact than the one they meant.

## Who it is for

Anyone who asks Tabris what it remembers about them, or who wants to correct or forget a specific
fact — today the owner and the beta-testers.

## Evidence it matters

2026-09-01: asked what it remembered, Tabris recited facts 1–15 in its own numbering while the
owner was investigating whether a stored instruction had been lost to a distillation bug — the
renumbered, resummarized list could not settle that question on its own.

## Out of scope

1. **Acting on a fact from the same turn.** `list_facts` shows facts; it never calls `forget_fact`
   or `remember_fact` itself. Purely a presentation fix — no memory behavior changes.
2. **What deserves to become a fact, or how distillation summarizes.** That is item 35g.

## Decision

Build. Feature tier: spec and design before any code.

---

**Exit gate**

- [x] Research done and sources cited
- [x] Problem is one paragraph a stranger could read
- [x] Anti-scope is named
- [x] Evidence exists beyond the owner's intuition
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
