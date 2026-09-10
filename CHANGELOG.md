# Changelog

Internal: written for whoever runs or tests this. Newest on top, one section per tag, entries
grouped by what a reader would notice, each written in the change that earns it.

Nothing before `v0.1.15` is reconstructed here — that history lives in the tags, in `PLAN.md` and
in `docs/defects.md`. *Why: rebuilt from commit archaeology it would invent detail nobody recorded.*

## [Unreleased]

### Changed
- An answer resting on an address the turn never saw no longer reaches the user cut short: it goes back to the model, which is told which addresses it could not justify and can search again to complete what was asked, twice at most. Only what it still cannot justify after that is cut, as before — so a request for five sources comes back with five it can stand behind, instead of the three that survived the cut. The log now names the host of each rejected address, which is what tells an invented domain apart from a real site refused over a detail of its address.
- A web page that could not be read is reported by its host rather than by the address that was tried. Its message is a tool result, and every address in a tool result counts as a source, so failing to fetch an address was a way of turning an invented one into a source it could then cite.

## [v0.1.17] — 2026-09-09

### Changed
- An answer no longer carries a link the turn never saw. Every address in a reply is checked against what the turn actually had in front of it — the search results, the conversation, the message the user just wrote — and the block citing anything else is removed whole, its description with it, because an invented address arrives with an invented summary. The removal is silent; when nothing survives it, the reply says it has no sources it can confirm and offers to search again.
- A web search now hands the model the text of the pages it found, not only the search engine's snippet: the first 4000 characters of each of the first three results, so an answer can rest on what the page says instead of on a two-line summary. A whole turn carries 16000 characters of page text at most; once spent, further searches in that turn return snippets alone, exactly as before.

## [v0.1.16] — 2026-09-08

### Added
- `docs/defects.md` — what broke after an item was called done: symptom, cause, fix, how it was caught, and the class of mistake. Seeded with the six defects that were already known, three of which had recurred.
- `CHANGELOG.md` — this file.

### Changed
- `CONTRIBUTING.md` now states when a review runs and what performs it, and that a defect row is a fence: find why something is there before removing it.
- `web_fetch` reads public web addresses only: anything that is not `http(s)`, and any host resolving to a loopback, link-local, private or otherwise non-public address, is refused before a request leaves the machine. Redirects are followed by hand, each hop checked the same way, up to `WEB_FETCH_MAX_REDIRECTS`.
- What `web_search` and `web_fetch` bring back now reaches the model wrapped in `<tool_output>` tags, and the system prompt states that fenced tool output is material to report on, never instructions to follow.
