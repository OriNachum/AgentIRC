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
  **Pause / Resume / Close** buttons. Agents are **grouped into teams**: each boss
  heads its own group with its workers nested beneath it, and standalone agents
  fall under "unassigned" — so a boss and its team read as one unit. A running
  worker that has produced **no activity** (empty audit — spawned but never
  engaged) gets a loud **`IDLE`** badge, so a worker that's doing nothing outs
  itself regardless of what its boss reports.
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
| Close | `culture agent stop <nick>` (dashboard runs as the human/root — may close any agent) |
| Stop all | `pause` every agent, or `culture agent stop --all` (kill) |
| Edit policy | read/write `perm-policy/<nick>.yaml` |
| Send message | observer PRIVMSG to the agent's channel, nick-prefixed (mention fires) |

## API (for scripting / integration)

`GET /api/agents`, `GET /api/pending`, `GET /api/stream/{audit|daemon-log}/<nick>`
(SSE), `GET /api/channel/<nick>` (recent channel messages), `GET/PUT /api/policy/<nick>`,
and `POST /api/{approve,deny,pause,resume,close,stop-all,message}`.
All localhost JSON. `POST /api/message` takes `{nick, text}` and posts
`@<nick> <text>` to the agent's channel.

## Remote access (mobile / another machine)

The dashboard is a control plane (it can approve tool calls, kill agents, and
message agents that hold your MCP credentials), so it is **localhost-only by
default** and its guard rejects non-loopback `Host`/`Origin`. To reach it
remotely, do **not** flip `--unsafe-bind` — instead keep the bind on loopback and
front it with a **private tunnel + a token**:

```bash
# 1. Run with auth (token auto-generated at ~/.culture/dashboard-token) and
#    trust your tunnel's hostname:
culture dashboard --auth --trusted-host mymac.tailXXXX.ts.net

# 2. Publish the loopback dashboard onto your private network (example: Tailscale):
tailscale serve --bg 8787
```

On start, `--auth` prints a one-time bootstrap URL
(`https://<trusted-host>/?token=…`). Open it once per device: the server sets a
`SameSite=Strict`, HttpOnly cookie, so every later request (including the SSE
streams) is authenticated. Requests without a valid cookie get `401`; a `Host`/
`Origin` that is neither loopback nor a `--trusted-host` gets `403`.

Why this is the safe shape:

- **Tailscale** (or any private tunnel) keeps the dashboard off the public
  internet — only your own devices can route to it.
- The **token cookie** means even a leaked URL or a compromised device on the
  tailnet can't drive the control plane without the secret.
- `SameSite=Strict` + the Origin allow-list keep CSRF / DNS-rebinding defenses
  intact.

`--auth-token <tok>` sets an explicit token instead of the generated one;
`--trusted-host` is repeatable.

## Security model

Same-machine, same-UID, localhost-only **unless** you opt into the remote-access
setup above. Anyone who can reach the port as this user already has shell access
and the same powers via the CLI/files — the dashboard adds no privilege locally.
Without `--auth` there is no token (fine for pure localhost); never bind a
non-loopback interface directly — use a private tunnel + `--auth` instead.
