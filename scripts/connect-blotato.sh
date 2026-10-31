#!/bin/zsh
# Store your Blotato API key in the morning-content-brief vault as a bearer
# credential for https://mcp.blotato.com/mcp. The key is read hidden, sent
# straight to the vault, and never printed or written to disk.
# Get the key from Blotato: Settings > API. Run from the repo root:
#   ./scripts/connect-blotato.sh
set -euo pipefail

VAULT_ID=$(jq -r '.resources["./agents/morning-content-brief/vault.yaml"].id // empty' claude-lock.json)
if [[ -z "$VAULT_ID" ]]; then
  echo "Vault not in claude-lock.json. Run: ant apply agents/morning-content-brief/vault.yaml" >&2
  exit 1
fi

read -rs "key?Paste your Blotato API key, then press Enter: "
echo
if [[ -z "$key" ]]; then echo "No key entered. Nothing stored."; exit 1; fi

auth=$(jq -nc --arg t "$key" '{type: "static_bearer", mcp_server_url: "https://mcp.blotato.com/mcp", token: $t}')
unset key
id=$(ant beta:vaults:credentials create --vault-id "$VAULT_ID" --display-name Blotato --auth "$auth" --transform id -r)
unset auth
echo "Blotato credential stored in vault $VAULT_ID: $id"
