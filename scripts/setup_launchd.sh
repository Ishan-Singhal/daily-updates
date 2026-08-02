#!/bin/bash
# === Daily Updates Agent - macOS launchd Setup ===
# Schedules daily_update.py to run daily at 7:00 AM via launchd,
# so it can send the brief through Messages.app on this Mac.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$(command -v python3)"
PLIST_LABEL="com.dailyupdates.agent"
PLIST_DEST="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

mkdir -p "$REPO_DIR/logs"

sed \
  -e "s#__PYTHON_PATH__#${PYTHON_PATH}#g" \
  -e "s#__SCRIPT_PATH__#${REPO_DIR}/daily_update.py#g" \
  -e "s#__REPO_DIR__#${REPO_DIR}#g" \
  "$REPO_DIR/scripts/com.dailyupdates.agent.plist" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo "Installed and loaded ${PLIST_LABEL} (runs daily at 7:00 AM)."
echo "  Plist:  $PLIST_DEST"
echo "  Logs:   $REPO_DIR/logs/daily_update.log"
echo ""
echo "To change the time, edit $PLIST_DEST (StartCalendarInterval), then run:"
echo "  launchctl unload $PLIST_DEST && launchctl load $PLIST_DEST"
echo ""
echo "To run it now for testing:"
echo "  launchctl start ${PLIST_LABEL}"
echo ""
echo "To remove the schedule:"
echo "  launchctl unload $PLIST_DEST && rm $PLIST_DEST"
echo ""
echo "NOTE: launchd only fires this job while macOS is awake. If your Mac is"
echo "asleep or the lid is closed at 7:00 AM, the job will NOT run until it wakes."
echo "To make the Mac auto-wake (screen stays off, no need to open the lid) a"
echo "few minutes before the job runs, set a scheduled wake (needs your password):"
echo ""
echo "  sudo pmset repeat wake MTWRFSU 06:55:00"
echo ""
echo "This works even with the lid closed, as long as the Mac is plugged into"
echo "power (scheduled wake is unreliable on battery with a closed lid). Run"
echo "'pmset -g sched' to confirm it's set, or 'sudo pmset repeat cancel' to undo."
