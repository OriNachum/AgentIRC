# OTEL Audit JSONL Sink Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the third observability pillar — a durable, file-based JSONL audit log capturing every event the server emits, independent of the OTEL collector. Admin-only "who said what to whom, when" trail.

**Architecture:** New `culture/telemetry/audit.py` with an `AuditSink` (bounded asyncio.Queue + dedicated writer task + file rotation). `IRCd.__init__` constructs the sink via `init_audit(config, metrics)`; `IRCd.start()`/`stop()` own the writer-task lifecycle. `IRCd.emit_event` calls `audit.submit(record)` after the existing span/metrics work. Records follow the schema in `culture/protocol/extensions/audit.md` (a stable contract). Two new metrics extend the Plan-3 `MetricsRegistry`: `culture.audit.writes{outcome}` and `culture.audit.queue_depth`.

**Tech Stack:** Python stdlib `asyncio` + `os.write` for atomic appends; no new dependencies. Reuses Plan-3's `MetricsRegistry` extension pattern.

---

## Context

Plans 1–3 shipped the **traces** and **metrics** pillars of OTEL. Plan 4 adds the **audit JSONL sink** — a separate, durable, file-based "who said what to whom, when" trail. Audit is the spec's third observability question (`docs/superpowers/specs/2026-04-24-otel-observability-design.md` §Context line 5):

- **Trace context** (Plans 1–2) → "where did a flow stall?"
- **Metrics** (Plan 3) → "is the mesh healthy?"
- **Audit log** (Plan 4) → "who said what, when, via what path?"

Audit is independent of the OTEL collector — JSONL on local disk, never depends on a running `otelcol-contrib`. After this ships, an admin can `tail ~/.culture/audit/<server>-YYYY-MM-DD.jsonl | jq` and replay every event the server has emitted, including federated ones.

The OTEL Logs export of audit records (spec line 192, "best-effort duplicate") is **deferred** to a future task — Plan 4 is JSONL-only. JSONL is source of truth either way; OTEL log dual-export is a nice-to-have we can layer on once the audit format is stable.

## Critical files to read before implementing

- `docs/superpowers/specs/2026-04-24-otel-observability-design.md:147-192` — audit metrics + audit log section (record schema, durability, rotation, retention).
- `docs/superpowers/plans/2026-04-26-otel-metrics.md` — Plan 3 reference for the `MetricsRegistry` extension pattern, `init_metrics` shape, fixture pattern.
- `culture/telemetry/metrics.py` — pattern to mirror (idempotency snapshot, no-op when disabled, extension comment on `MetricsRegistry`).
- `culture/agentirc/ircd.py:217-241` — `emit_event` (the single audit submit site).
- `culture/agentirc/client.py:127-160` — `_process_buffer` (the PARSE_ERROR submit site; already has parse-exception compensation as a span event).
- `culture/agentirc/skill.py:14-44` — `Event`/`EventType` definitions.
- `culture/agentirc/config.py` — `TelemetryConfig` (extend with audit fields).
- `culture/protocol/extensions/` — siblings (`tracing.md`, `events.md`, etc.) for tone/format of the new `audit.md`.

## Approach

### 1. Config — extend `TelemetryConfig`

Add to `culture/agentirc/config.py::TelemetryConfig`:

```python
audit_enabled: bool = True  # independent of `enabled` — audit fires even with telemetry off
audit_dir: str = "~/.culture/audit"
audit_max_file_bytes: int = 256 * 1024 * 1024  # 256 MiB
audit_rotate_utc_midnight: bool = True
audit_queue_depth: int = 10000
```

Critically: `audit_enabled` is **not** gated by the parent `enabled`. Audit is the spec's "always-on" property — even with `telemetry.enabled=False`, the JSONL still writes. Default `True` so freshly-installed servers get audit out of the box.

### 2. Protocol extension — `culture/protocol/extensions/audit.md`

New page documenting the JSONL record schema as a stable contract. Sections:

- **File layout**: `~/.culture/audit/<server>-YYYY-MM-DD.jsonl` (UTC date), `0600` file mode, `0700` directory mode, optional rotation suffix `.<n>` when same-day size cap hits twice.
- **Record schema** verbatim from spec line 172-185 with field descriptions.
- **Rotation**: daily on UTC midnight + 256 MiB whichever first.
- **Durability**: bounded queue, async writer, drop-on-overflow with stderr warning.
- **Retention**: not auto-pruned in v1 (TODO: future `audit-prune` CLI).
- **Compat**: additive; record-level fields can be added in future versions; downstream consumers must tolerate unknown keys.

### 3. New module `culture/telemetry/audit.py`

