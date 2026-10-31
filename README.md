# AIAgent

Claude Managed Agents for VNMSFX, defined as files and synced with `ant apply`.

| Agent | What it does | Runs |
|---|---|---|
| [`agents/morning-content-brief`](agents/morning-content-brief/README.md) | Overnight writers' room: researches what is moving in short-form comedy and drafts 3 to 5 production-ready skit concepts into a morning brief. | Weekdays 06:00 US Eastern |

## Layout

```
agents/<agent-name>/
  agent.md               # agent config (frontmatter) + system prompt (body)
  environment.yaml       # the sandbox
  deployment-*.yaml      # schedule, budget, kickoff / rubric
  skills/<skill>/SKILL.md
  README.md              # setup and operating notes for that agent
scripts/                 # helpers for triggering and reading runs
claude-lock.json         # written by `ant apply`; commit it
```

## Quick start

```sh
brew install anthropics/tap/ant && ant auth login
ant apply --dry-run -v agents/morning-content-brief/agent.md agents/morning-content-brief/environment.yaml
```

Then follow the agent's README for the deployment, a manual test run, and turning the schedule on.
