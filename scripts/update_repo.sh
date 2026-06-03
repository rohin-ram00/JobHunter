#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo
echo "======================================="
echo "      JOBHUNTER AUTO UPDATE"
echo "======================================="
echo

echo "[1/4] Pulling latest repository..."
git pull origin main

echo
echo "[2/4] Staging files..."
git add .

echo
echo "[3/4] Creating commit..."
timestamp="$(date +'%Y-%m-%d %H:%M:%S')"

if git diff --cached --quiet; then
  echo
  echo "No changes detected."
else
  git commit -m "Auto update $timestamp"
  echo
  echo "Commit created."
fi

echo
echo "[4/4] Pushing to GitHub..."
git push origin main

echo
echo "======================================="
echo " Repository successfully updated"
echo "======================================="
echo
