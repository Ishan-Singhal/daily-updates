#!/bin/bash
# === Daily Updates Agent - Local Dashboard Server Setup ===
# Runs a persistent local HTTP server (via launchd, starts on login, restarts
# if it crashes) serving dashboard/index.html at http://localhost:3000
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$(command -v python3)"
PLIST_LABEL="com.dailyupdates.dashboard"
PLIST_DEST="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

mkdir -p "$REPO_DIR/logs"

sed \
  -e "s#__PYTHON_PATH__#${PYTHON_PATH}#g" \
  -e "s#__DASHBOARD_DIR__#${REPO_DIR}/dashboard#g" \
  -e "s#__REPO_DIR__#${REPO_DIR}#g" \
  "$REPO_DIR/scripts/com.dailyupdates.dashboard.plist" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Installed and started ${PLIST_LABEL}."
echo "  Dashboard: http://localhost:3000"
echo "  Plist:     $PLIST_DEST"
echo "  Logs:      $REPO_DIR/logs/dashboard_server.log"
echo ""
echo "It restarts automatically on crash and starts on login (KeepAlive)."
echo ""
echo "To stop it:"
echo "  launchctl unload $PLIST_DEST"
echo ""
echo "To remove it entirely:"
echo "  launchctl unload $PLIST_DEST && rm $PLIST_DEST"