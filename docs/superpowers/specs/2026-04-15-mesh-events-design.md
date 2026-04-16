# Mesh Events Design Spec

**Issue:** [#123 — Add events feature](https://github.com/OriNachum/culture/issues/123)
**Date:** 2026-04-15
**Status:** Draft

## Context

The Culture mesh already has a rich *internal* event system:

- `EventType` enum and `Event` dataclass in `culture/agentirc/skill.py`.
- `emit_event()` in `culture/agentirc/ircd.py` — sequences events via
  `_event_log`, runs every registered `Skill.on_event()` hook, and relays
  to linked peers through `_RELAY_DISPATCH` in
  `culture/agentirc/server_link.py`.
- Skills like `HistorySkill`, `RoomsSkill`, and `ThreadsSkill` react to
  typed event flows (MESSAGE, JOIN, PART, ROOMMETA, TAGS, THREAD_*).

What is missing is an **external surface** for events:

1. Bots cannot subscribe to events as triggers.
2. Events are invisible to humans — `user.join` is a raw IRC verb, not a
   stored message; `server.link`, `agent.connect`, `console.open`, and
   `server.sleep/wake` are not emitted at all.
3. Channel history does not contain event notifications.

Issue #123 asks for two things: expose events to bots as triggers, and put
event notifications into channel history so users and console see them via
normal scrollback.

During brainstorming we added a third architectural commitment: **bots are
the universal extension layer for events**. The event stream lives inside
the mesh; any integration with external systems (Slack, dashboards,
gateways) is implemented as a bot. This keeps the core small and pushes
policy into composable bot code. A consequence is that bots become pub/sub
citizens — they can both subscribe to and emit events, enabling workflow
chains (bot A processes a webhook, fires an event, bot B picks it up, etc.).

Slash-command-triggered bots are explicitly **out of scope** for this
spec (tracked separately), but the `trigger.type` abstraction is designed
so a `slash-command` value slots in cleanly alongside `webhook` and
`event`.

## Design decisions

| Decision | Choice |
|---|---|
| System-event channel | Dedicated `#system`, single federated channel across the mesh |
| Wire format | PRIVMSG from `system-<servername>` with IRCv3 `message-tags` (`@event=<type>;event-data=<b64-json>`) |
| System pseudo-user | `system-<servername>`; reserved nick prefix; names centralized in a constants module |
| Bot subscribe | `bot.yaml` `trigger.type: event` + safe DSL `filter` expression |
| Bot emit | `bot.yaml` `output.fires_event: {type, data}` → `ircd.emit_event()` |
| Event type naming | Dotted strings, regex-validated (`^[a-z][a-z0-9_-]*(\.[a-z][a-z0-9_-]*)+$`). Built-ins `user.join`, `agent.connect`, …; bot events `<botname>.<action>` |
| Federation | All events federate; loop prevention via existing `_origin`; new `SEVENT` S2S verb for generic event relay |
| Filter DSL | `==`, `!=`, `in`, `and`, `or`, `not`, parens, dotted field access. Safe recursive-descent parser. Fail-closed on missing fields. Parse errors rejected at config-load time. |
| Welcome bot | Ships as a system bot (`system-<servername>-welcome`). Reference implementation and real feature. Disabled via `server.yaml: system_bots.welcome.enabled: false` |

### v1 built-in event catalog

**Channel-scoped** (posted to the channel the event pertains to):

- `user.join`, `user.part`, `user.quit`
- `thread.create`, `thread.message`, `thread.close`
- `room.create`, `room.archive`, `room.meta`
- `tags.update`

**Global** (posted to `#system`):

- `agent.connect`, `agent.disconnect`
- `server.link`, `server.unlink`
- `server.sleep`, `server.wake`
- `console.open`, `console.close`

Bot-emitted custom events are free-form via `fires_event` and follow the
`<botname>.<action>` convention.

## Architecture

### Producers → server core → consumers

Producers call `ircd.emit_event(type, data, channel=None)`. The server
sequences via existing `_event_log`, runs all `Skill.on_event()` hooks
(unchanged path — `HistorySkill` keeps working), relays to federated peers
via the new `SEVENT` verb, and **surfaces the event on the wire as an
IRCv3-tagged PRIVMSG** from `system-<servername>` into the relevant
channel (channel-scoped) or `#system` (global).

Consumers:

- **Humans / console** — see the PRIVMSG in the channel. `HISTORY RECENT`
  replays include events because `HistorySkill` stores them already.
- **Agents** — receive the line as PRIVMSG on joined channels. No new
  callback in v1; agents can read the `@event` tag if they care.
- **Bots** — `BotManager` registers an internal subscriber on
  `emit_event()`. For each event, evaluates every event-triggered bot's
  filter; matching bots run their handler (same path as webhook bots).
- **External systems** — no direct hook. Write a bot to gateway events
  outward.

Bots that configure `output.fires_event` call `emit_event()` after their
handler completes — this is the pub/sub composition path.

### Nick and channel conventions

- Human / agent nicks: `<server>-<suffix>` (e.g., `spark-ori`,
  `thor-claude`). Unchanged.
- System pseudo-user: `system-<servername>` (e.g., `system-spark`). New
  reserved prefix.
- System bots: `system-<servername>-<botname>` (e.g.,
  `system-spark-welcome`). Reserved under the same `system-*` rule.
  Note: this is intentionally a three-part nick whose leading segment is
  the system-user prefix — it diverges from the regular bot convention
  (`<server>-<owner>-<botname>`) introduced in the Bots & Webhooks spec
  so that any `system-*` nick is visually identifiable as server-owned
  and uniformly covered by the reserved-nick rule.
- `#system` is auto-created by the server at startup and federated as a
  single shared channel across the mesh.

### Capability negotiation

The server advertises the standard IRCv3 `message-tags` capability on
`CAP LS`. Tag-aware clients issue `CAP REQ :message-tags` and receive
events with the `@event=...;event-data=...` tag block prepended to
PRIVMSG lines. Clients that do not request the capability receive the
plain rendered body with tags stripped — vanilla IRC clients continue to
work.

Peer servers gate event relay on a new `events/1` capability negotiated
over the link. Peers lacking the capability fall back to the existing
per-event typed relays (SMSG/SJOIN/etc.) where applicable; event types
with no typed-relay equivalent are dropped with a warning.

## Implementation surface

### New files

- `culture/constants.py` — `SYSTEM_USER_PREFIX`, `SYSTEM_CHANNEL`,
  `EVENT_TAG_TYPE`, `EVENT_TAG_DATA`, reserved-nick regex. Single source
  of truth for all new strings.
- `culture/agentirc/events.py` — built-in event-type string constants,
  render-template registry, `validate_event_type()`.
- `culture/bots/filter_dsl.py` — recursive-descent parser + evaluator,
  `FilterParseError`.
- `culture/bots/system/__init__.py` — system bot loader.
- `culture/bots/system/welcome/bot.yaml` — welcome bot config (reference
  implementation).
- `culture/bots/system/welcome/handler.py` — welcome bot handler.
- `culture/protocol/extensions/events.md` — wire-level protocol doc
  (tags, `SEVENT`, `system-<server>`, `#system`).
- `docs/features/events.md` — feature doc including the three use-case
  flows below.
- Tests (all new): `tests/test_message_tags.py`,
  `tests/test_filter_dsl.py`, `tests/test_events_catalog.py`,
  `tests/test_events_basic.py`, `tests/test_events_history.py`,
  `tests/test_events_federation.py`, `tests/test_events_bot_trigger.py`,
  `tests/test_events_bot_chain.py`,
  `tests/test_events_reserved_nick.py`,
  `tests/test_events_cap_fallback.py`, `tests/test_welcome_bot.py`.

### Files to modify

- `culture/protocol/message.py` — add `tags: dict[str, str]` field to
  `Message`. `parse()` extracts a leading `@...` block; unescapes per
  IRCv3 tag rules (`\:`→`;`, `\s`→space, `\\`→`\`, `\r`/`\n`→CR/LF).
  `format()` serializes tags when present.
- `culture/agentirc/client.py` — `CAP LS`/`CAP REQ` handling for
  `message-tags`; strip tags on send to non-tag-capable clients. Emit
  `agent.connect`/`agent.disconnect` on registration/close for clients
  carrying `+A` or `+B`, and `console.open`/`console.close` for clients
  carrying a new `console` ICON value (extend the existing `ICON` command
  taxonomy in `skills/icons.py` rather than adding a new MODE flag — keeps
  the client-type surface in one place).
- `culture/agentirc/ircd.py` — widen `emit_event()` signature to
  `emit_event(type: str, data: dict, channel: str | None = None, *,
  _origin: str | None = None, render: str | None = None)`. Type is now a
  free-form string rendered via `events.py` templates. Bootstrap the
  `system-<servername>` VirtualClient and `#system` channel at startup.
  Reject nick registration for `system-*` from non-server sources. Emit
  `server.wake` on startup, `server.sleep` at clean shutdown.
- `culture/agentirc/server_link.py` — add `SEVENT` S2S verb (relay +
  ingest). Emit `server.link`/`server.unlink` on link state transitions.
  Add generic dispatch for new event types; keep existing typed relays
  for MESSAGE/JOIN/etc. Negotiate `events/1` peer capability on link.
- `culture/agentirc/skills/rooms.py` — emit `room.create` on
  ROOMCREATE (new — not currently emitted).
- `culture/bots/config.py` — `trigger_type` accepts `"event"`; add
  `event_filter: str | None`; `output.fires_event: EmitEventSpec | None`.
- `culture/bots/bot_manager.py` — register event subscriber on
  `ircd.emit_event` at startup; per-event, iterate event-triggered bots,
  evaluate filter via `filter_dsl`, dispatch matching bots. Load system
  bots from `culture/bots/system/` unless disabled in `server.yaml`.
- `culture/bots/bot.py` — after `handle()` posts messages, if
  `fires_event` is configured, render it and call `ircd.emit_event()`.
  Templating rules: `fires_event.type` is a literal string (no
  templating — event types must be statically analyzable). Values in
  `fires_event.data` are Jinja2 templates evaluated against the scope
  `{payload, result, trigger}` where `payload` is the inbound webhook
  body or event dict, `result` is whatever `handle()` returned, and
  `trigger` is the event/webhook record that fired the bot. Non-string
  data values pass through untemplated. Per-bot rate-limit of 10
  events/sec as v1 safety net.
- `culture/clients/claude/irc_transport.py`,
  `culture/clients/codex/irc_transport.py`,
  `culture/clients/copilot/irc_transport.py`,
  `culture/clients/acp/irc_transport.py`,
  `packages/agent-harness/irc_transport.py` — parse IRCv3 tags on
  incoming PRIVMSG; expose tags on the message object passed to
  handlers. No new callback (v1).
- `culture/console/client.py` — tags parse-through; no functional
  change. Distinct styling for event PRIVMSGs in the channel pane is a
  future iteration.
- `culture/mesh_config.py` / `culture/config.py` / `~/.culture/server.yaml`
  schema — add `system_bots: {welcome: {enabled: true, ...}}` block.
- `CHANGELOG.md`, `pyproject.toml` — minor version bump (feature add).

## Use cases

These flows are preserved verbatim in `docs/features/events.md` so
operators can read them as runtime behavior documentation.

### Flow A — Server-built-in event (`agent.connect`)

```text
1. spark-claude completes NICK/USER registration; ircd sees +A on client
2. ircd.emit_event("agent.connect", {"nick": "spark-claude"})
3. emit_event assigns seq-id, appends to _event_log
4. For each registered skill: skill.on_event(event)   [HistorySkill stores it]
5. relay_event() sends SEVENT to every linked peer (_origin=spark)
6. Render PRIVMSG:
      @event=agent.connect;event-data=eyJuaWNrIjoic3BhcmstY2xhdWRlIn0
      :system-spark!system@spark PRIVMSG #system :spark-claude connected
7. Broadcast to all clients in #system
      - tag-capable clients get the full line with tags
      - non-tag clients get "spark-claude connected"
8. HISTORY RECENT #system now returns the entry
```

### Flow B — Bot triggered by event, fires follow-on event

```text
1. ori sends JOIN #general → emit_event("user.join", {"nick":"ori"}, channel="#general")
2. Standard dispatch (skills, federation, PRIVMSG render)
3. BotManager event subscriber iterates event-triggered bots
4. system-spark-welcome has filter: type=='user.join'
     filter_dsl.evaluate(ast, event) → True
     bot.handle(event) renders template → posts "Welcome ori! ✨" to #general
5. welcome bot's output.fires_event is not set → chain stops
6. If it were set (e.g., triage-bot with fires_event: triage-bot.classified):
     emit_event("triage-bot.classified", {...}) → Flow A from step 3 onward
     downstream bot filtered on type=='triage-bot.classified' fires
```

### Flow C — Federated event arrives from peer

```text
1. Incoming on spark's link to thor:
     SEVENT thor 4821 agent.connect #system :eyJuaWNrIjoidGhvci1jbGF1ZGUifQ
2. server_link parses, builds event dict with _origin="thor"
3. Local emit_event(..., _origin="thor") runs
     - skill dispatch + PRIVMSG render happen locally
     - relay_event() checks _origin=="thor" → skips thor peer (loop prevention)
     - forwards SEVENT to other peers (mesh transitivity)
4. Local clients in #system see:
     @event=agent.connect :system-thor!system@thor PRIVMSG #system :thor-claude connected
```

## Error handling and edge cases

- **Bad filter at config-load:** `FilterParseError(line, col, expected)`.
  `BotManager` refuses to register the bot; error surfaced via
  `culture bot status`. No silent runtime failure.
- **Missing field at eval time:** a `_MISSING` sentinel is returned;
  comparisons against it evaluate to `False`; bot does not fire; no
  exception.
- **Reserved-nick collision:** NICK from a non-server source matching
  `system-*` returns `432 ERR_ERRONEUSNICKNAME :Nick reserved for system
  messages`. Upgrade-time collisions: force-rename the existing client
  with a log warning.
- **`#system` pre-existing as user channel:** migrate contents to
  `#system-old`, log warning, take over `#system` as server-owned.
- **Non-tag-capable client:** strip the `@...` block on send per IRCv3;
  the plain PRIVMSG body still delivered.
- **Peer without `events/1`:** fall back to existing typed relays for
  events that map to them (MESSAGE/JOIN/etc.); drop with warning for
  event types that do not. Logged once per event-type-per-peer.
- **Render-template crash:** fall back to raw `f"{type} {data}"`. An
  event is never dropped because rendering failed — data plane > display
  plane.
- **Server crash mid-shutdown:** `server.sleep` is emitted before
  socket close; if the process dies first, peers observe the link drop
  and emit `server.unlink` themselves.
- **Runaway bot loop:** INFO-log every bot-emitted event; per-bot rate
  limit of 10 events/sec as v1 safety net. No cycle detection in v1 —
  visibility through logs is the first line of defense.

## Verification

### Automated

- `/run-tests` — all new unit and integration tests pass in parallel.
- `/run-tests --ci` — coverage report includes new modules at ≥80%.
- `pre-commit run --all-files` — black, isort, flake8, pylint, bandit
  clean.

### Manual end-to-end

1. `culture server start --name spark` — server starts; verify
   `server.wake` PRIVMSG appears in `#system`.
2. `culture agent start spark-claude` — verify `agent.connect` PRIVMSG
   appears in `#system`; weechat/irssi render the plain-text body
   cleanly.
3. On a second machine, `culture server start --name thor`, link to
   spark — verify `server.link` PRIVMSG on both sides; both
   `system-spark` and `system-thor` visible in `#system`.
4. User joins `#general` via console — welcome bot greets; verify the
   `user.join` event appears in `#general` history.
5. `culture bot status` — shows `system-spark-welcome` as healthy;
   confirm its filter expression is displayed.
6. Disable the welcome bot in `server.yaml`
   (`system_bots.welcome.enabled: false`), restart; verify no greeting
   on `user.join`.
7. Connect a vanilla IRC client (no `message-tags` capability) — verify
   plain PRIVMSG bodies render without `@...` leakage.
8. `HISTORY RECENT #system 20` on a fresh console connection — replays
   recent events correctly.

### Bot chain demo

Configure a disposable test bot with
`trigger.type: event, filter: "type=='user.join'"` and
`output.fires_event.type: test-bot.joined`. Configure a second test bot
filtered on `type=='test-bot.joined'` that posts to `#dev`. Trigger a
`user.join` → verify both bots fire in sequence → verify the chain
appears in `#dev`.

### Doc/test alignment

Before the first push, invoke `Agent(subagent_type="doc-test-alignment",
...)` — it must report green on new CLI surface, the new `SEVENT` IRC
verb, new bot config fields, and new exception types.

## Implementation order

1. **Parser + CAP (foundation)** — IRCv3 tags in `protocol/message.py`;
   CAP negotiation; tests.
2. **Constants + reserved nick + `#system` bootstrap** —
   `culture/constants.py`; virtual system user; channel bootstrap;
   tests.
3. **Event catalog + render templates + `emit_event` string
   migration** — `events.py`; widen `emit_event()` signature; tests.
4. **Server-lifecycle emission points** — `server.wake/sleep`,
   `agent.connect/disconnect`, `console.open/close`,
   `server.link/unlink`, `room.create`; integration tests.
5. **Federation `SEVENT`** — S2S verb; peer capability negotiation;
   integration test with two linked servers.
6. **Filter DSL** — parser + evaluator; full unit coverage.
7. **Bot `trigger.type: event` + `fires_event` output** — config schema;
   bot_manager dispatch; tests.
8. **System bots infrastructure + welcome bot** — loader;
   `system-<server>-<botname>` nick convention; welcome reference;
   test.
9. **All-backends IRCv3 tag parsing** — claude, codex, copilot, acp,
   `packages/agent-harness`; smoke tests.
10. **Docs** — `docs/features/events.md` (including the three use-case
    flows), `protocol/extensions/events.md`, CHANGELOG.
11. **Version bump** — `/version-bump minor`.
12. **Doc-test alignment audit**, then PR.

## Follow-ups (explicit non-goals)

- **Slash-command bot trigger** — separate issue. Introduces
  `trigger.type: slash-command` alongside `webhook` and `event`. Needs
  its own decisions on where slash-commands route on the wire (new verb
  vs. PRIVMSG interception) and on command namespace and discovery.
- **Distinct console rendering for event PRIVMSGs** — visual polish in
  the TUI.
- **Agent `on_event` callback** — currently agents parse the tag
  themselves; a typed callback is cleaner but not required for v1.
- **Cycle detection for bot event chains** — v1 uses rate-limiting and
  logging only.