```python
@dataclass
class AuditSink:
    """Bounded async queue + dedicated writer task + JSONL file rotation."""
    config: ServerConfig
    metrics: MetricsRegistry
    enabled: bool
    queue: asyncio.Queue[dict] | None = None
    writer_task: asyncio.Task | None = None
    current_path: Path | None = None
    current_size: int = 0
    current_date: date | None = None

    def submit(self, record: dict) -> None:
        """Non-blocking enqueue. On overflow, drop + count error."""
        ...

    async def start(self) -> None:
        """Spawn writer task; ensure dir 0700; open current file."""
        ...

    async def shutdown(self, *, drain_timeout: float = 5.0) -> None:
        """Drain queue (bounded by timeout) then cancel writer task."""
        ...

    async def _writer_loop(self) -> None:
        """json.dumps each record, _maybe_rotate, os.write append."""
        ...

    def _maybe_rotate(self, next_record_bytes: int) -> None:
        """Date roll or size cap → open new file with .N suffix."""
        ...


def init_audit(config: ServerConfig, metrics: MetricsRegistry) -> AuditSink:
    """Idempotent. When disabled, sink.submit() is no-op."""
    ...


def reset_for_tests() -> None:
    ...
```

Key implementation details:

- Writer uses `os.open(path, O_WRONLY|O_APPEND|O_CREAT, 0o600)` + `os.write` per record for atomic appends.
- Directory is created with `mkdir(parents=True, exist_ok=True, mode=0o700)`.
- `_maybe_rotate` is sync (no awaits inside the writer loop's hot path).
- `~` in `audit_dir` expanded via `Path(...).expanduser()`.
- No fsync per record (too slow per spec).

### 4. Extend `MetricsRegistry` — Plan 3 carry-forward

Add to `culture/telemetry/metrics.py::MetricsRegistry` and `_build_registry`:

```python
audit_writes: Counter
audit_queue_depth: UpDownCounter
```

Names per spec: `culture.audit.writes` (labels: `outcome=ok|error`) and `culture.audit.queue_depth`.

### 5. Wire `init_audit` into `IRCd` lifecycle

```python
# IRCd.__init__
self.metrics = init_metrics(config)
self.audit = init_audit(config, self.metrics)

# IRCd.start (early, before listener bind)
await self.audit.start()

# IRCd.stop (end of teardown)
await self.audit.shutdown()
```

### 6. Wire `submit()` into `IRCd.emit_event`

Capture `trace_id`/`span_id` inside the `irc.event.emit` span, build the audit record outside it, call `self.audit.submit(record)`. Helper `_build_audit_record(server_name, event, origin_tag, trace_id, span_id) -> dict` produces the schema-compliant dict with payload (underscore-prefix keys stripped), actor (kind="human" for v1), target, tags (current `traceparent` only).

### 7. PARSE_ERROR records

In `culture/agentirc/client.py::_process_buffer`, the existing `except Exception as exc` handler emits a span event. Add `audit.submit({event_type: "PARSE_ERROR", line_preview, error_type, remote_addr, ...})` alongside.

### 8. Test fixture `audit_dir`

Add to `tests/conftest.py`:

```python
@pytest_asyncio.fixture
async def audit_dir(tmp_path):
    yield tmp_path
```

Tests build a `ServerConfig` with `telemetry.audit_dir=str(tmp_path)` and inspect file contents.

### 9. Documentation

- New `culture/protocol/extensions/audit.md` — record schema + file layout + rotation + retention.
- `docs/agentirc/telemetry.md` — new "What you get in 8.5.0" section.
- `docs/agentirc/audit.md` — operator guide (where files live, jq examples, disable instructions, prune TODO).

### 10. Version bump

`/version-bump minor` → `8.4.0` → `8.5.0`.

## Files to modify / create

**New:**

- `culture/telemetry/audit.py` — `AuditSink`, `init_audit`, `reset_for_tests`, `_build_audit_record` helper.
- `culture/protocol/extensions/audit.md` — record schema doc.
- `docs/agentirc/audit.md` — operator guide.
- `tests/telemetry/test_audit_basic.py`
- `tests/telemetry/test_audit_rotation.py`
- `tests/telemetry/test_audit_overflow.py`
- `tests/telemetry/test_audit_disabled.py`
- `tests/telemetry/test_audit_parse_error.py`
- `tests/telemetry/test_audit_federation.py`

**Modified:**

- `culture/agentirc/config.py` — 5 audit fields on `TelemetryConfig`.
- `culture/telemetry/metrics.py` — `audit_writes` + `audit_queue_depth` on `MetricsRegistry`.
- `culture/telemetry/__init__.py` — re-export `AuditSink`, `init_audit`.
- `culture/agentirc/ircd.py` — `__init__` + `start()` + `stop()` + `emit_event` audit submit.
- `culture/agentirc/client.py` — `_process_buffer` PARSE_ERROR audit submit.
- `tests/conftest.py` — `audit_dir` fixture.
- `docs/agentirc/telemetry.md` — "What you get in 8.5.0".
- `pyproject.toml`, `CHANGELOG.md` — version bump.

## Tests

Per-area tests in `tests/telemetry/test_audit_*.py`:

1. **basic**: emit event → record on disk with right shape (ts, server, event_type, origin, peer, trace_id/span_id, actor, target, payload, tags). Underscore-prefix keys stripped from payload.
2. **rotation**: monkey-patch the date for daily rotation; monkey-patch `audit_max_file_bytes` to a small value for size rotation. Assert two files with `.0`/`.1` suffix.
3. **overflow**: queue depth 2; flood 10 submits; assert `outcome=error` counter ≥ 8.
4. **disabled**: `audit_enabled=False` → no file. `telemetry.enabled=False, audit_enabled=True` → still writes.
5. **parse_error**: send malformed line via raw bytes → `event_type: "PARSE_ERROR"` in JSONL.
6. **federation**: `linked_servers` + per-server audit_dir; PRIVMSG from alpha → record on beta has `origin=federated, peer=alpha`.

## Verification

1. `bash ~/.claude/skills/run-tests/scripts/test.sh -p` — full suite green (current baseline 1022).
2. `bash ~/.claude/skills/run-tests/scripts/test.sh -p tests/telemetry/test_audit_*.py` — audit suite green.
3. Manual: start a server with `audit_enabled=true`; connect weechat; send PRIVMSG/JOIN/PART; `tail ~/.culture/audit/<server>-*.jsonl | jq` — see records.
4. Manual: start with `telemetry.enabled=false, audit_enabled=true`; verify audit still writes (independence).
5. `Agent(subagent_type="doc-test-alignment", ...)` before first push.
6. `Agent(subagent_type="superpowers:code-reviewer", ...)` on staged diff — `audit.py` is a new file with bounded-queue semantics + IO; the kind of choke-point CLAUDE.md calls for pre-push review on.
7. `bash ~/.claude/skills/pr-review/scripts/pr-status.sh <PR>` after push.

## Out of scope (future plans)

- **OTEL Logs export** of audit records — JSONL is source of truth; OTEL Logs is additive. Defer.
- **`audit-prune` CLI** — operators prune manually in v1.
- **Capture inbound IRCv3 tag bag** in the `tags` field — v1 captures only the active span's `traceparent`. Capturing original wire tags would require threading the source `Message` through `emit_event`.
- **`actor.remote_addr`** for non-Client paths — v1 leaves it empty for emit_event-from-server-internal sites.
- **`actor.kind`** — defaults `"human"`. Plan 5/6 refines to `bot`/`harness`.
- **fsync per record** — not in v1.

## Carry-forward notes

- **MetricsRegistry continues to grow.** Plan 5/6 will add `harness_*` / `bot_*` fields. Don't fork the dataclass.
- **`audit_enabled` is not gated by `enabled`.** Future audit fields should follow the same gating.
- **Record schema is a stable contract.** Future schema changes are additive only (new keys); existing keys keep their type.
- **Path expansion.** Resolve `~` once at init; don't store the `~`-form internally.
- **Writer task lifecycle.** Owned by `IRCd.start()` / `IRCd.stop()`. The shutdown drain is bounded.
- **Tests use `await sink.queue.join()`** to drain before assertion.
- **OTEL Logs export deferred** — when added, factor `_build_audit_record` so the same dict feeds both JSONL and the OTEL Logs API.

## Phasing (suggested task breakdown for subagent execution)

1. **Task 1**: TelemetryConfig audit fields + `culture/protocol/extensions/audit.md` schema doc.
2. **Task 2**: `culture/telemetry/audit.py` — `AuditSink`, `init_audit`, lifecycle, rotation logic, isolated tests.
3. **Task 3**: extend `MetricsRegistry` with `audit_writes` + `audit_queue_depth`.
4. **Task 4**: wire `init_audit` + `start()`/`stop()` into `IRCd` lifecycle.
5. **Task 5**: wire `submit()` into `IRCd.emit_event` (with `_build_audit_record` helper).
6. **Task 6**: PARSE_ERROR audit records from `Client._process_buffer`.
7. **Task 7**: integration tests (rotation under live IRCd, federation, disabled, queue overflow).
8. **Task 8**: `docs/agentirc/telemetry.md` "What you get in 8.5.0" + `docs/agentirc/audit.md` operator guide.
9. **Task 9**: version bump 8.4.0 → 8.5.0.
10. **Task 10**: pre-push verification + open PR.
