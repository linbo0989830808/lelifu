#!/usr/bin/env bash
# auto_pr.sh - simple helper to create branch, commit, push, and open PR via gh
# Usage: ./scripts/auto_pr.sh "branch-name" "commit-message" path/to/file
set -e
BRANCH="$1"
MSG="$2"
FILE="$3"
if [ -z "$BRANCH" ] || [ -z "$MSG" ] || [ -z "$FILE" ]; then
  echo "Usage: $0 \"branch-name\" \"commit-message\" path/to/file"
  exit 1
fi
# create branch
git checkout -b "$BRANCH"
# add and commit file
git add "$FILE"
git commit -m "$MSG"
# ensure origin exists
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "No remote 'origin' set. Please add it with: git remote add origin <url>"
  exit 1
fi
# push branch
git push -u origin "$BRANCH"
# open PR with gh
if command -v gh >/dev/null 2>&1; then
  gh pr create --head "$BRANCH" --title "$MSG" --body "Auto PR created by scripts/auto_pr.sh"
else
  echo "gh not found; branch pushed. Use gh or GitHub UI to create PR." 
fi
