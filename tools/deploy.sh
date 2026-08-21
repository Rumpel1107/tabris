#!/usr/bin/env bash
# Put one tag into service, or return to a previous one. Same command either way.
set -euo pipefail

DEPLOY_DIR="${TABRIS_DEPLOY_DIR:-/opt/tabris}"
REPO="$DEPLOY_DIR/repo"
VENV="$DEPLOY_DIR/.venvs/tabris"
KEYS_FILE="$DEPLOY_DIR/tabris.env"
SERVICE=tabris
RUN_AS=tabris

if [ $# -ne 1 ]; then
    echo "usage: sudo $0 <tag>" >&2
    exit 2
fi
TARGET=$1

if [ "$(id -u)" -ne 0 ]; then
    echo "run this with sudo: restarting the service needs root" >&2
    exit 2
fi

as_service_user() { sudo -u "$RUN_AS" "$@"; }

CURRENT=$(as_service_user git -C "$REPO" describe --tags --exact-match 2>/dev/null \
    || as_service_user git -C "$REPO" rev-parse HEAD)
echo "in service: $CURRENT"

rollback() {
    echo "leaving $CURRENT in service"
    as_service_user git -C "$REPO" checkout --force --quiet "$CURRENT"
}

as_service_user git -C "$REPO" fetch --tags --quiet origin \
    || echo "could not reach the remote; continuing with the tags already here"

if ! as_service_user git -C "$REPO" rev-parse --verify --quiet "$TARGET^{commit}" >/dev/null; then
    echo "no such tag here: $TARGET" >&2
    exit 1
fi

as_service_user git -C "$REPO" checkout --force --quiet "$TARGET"
echo "checked out: $TARGET"

if ! as_service_user git -C "$REPO" diff --quiet "$CURRENT" "$TARGET" -- requirements.txt; then
    echo "requirements changed; installing"
    if ! as_service_user "$VENV/bin/pip" install --quiet -r "$REPO/requirements.txt"; then
        rollback
        exit 1
    fi
fi

# Names only: the values are never read, printed, or compared.
missing=""
while read -r name || [ -n "$name" ]; do  # the last line counts even if the file ends without a newline
    grep -qE "^${name}=" "$KEYS_FILE" || missing="$missing $name"
done < <(sed -n 's/^\([A-Z0-9_]\+\)=.*/\1/p' "$REPO/.env.example")
if [ -n "$missing" ]; then
    echo "the keys file is missing:$missing" >&2
    rollback
    exit 1
fi

if ! (cd "$REPO" && as_service_user "$VENV/bin/python" -m pytest -q); then
    rollback
    exit 1
fi

systemctl restart "$SERVICE"
sleep 3
if ! systemctl is-active --quiet "$SERVICE"; then
    echo "the service did not come up on $TARGET" >&2
    rollback
    systemctl restart "$SERVICE"
    exit 1
fi

echo "in service: $TARGET"
