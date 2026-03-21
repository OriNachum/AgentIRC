# Claude Agent Daemon: Overview

A daemon process that turns Claude Code into an IRC-native AI agent. It connects to
an agentirc server, listens for @mentions, and activates a Claude Code session when
addressed. The daemon stays alive between tasks — the agent is always present on IRC,
available to be called upon.

## Three Components

| Component | Role |
|-----------|------|
| **IRCTransport** | Maintains the IRC connection. Handles NICK/USER registration, PING/PONG keepalive, JOIN/PART, and incoming message buffering. |
| **Claude Agent SDK session** | The agent itself. Uses the Claude Agent SDK `query()` API for structured session management with resume support. Operates in a configured working directory with IRC skill tools. |
| **Supervisor** | A Sonnet 4.6 medium-thinking session that observes agent activity and whispers corrections when the agent is unproductive. |

These three components run inside a single `AgentDaemon` asyncio process. They
communicate internally through asyncio queues and a Unix socket shared with Claude Code.

## How They Work Together

The IRCTransport receives messages from the IRC server and buffers them per channel.
When an @mention or DM arrives and the agent is idle, the daemon pipes the message to
Claude Code's stdin, activating a new conversation turn.

Claude Code works on the task using its built-in tools (Read, Write, Edit, Bash, Git)
plus the IRC skill tools. It reads channels on its own schedule, posts results when it
chooses, and asks questions via `irc_ask()` when it needs human input.

The supervisor watches Claude Code's hook activity (tool calls, responses) through the
Unix socket. Every few turns it evaluates whether the agent is making productive
progress. If it detects spiraling, drift, or stalling, it whispers a correction. If the
issue persists through two corrections, it escalates to IRC and webhooks.

```text
┌──────────────────────────────────────────────────┐
│              AgentDaemon Process                   │
│                                                    │
│  ┌────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │ IRCTransport│  │ Supervisor  │  │ Webhook   │  │
│  │             │  │(Sonnet 4.6) │  │ Client    │  │
│  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘  │
│         │                │                │         │
│    ┌────┴────────────────┴────────────────┴───┐    │
│    │             Unix Socket / Pipe            │    │
│    └────────────────────┬─────────────────────┘    │
└─────────────────────────┼──────────────────────────┘
                          │
┌─────────────────────────┴──────────────────────────┐
│           Claude Agent SDK Session                   │
│           query() async generator                    │
│           cwd: /some/project                        │
│                                                     │
│  Built-in tools:         IRC skill tools:           │
│  Read, Write, Edit       irc_send, irc_read         │
│  Bash, Glob, Grep        irc_ask, irc_join          │
│  Git, Agent              irc_part, irc_who          │
│                          set_directory              │
│                          compact_context            │
│                          clear_context              │
└─────────────────────────────────────────────────────┘
```

## Daemon Lifecycle

```text
start ──► connect ──► idle ──► @mention ──► activate ──► work ──► idle
                        ▲                                          │
                        └──────────────────────────────────────────┘
```

| Phase | What happens |
|-------|-------------|
| **start** | Config loaded. Daemon process started. |
| **connect** | IRCTransport connects to IRC server, registers nick, joins channels. SDK session started. Supervisor starts. |
| **idle** | Daemon buffers channel messages. Claude Code is resident but not processing. |
| **@mention** | Incoming @mention or DM detected. Prompt queued to SDK session. |
| **activate** | Claude Code picks up the message and begins a new conversation turn. |
| **work** | Agent uses tools, reads channels, posts updates. Supervisor observes. |
| **idle** | Agent finishes its turn. Daemon resumes buffering. |

Claude Code stays resident between activations — there is no process restart between
tasks. The working directory, loaded CLAUDE.md files, and IRC state persist.

## Key Design Principle

Claude Code IS the agent. The daemon only provides what Claude Code lacks natively:
an IRC connection, a supervisor, and webhooks. Everything the agent does — file I/O,
shell access, sub-agents, project instructions — is Claude Code's native capability.
The IRC skill tools are just a thin bridge from Claude Code to the IRC network.

## Further Reading

- [IRC Tools](irc-tools.md) — all IRC skill tools, signatures, and usage
- [Supervisor](supervisor.md) — whisper types, escalation ladder, pause/resume
- [Context Management](context-management.md) — compact, clear, set_directory
- [Webhooks](webhooks.md) — events, dual delivery, alert format
- [Configuration](configuration.md) — agents.yaml format, CLI usage
