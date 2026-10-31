#!/usr/bin/env bash
# Print the latest morning-content-brief run's status and the agent's final message
# (which carries the "Pick one" section of the brief).
# Run from the repo root.
set -euo pipefail

LOCK="claude-lock.json"
KEY='./agents/morning-content-brief/deployment-weekday.yaml'

DEPLOYMENT_ID=$(jq -r --arg k "$KEY" '.resources[$k].id // empty' "$LOCK")
if [ -z "$DEPLOYMENT_ID" ]; then
  echo "Deployment not in claude-lock.json. See agents/morning-content-brief/README.md." >&2
  exit 1
fi

RUN_JSON=$(ant beta:deployment-runs list --deployment-id "$DEPLOYMENT_ID" --max-items 1 --format json)
SESSION_ID=$(printf '%s' "$RUN_JSON" | jq -r '.[0].session_id // empty')
ERROR_TYPE=$(printf '%s' "$RUN_JSON" | jq -r '.[0].error.type // empty')

if [ -n "$ERROR_TYPE" ]; then
  echo "Latest run failed to start: $ERROR_TYPE"
  printf '%s' "$RUN_JSON" | jq -r '.[0].error.message // empty'
  exit 1
fi

echo "Session: $SESSION_ID"
ant beta:sessions retrieve --session-id "$SESSION_ID" --transform '{status,stop_reason,usage:usage.list_cost}' --format yaml
echo
echo "--- latest agent message ---"
# agent.message events carry the text in content[].text; take the last one.
ant beta:sessions:events list --session-id "$SESSION_ID" --format json \
  | jq -r '[.[] | select(.type=="agent.message")] | last | .content[]? | select(.type=="text") | .text'
