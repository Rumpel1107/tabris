# Framing — item 34b, image input

## Research

- All four providers already in the roster accept images today, which was not true when this item was written. Gemini is natively multimodal; Groq serves Qwen 3.6 / 3.8 27B with a 20 MB request cap, at most 5 images and 2048 tokens per image; DeepSeek added vision on 2026-08-21 as an experimental endpoint capped at 384 tokens per image; OpenRouter carries free vision models, the strongest being Gemma-4-31B-IT — [Groq vision](https://console.groq.com/docs/vision), [DeepSeek V4 Flash vision](https://codepick.dev/en/guides/deepseek-v4-flash-vision-guide/), [OpenRouter vision models](https://openrouter.ai/collections/vision-models).
- An image travels inside the ordinary chat call as a base64 data URL, the same way the OpenAI API takes it, so the provider layer keeps its shape — [Gemini OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai).
- `gemini-3.5-flash-lite`, already first in no role but second in `general`, described a test image correctly in a real call on 2026-08-17. That call proved *describing*, not reading.
- **Verified 2026-08-30 with real calls**, since the item is sized for a capability nothing had demonstrated. A 1920×1080 terminal screenshot at 15px type, carrying an exception, two file paths with line numbers and three configuration values, was sent to four candidates and asked for a verbatim transcription. `gemini-3.5-flash-lite` returned it exactly in 2.3s; MiniMax M3 on OpenRouter's free tier returned it exactly; Groq's `qwen/qwen3.8-27b` read the exception and every path correctly in 2.2s but mangled one identifier; `google/gemma-4-31b-it:free` never answered, refused by OpenRouter's shared free pool rather than by the account's own quota. Reading a screen is therefore established, and so is the fact that a free shared pool cannot be relied on as the last link.
- Video is affordable at the model (~300 tokens per second of footage) and blocked at the channel: Discord caps an attachment at 25 MB on a free account, recorded in this project during item 39a — [Gemini video understanding](https://ai.google.dev/gemini-api/docs/video-understanding).
- **Assumption (unverified):** a four-minute video recorded on a phone runs between 100 and 400 MB, an order of magnitude past that cap.

## Problem

Tabris can only be shown things in words. The owner's most frequent unmet case is the one hardest to describe by typing: a screenshot, or a photograph of his own monitor, held up to ask what something means or why it is failing. Retyping an error, a form or a table into a message is slow and lossy, and describing a screen well enough to get a useful answer is often harder than the original question. Every general assistant his testers use accepts a photo, so its absence reads as Tabris being the one that cannot look.

## Who it is for

The owner first, whose dominant case is reading a screen. Beta-testers next, whose cases are broader and were named from real trials: identifying objects, films, places. The subject matter is deliberately not narrowed — it is open-ended language, like everything else that already arrives as text.

## Evidence it matters

Named by the owner on 2026-08-30 as his normal use, unprompted: screenshots asking for help with something he does not understand, and photographs of his PC. Testers' broader uses come from conversations and trials he ran with them, not from intuition. He also states this item is what makes Tabris ready to open to more testers, which sets its position in the round.

## Framing

The subject matter cannot be enumerated, so the item is sized by its hardest demand instead: **reading text inside a screenshot.** A model that reads a screen legibly describes an object or recognizes a place for free; the reverse does not hold. This is what decides which models qualify, how far an image may be downscaled before it is sent, and what size is accepted — and it is what disqualifies a 384-token-per-image ceiling, which cannot carry a screen's text at any useful resolution.

## Out of scope

- **Image generation.** It is an output modality, not an input one: it changes the shape of a reply and touches the path every answer takes. Reaffirmed on 2026-08-30, having been out since 2026-07-01.
- **Video.** Out for a channel reason, not a model one — most real recordings cannot be uploaded at all. Recorded here so a future review starts from the actual blocker: where the file enters, not what the model can watch. It also carries decisions this item does not: a duration limit, a resolution setting worth 3× in cost, and an audio track that overlaps item 34a.
- The command line, which cannot send an image.

## Decision

Build. The keys, the providers and the channel are all in place; the cost is design and wiring, not procurement. The capability the framing rests on was measured before the design began rather than assumed, and it holds on more than one provider, so the item does not depend on a single vendor staying available.

---

**Exit gate**

- [x] Research done and sources cited
- [x] Problem is one paragraph a stranger could read
- [x] Anti-scope is named
- [x] Evidence exists beyond the owner's intuition
- [x] No `[NEEDS CLARIFICATION]` marker is left unresolved
- [x] Every claim here was confirmed in conversation before it was written down
