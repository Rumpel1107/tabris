import logging
import subprocess

logger = logging.getLogger(__name__)

GIT_TIMEOUT = 5  # a checkout answers instantly; this only bounds a git that hangs on a broken repository


def describe(base_dir):
    """Return the tag the checkout is on, so a log line says which version is running.

    Falls back to the commit when no tag points here, and to "unknown" when git cannot answer
    at all — a missing version is worth a warning, never a failed start.
    """
    try:
        answer = subprocess.run(
            ["git", "-C", base_dir, "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            check=True,
        )
    except Exception as failure:
        logger.warning("could not read the running version (%s)", type(failure).__name__)
        return "unknown"
    return answer.stdout.strip() or "unknown"
