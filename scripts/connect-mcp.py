#!/usr/bin/env python3
"""Connect an OAuth MCP server (vidIQ or Notion) to the morning-content-brief vault.

Signs you in to the service in your browser (OAuth with PKCE), then stores the
resulting access + refresh token as an mcp_oauth credential in the vault, so
Anthropic refreshes it on its own from then on. The tokens go straight from
the service to the vault; nothing is printed or written to disk.

Run from the repo root after `ant apply agents/morning-content-brief/vault.yaml`:
    python3 scripts/connect-mcp.py vidiq
    python3 scripts/connect-mcp.py notion
Re-run it any time a service needs re-authorizing.
"""
import base64
import hashlib
import http.server
import json
import secrets
import subprocess
import sys
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone

PROVIDERS = {
    "vidiq": {
        "name": "vidIQ",
        "mcp_url": "https://mcp.vidiq.com/mcp",
        "authorize": "https://mcp.vidiq.com/mcp/authorize",
        "token": "https://mcp.vidiq.com/mcp/token",
        "register": "https://mcp.vidiq.com/mcp/register",
        "scope": "api",
    },
    "notion": {
        "name": "Notion",
        "mcp_url": "https://mcp.notion.com/mcp",
        "authorize": "https://mcp.notion.com/authorize",
        "token": "https://mcp.notion.com/token",
        "register": "https://mcp.notion.com/register",
        "scope": "default",
    },
}
PORT = 8765
REDIRECT = f"http://127.0.0.1:{PORT}/callback"
LOCK_KEY = "./agents/morning-content-brief/vault.yaml"


def post(url, data, as_json):
    body = json.dumps(data).encode() if as_json else urllib.parse.urlencode(data).encode()
    ctype = "application/json" if as_json else "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": ctype, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def vault_id():
    try:
        with open("claude-lock.json") as f:
            return json.load(f)["resources"][LOCK_KEY]["id"]
    except (OSError, KeyError):
        sys.exit("Vault not in claude-lock.json. Run: ant apply agents/morning-content-brief/vault.yaml")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in PROVIDERS:
        sys.exit("Usage: python3 scripts/connect-mcp.py " + "|".join(PROVIDERS))
    p = PROVIDERS[sys.argv[1]]
    vid = vault_id()

    client = post(p["register"], {
        "client_name": "VNMSFX morning-content-brief",
        "redirect_uris": [REDIRECT],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": p["scope"],
    }, as_json=True)
    client_id = client["client_id"]

    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    url = p["authorize"] + "?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id, "redirect_uri": REDIRECT,
        "scope": p["scope"], "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
    })

    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                result["code"] = q["code"][0]
                msg = p["name"] + " connected. You can close this tab and go back to the terminal."
            else:
                result["error"] = q.get("error", ["state mismatch"])[0]
                msg = p["name"] + " sign-in failed. Check the terminal."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg.encode())

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print("Opening " + p["name"] + " sign-in in your browser...")
    webbrowser.open(url)
    while not result:
        server.handle_request()
    server.server_close()
    if "error" in result:
        sys.exit(f"{p['name']} sign-in failed: {result['error']}")

    tok = post(p["token"], {
        "grant_type": "authorization_code", "code": result["code"], "redirect_uri": REDIRECT,
        "client_id": client_id, "code_verifier": verifier,
    }, as_json=False)
    if "refresh_token" not in tok:
        sys.exit(p["name"] + " returned no refresh token, so the credential could not refresh itself. Nothing was stored.")

    expires = datetime.now(timezone.utc) + timedelta(seconds=int(tok.get("expires_in", 3600)))
    auth = {
        "type": "mcp_oauth",
        "mcp_server_url": p["mcp_url"],
        "access_token": tok["access_token"],
        "expires_at": expires.isoformat(timespec="seconds"),
        "refresh": {
            "token_endpoint": p["token"],
            "client_id": client_id,
            "refresh_token": tok["refresh_token"],
            "scope": p["scope"],
            "token_endpoint_auth": {"type": "none"},
        },
    }
    out = subprocess.run(
        ["ant", "beta:vaults:credentials", "create", "--vault-id", vid,
         "--display-name", p["name"], "--auth", json.dumps(auth), "--transform", "id", "-r"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit("Storing the credential failed:\n" + out.stderr.strip())
    print(f"{p['name']} credential stored in vault {vid}: {out.stdout.strip()}")


if __name__ == "__main__":
    main()
