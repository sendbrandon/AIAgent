#!/usr/bin/env bash
# Start a morning-content-brief run right now (works while the deployment is paused).
# Run from the repo root after `ant apply` has written claude-lock.json.
set -euo pipefail

LOCK="claude-lock.json"
KEY='./agents/morning-content-brief/deployment-weekday.yaml'

if [ ! -f "$LOCK" ]; then
  echo "claude-lock.json not found. Run ant apply first (see agents/morning-content-brief/README.md)." >&2
  exit 1
fi

DEPLOYMENT_ID=$(jq -r --arg k "$KEY" '.resources[$k].id // empty' "$LOCK")
if [ -z "$DEPLOYMENT_ID" ]; then
  echo "Deployment not in claude-lock.json yet. Apply agents/morning-content-brief/deployment-weekday.yaml first." >&2
  exit 1
fi

echo "Triggering deployment $DEPLOYMENT_ID ..."
ant beta:deployments run --deployment-id "$DEPLOYMENT_ID" > /dev/null

SESSION_ID=$(ant beta:deployment-runs list --deployment-id "$DEPLOYMENT_ID" --max-items 1 --transform session_id -r)
echo "Session: $SESSION_ID"
echo "Console: https://platform.claude.com/workspaces/default/sessions/$SESSION_ID"
echo "         (replace 'default' with your workspace ID if the key is not in the Default workspace)"
echo "Watch live: ant beta:sessions connect $SESSION_ID"
