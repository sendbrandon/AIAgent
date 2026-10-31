# Morning content brief

A scheduled Claude Managed Agent that runs every weekday at 6:00 AM US Eastern, researches what is moving in short-form comedy and creator video, and writes a brief with 3 to 5 production-ready VNMSFX skit concepts. You open it, pick one, kill the rest.

It runs on the monthly Claude Platform API credits that come with the Max plan. It does not touch Claude Code or chat usage limits.

## What is in this directory

| File | What it is |
|---|---|
| `agent.md` | The agent: model, tools, system prompt (the Markdown body). |
| `skills/vnmsfx-skit-pipeline/SKILL.md` | The house method the agent follows. Replace or extend with your fuller skills at any time. |
| `environment.yaml` | The sandbox the agent runs in. |
| `deployment-weekday.yaml` | The schedule, the per-run budget cap, and the outcome rubric the grader scores each run against. |

`ant apply` turns these files into resources on Anthropic's side and records their IDs in `claude-lock.json` at the repo root. Commit that file alongside any change here, or the next apply creates duplicates.

## First-time setup (your terminal, about 10 minutes)

**1. Install the Anthropic CLI** (needs 1.34.0 or later).

```sh
brew install anthropics/tap/ant        # macOS
ant --version
```

Linux and other installs: https://github.com/anthropics/anthropic-cli/releases

**2. Sign in.** This opens a browser and binds the CLI to your org and workspace. Your Max plan API credits are spent from whichever workspace you pick here.

```sh
ant auth login
ant auth status      # confirm the org and workspace you expect
```

**3. Preview, then apply.** Run from the repo root.

```sh
ant apply --dry-run -v agents/morning-content-brief/agent.md agents/morning-content-brief/environment.yaml
ant apply agents/morning-content-brief/agent.md agents/morning-content-brief/environment.yaml
```

Then the deployment. A deployment is live the moment it exists, so apply and pause in one command, test manually, and unpause only once a run looks right.

```sh
ant apply agents/morning-content-brief/deployment-weekday.yaml &&
  DEPLOYMENT_ID=$(jq -r '.resources["./agents/morning-content-brief/deployment-weekday.yaml"].id' claude-lock.json) &&
  ant beta:deployments pause --deployment-id "$DEPLOYMENT_ID"
```

**4. Run it once by hand.**

```sh
./scripts/brief-run-now.sh          # starts a session now, prints its ID and Console URL
./scripts/brief-latest.sh           # shows the latest run's final message (the "Pick one" list)
```

Or watch it live: `ant beta:sessions connect <session-id>`.

**5. Turn the schedule on.**

```sh
ant beta:deployments unpause --deployment-id "$DEPLOYMENT_ID"
```

**6. Commit `claude-lock.json`.**

## Where the brief lands

Each run writes `/mnt/session/outputs/brief-YYYY-MM-DD.md` inside its session and pastes the "Pick one" section as its final message. The Console session page shows both. The outputs file can be listed and downloaded with `ant beta:files list` scoped to the session (see `ant beta:files list --help` for the scope flag).

## Changing it

- **Schedule or timezone:** edit `deployment-weekday.yaml`, run `ant apply agents/morning-content-brief/deployment-weekday.yaml`.
- **Taste, format, rules:** edit `agent.md` or the skill, run `ant apply agents/morning-content-brief/agent.md`. Each apply creates a new agent version; the deployment moves to it.
- **Swap in your real skills:** copy your `narrative-tension-engine`, `cut-dialogue`, `physical-comedy-pass`, `shot-list-architect`, `sound-off-test` and `storyboard-standard` SKILL.md files into `skills/<name>/SKILL.md` beside the pipeline skill, list them under `skills:` in `agent.md`, and apply. The agent will load them by description.
- **Rubric:** the grader iterates the agent against it up to `max_iterations` times. If runs over-iterate on criteria you do not care about, loosen them; if briefs come back sloppy, tighten.
- **Cost:** `budget.max_list_cost.amount` is cents per run. A run that hits it pauses with `budget_reached`; raise the cap and the paused run resumes.

## Phase 2: writing into your tools

Version 1 deliberately has no credentials, so it can run today. When the briefs are worth keeping, the natural next step is to have the agent file them into Notion and queue caption drafts into Blotato instead of leaving them in session outputs.

That needs: an MCP server entry under `mcp_servers:` in `agent.md` for each service, an `mcp_toolset` entry under `tools:` enabling only the tools the agent should call, a `vault.yaml` (`type: vault`) beside this file, the credential added with `ant beta:vaults:credentials create`, the vault ID written into `vault_ids:` on the deployment, and `environment.yaml` switched to `limited` networking with the services' hosts in `allowed_hosts` and `allow_mcp_servers: true`.

Get each MCP server's URL and auth instructions from the vendor's own docs. Notion's hosted MCP server is `https://mcp.notion.com/mcp` and needs an OAuth token, not an integration key. Confirm vidiq's and Blotato's from their documentation before adding them.

## Kill criterion

Four weeks. If the brief is not saving you two or more hours a week, or you stop opening it, pause the deployment and point the agent at a different recurring task. The credits renew monthly.
