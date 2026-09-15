"""Run as `python -m tools.probe_reviewers --out DIR` from the repository root, like the other probes."""
import argparse
import config
import logging
import re
import statistics
import subprocess
import sys
import time

from openai import OpenAI
from pathlib import Path

from core.providers import PROVIDER_CONFIG

logger = logging.getLogger(__name__)

# One model per family, the strongest tier the budget allows; the control is the family the method already reviews with.
MODELS = [
    "openai/gpt-5.6-sol",
    "google/gemini-3.8-flash",
    "deepseek/deepseek-v4-pro",
    "x-ai/grok-4.6",
    "moonshotai/kimi-k3",
    "qwen/qwen3.8-max-0902",
    "z-ai/glm-5.3",
    "anthropic/claude-opus-5",
]


def _finding(defect: str, description: str, hint: str) -> dict:
    return {"defect": defect, "description": description, "hint": re.compile(hint, re.IGNORECASE)}


# Each case is a commit that was called done and later broke; the findings are what the reviewer had to see.
CASES = [
    {
        "commit": "d96722c",
        "label": "time stamp on every turn",
        "findings": [
            _finding("DEF-2", "the assistant's own turns are stamped too, so the model copies the stamp into its replies",
                     r"assistant.{0,60}stamp|stamp.{0,60}assistant|cop(y|ies|ying)|echo|imitat|mimic|learn.{0,30}(format|pattern)"),
        ],
    },
    {
        "commit": "3cc2a9e",
        "label": "fact consolidation (item 35c)",
        "findings": [
            _finding("DEF-1", "facts are shown as `[id] content`, so the model writes the id prefix back into new facts and nothing strips it",
                     r"prefix|\[id\]|\[\d+\]|strip|bracket"),
            _finding("DEF-6", "retire ids are applied even when no new fact came back, so facts are deleted with nothing in their place",
                     r"empty|nothing (in|to) (its|their) place|without (a |any )?(replacement|new)|retire.{0,80}(no|without).{0,20}new|data loss|lose|lost"),
            _finding("DEF-12", "a replacement that collides with an active fact is swallowed as a duplicate and the retire still runs",
                     r"IntegrityError|duplicate.{0,120}(retir|deactivat)|(retir|deactivat).{0,120}duplicate|swallow"),
        ],
    },
    {
        "commit": "83b2fd2",
        "label": "id-prefix stripper",
        "findings": [
            _finding("DEF-3", "the prefix pattern matches one id only, and a merged fact cites several (`[15,58]`)",
                     r"multiple|several|more than one|comma|\[\d+,|list of ids|two ids"),
        ],
    },
    {
        "commit": "5f95e72",
        "label": "images in view (item 34b)",
        "findings": [
            _finding("DEF-7", "session.images is replaced on every turn, so a turn without an image erases the previous one",
                     r"replac|overwrit|eras|(lost|lose|drop).{0,40}(image|previous)|(previous|earlier|prior).{0,30}image|clear"),
        ],
    },
    {
        "commit": "f9cff99",
        "label": "link fence (item 35i, first cut)",
        "findings": [
            _finding("35i-1", "an address the model writes while asking for a tool joins the allowed set, so it authorizes itself",
                     r"assistant.{0,80}(message|turn|url|address|link)|mid-turn|tool.?call.{0,80}(url|address|link)|its own|itself|self-"),
            _finding("35i-2", "a link written in bold or inside markdown is captured with the markup around it",
                     r"bold|\*\*|markdown|markup|trailing|punctuation|parenthes"),
            _finding("35i-3", "the same address encoded and decoded compares unequal, so an accented URL reads as invented",
                     r"encod|percent|unicode|accent|non-ascii|idna|normali[sz]"),
            _finding("35i-4", "the search executor takes `query` only, so a `max_results` the model adds kills the turn",
                     r"max_results|unexpected keyword|TypeError|extra (field|argument|parameter)|lambda query"),
            _finding("35i-5", "the log counts spans, not blocks, so two adjacent removals are reported as one",
                     r"count|span|adjacent|side by side|merged|overlap"),
        ],
    },
]

