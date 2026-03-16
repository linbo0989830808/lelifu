#!/usr/bin/env bash
# monitor_restart.sh - check a URL, if non-200 then print restart suggestion
URL="$1"
if [ -z "$URL" ]; then
  echo "Usage: $0 <url-to-check>"
  exit 1
fi
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL" || echo "000")
if [ "$STATUS" != "200" ]; then
  echo "[$(date)] $URL returned $STATUS — recommending restart of gateway"
  echo "To restart: openclaw gateway restart"
else
  echo "[$(date)] $URL OK ($STATUS)"
fi
