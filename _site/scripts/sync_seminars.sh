#!/usr/bin/env bash
# Fetch the latest seminar schedule from the Google Sheet, regenerate the
# _data/seminars-*.yml files, and commit+push the result if anything changed.
#
# Usage:
#   ./scripts/sync_seminars.sh              # sync, commit, and push
#   ./scripts/sync_seminars.sh --no-push    # sync and commit only
#   ./scripts/sync_seminars.sh --dry-run    # sync only, no git actions

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PUSH=1
COMMIT=1
for arg in "$@"; do
  case "$arg" in
    --no-push) PUSH=0 ;;
    --dry-run) PUSH=0; COMMIT=0 ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

python3 "$REPO_ROOT/scripts/sync_seminars.py"
jekyll build

if [ "$COMMIT" -eq 0 ]; then
  echo "Dry run: skipping git commit/push."
  exit 0
fi

if git diff --quiet -- _data csv_exports _site && git diff --cached --quiet -- _data csv_exports _site; then
  echo "No changes to commit."
  exit 0
fi

git add _data/seminars-*.yml csv_exports/*.csv _site
git commit -m "Auto-update seminar schedule from Google Sheet"

if [ "$PUSH" -eq 1 ]; then
  git push
else
  echo "Committed locally. Skipping push (--no-push)."
fi