REVIEW_PROMPT = """You are reviewing a change to a Python project before it is deployed. Your job is to find what is wrong with it — not to say whether it is good.

Report findings only, ordered by weight, most severe first. For each finding give: the file and function, what is wrong in one sentence, and a concrete scenario (inputs or state, then the wrong outcome). Cover correctness, what happens at the edges, what a model in the loop can do with it, and what breaks later. Do not praise, do not summarise the change, do not list what is fine.

The contract the change had to meet — the project's contributing rules at the time — is below, followed by the diff and then the full text of the changed core files after the change.

=== CONTRIBUTING.md ===
{contract}

=== DIFF ===
{diff}

=== FILES AFTER THE CHANGE ===
{files}
"""


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=config.BASE_DIR).stdout


def build_case_input(commit: str) -> dict:
    """The diff without documents, the contributing rules of that day, and the changed core files as they stood after the commit."""
    diff = _git("show", commit, "--", ".", ":!*.md")
    contract = _git("show", f"{commit}~1:CONTRIBUTING.md")
    changed = _git("show", "--name-only", "--format=", commit).split()
    files = "\n\n".join(
        f"--- {path} ---\n{_git('show', f'{commit}:{path}')}"
        for path in changed if path.startswith("core/") and path.endswith(".py")
    )
    return {"diff": diff, "contract": contract, "files": files}


def review_messages(case_input: dict) -> list[dict]:
    return [{"role": "user", "content": REVIEW_PROMPT.format(**case_input)}]


def score(answer: str, findings: list[dict]) -> list[str]:
    """Which expected findings the answer seems to name; a hint match is a pointer for the reader, not a verdict."""
    return [f["defect"] for f in findings if f["hint"].search(answer)]


def _client() -> OpenAI:
    settings = PROVIDER_CONFIG["openrouter"]
    return OpenAI(base_url=settings["base_url"], api_key=settings["api_key"] or "missing", timeout=600, max_retries=0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hand each candidate reviewer the diffs that later broke in production, and report which of the known defects it names.",
    )
    parser.add_argument("--models", nargs="+", default=MODELS, help="OpenRouter model ids (default: the shortlist)")
    parser.add_argument("--cases", nargs="+", default=[c["commit"] for c in CASES], help="Commits to review (default: all)")
    parser.add_argument("--rounds", type=int, default=1, help="Calls per model and case (default 1)")
    parser.add_argument("--out", type=Path, required=True, help="Directory where every answer is written, one file per call")
    return parser


def main(argv=None) -> int:
    """Run the lot, write every answer to disk for reading, and print hits per model, latency and tokens."""
    args = build_parser().parse_args(argv)
    client = _client()
    cases = [c for c in CASES if c["commit"] in args.cases]
    if not cases:
        sys.exit(f"no case matches {args.cases}; known: {', '.join(c['commit'] for c in CASES)}")
    inputs = {c["commit"]: build_case_input(c["commit"]) for c in cases}
    expected = sum(len(c["findings"]) for c in cases) * args.rounds
    answered = 0
    for model in args.models:
        hits, times, tokens_in, tokens_out, errors = [], [], 0, 0, 0
        out_dir = args.out / model.replace("/", "__")
        out_dir.mkdir(parents=True, exist_ok=True)
        for case in cases:
            for round_number in range(args.rounds):
                started = time.monotonic()
                try:
                    response = client.chat.completions.create(model=model, messages=review_messages(inputs[case["commit"]]))
                    answer = (response.choices[0].message.content or "").strip()
                except Exception as error:
                    errors += 1
                    logger.warning(f"{model} on {case['commit']}: {type(error).__name__}: {error}")
                    continue
                times.append(time.monotonic() - started)
                answered += 1
                if response.usage:
                    tokens_in += response.usage.prompt_tokens or 0
                    tokens_out += response.usage.completion_tokens or 0
                named = score(answer, case["findings"])
                hits += named
                (out_dir / f"{case['commit']}-r{round_number + 1}.md").write_text(
                    f"# {model} — {case['label']} ({case['commit']})\n\nhints matched: {', '.join(named) or '-'}\n\n{answer}\n"
                )
        summary = f"{len(hits)}/{expected} hinted"
        if times:
            summary += f", median {statistics.median(times):.0f}s, worst {max(times):.0f}s, {tokens_in} in / {tokens_out} out tokens"
        if errors:
            summary += f", {errors} error(s)"
        print(f"{model:<32} {summary}")
    print(f"\nanswers in {args.out} — the hints point, the reader decides")
    return 0 if answered else 1


if __name__ == "__main__":
    logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    sys.exit(main())
