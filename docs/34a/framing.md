# Framing — item 34a, audio input

## Research

- Speech-to-text on the Groq key already in use costs about $0.04 per hour of audio, with a free tier of 2,000 requests/day and 7,200 audio-seconds/hour and a 10-second minimum billed per request — [Groq speech-to-text](https://apio.sh/apis/groq-speech-to-text), [Whisper API pricing comparison](https://tokenmix.ai/blog/whisper-api-pricing).
- The same Whisper model billed through OpenRouter costs 9× more, and transcription on Gemini is more accurate but between 17 and 27× more expensive — measured in the roster review of 2026-08-18, recorded as decision D11.
- A voice message arrives as a message carrying a flag that separates it from an ordinary audio attachment, and the attachment exposes its duration, its type and its bytes — [Discord message resource](https://docs.discord.com/developers/resources/message), confirmed in the installed `discord.py` 2.7.1.
- Both the provider and Discord cap a file at 25 MB on a free account, so no message can arrive that the transcriber has to refuse for being too large.
- The transcription response reports the detected language and the duration without asking for them — verified 2026-08-27 against the real endpoint.

## Problem

Tabris is only reachable by typing, and the moments its owner most needs it are the ones where typing is slowest or impossible: out running errands, driving, walking, hands busy. Today those thoughts either wait until he is back at a keyboard — by which time most are lost — or cost a minute of careful thumb-typing for something he could have said in eight seconds. Every other channel he uses accepts a voice message, so the gap is felt as Tabris being the one place that does not.

## Who it is for

The owner first, in the situations above. Beta-testers reach it for free once it exists, since the channel and the identity model already carry them. It deliberately does not serve anyone who wants to send Tabris third-party recordings to summarize.

## Evidence it matters

Stated by the owner on 2026-08-27, unprompted, as the primary case: away from home, doing errands or driving, where speed matters and typing takes longer. A second, weaker case — a short note from the sofa out of laziness — was named as real but not the one that decides the design.

## Out of scope

- **Spoken replies.** Tabris answers in writing, and the answer waits until the owner can look at the screen. Named explicitly because the primary scenario has eyes busy too, so this is the obvious next ask; it becomes its own roadmap item rather than growing this one.
- **Any audio that is not a voice message recorded in Discord.** Forwarded recordings, music, files. This is what keeps a half-hour attachment from turning into minutes of waiting and a wall of text entering the conversation.
- Video, and audio on the command line, which cannot send it.

## Decision

Build. The engine, the account, the channel and the libraries are all in place and verified; the item's cost is design and wiring, not procurement.
