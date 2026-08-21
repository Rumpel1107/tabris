import argparse
import config
import httpx
import logging
import sys
import time

logger = logging.getLogger(__name__)


def reach(url: str, timeout: float) -> float:
    """Return how long the endpoint took to answer, raising if it did not answer well."""
    started = time.monotonic()
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return time.monotonic() - started


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Record once whether the outside world is reachable from here.",
    )


def main(argv=None) -> int:
    """Probe once, leaving one line in the system log and an exit code the scheduler records."""
    build_parser().parse_args(argv)
    try:
        seconds = reach(config.PROBE_URL, config.PROBE_TIMEOUT)
    except Exception as failure:
        logger.warning("probe: unreachable (%s)", type(failure).__name__)
        return 1
    logger.info("probe: reachable in %.2fs", seconds)
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)  # its per-request line repeats what this probe already reports
    sys.exit(main())
