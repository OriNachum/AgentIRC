---
layout: default
title: Mission Control Dashboard
parent: AgentIRC
nav_order: 98
---

# Mission Control Dashboard

A local web app to **watch the whole mesh and take the wheel**. It streams every
agent's session, the daemon-action log, and pending tool-approvals into one
browser view, and exposes the full intervention surface — approve/deny,
pause/resume, close, emergency stop-all, and grant-policy edits — for when a run
goes sideways.

Design spec: `docs/superpowers/specs/2026-05-29-mission-control-dashboard-design.md`
Builds on the [Permission Broker](helper-permissions.md), [Daemon Action Log](helper-daemon-log.md), and [Boss Agent](boss-agent.md).

## Run it

```bash
culture dashboard               # http://127.0.0.1:8787
culture dashboard --port 9000
```

Bound to `127.0.0.1` only. It can approve tool calls and kill agents, so it
refuses a non-loopback `--host` unless you pass `--unsafe-bind` (documented as
dangerous). No new dependency — it's an `aiohttp` server (already a dep) serving
a vanilla-JS page (no build step).

## What you see

Three columns, no setup beyond a running mesh:

- **Agents** — every registered agent with live state (running/stopped), pending-
  approval count, last daemon action, and a `BOSS` tag for boss agents. Per-agent
  **Pause / Resume / Close** buttons.
- **Session / Daemon actions / Chat** — click an agent, then pick a tab:
  - **Session** — live-stream the agent's own messages + tool calls
    (`audit/<nick>.jsonl`). Server-sent events; backlog then live tail.
  - **Daemon actions** — the structured daemon-action log (`daemon-log/<nick>.jsonl`).
  - **Chat** — **talk to the agent directly.** Shows the recent conversation in
    the agent's channel (both sides) and gives you a message box. What you send is
    posted to the agent's channel prefixed with `@<nick>` so its mention detector
    fires — the same thing `culture boss brief` does, but no boss daemon needed
    (it goes over a transient observer connection). The target is the agent's
    private `#task-*` channel when it has one, else its first configured channel.
- **Pending approvals** — every worker tool request waiting on a human, with
  **Approve / Always / Deny**. (Requests already decided — awaiting their worker
  to consume the verdict — are not shown.)

Top bar: a pending badge, **Pause all**, and a red **STOP ALL** (emergency
kill of every agent including the boss).

## Control = the operator is the top authority

Unlike the boss agent (bounded by its [grant ceiling](boss-agent.md)), the
dashboard is **you** — its approvals are **not** ceiling-bounded. You can approve
any tool, including the high-risk ones a boss must escalate. Control actions reuse
the existing levers:

| Action | Under the hood |
|---|---|
| Approve / Deny | writes `perm-decisions/<id>.json` (`decided_by: dashboard`) |
| Pause / Resume | daemon IPC (`pause`/`resume`) |
| Close | `culture agent stop <nick>` |
| Stop all | `pause` every agent, or `culture agent stop --all` (kill) |
| Edit policy | read/write `perm-policy/<nick>.yaml` |
| Send message | observer PRIVMSG to the agent's channel, nick-prefixed (mention fires) |

## API (for scripting / integration)

`GET /api/agents`, `GET /api/pending`, `GET /api/stream/{audit|daemon-log}/<nick>`
(SSE), `GET /api/channel/<nick>` (recent channel messages), `GET/PUT /api/policy/<nick>`,
and `POST /api/{approve,deny,pause,resume,close,stop-all,message}`.
All localhost JSON. `POST /api/message` takes `{nick, text}` and posts
`@<nick> <text>` to the agent's channel.

## Security model

Same-machine, same-UID, localhost-only. Anyone who can reach the port as this
user already has shell access and the same powers via the CLI/files — the
dashboard adds no privilege. There is no auth token in v1; if the host is shared,
do not run it (or front it with your own auth). Never bind a non-loopback
interface.
