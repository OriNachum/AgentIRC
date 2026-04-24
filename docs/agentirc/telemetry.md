---
layout: default
title: Telemetry
parent: AgentIRC
nav_order: 90
---

# Telemetry

Culture ships with first-class OpenTelemetry support: traces for every IRC command and event, W3C trace context carried across federation via a new IRCv3 tag, and a local collector pattern that keeps Culture's surface small.

This page covers the **Foundation + Server Tracing** release (culture 8.2.0). Metrics, audit, harness instrumentation, and bot instrumentation ship in subsequent releases.

## What you get in 8.2.0

A single PRIVMSG from a connected client produces a trace with these spans:

```text
irc.command.PRIVMSG           (root, or child of client-supplied traceparent)
├── irc.privmsg.dispatch      (target + body attributes)
│   └── irc.privmsg.deliver.channel OR irc.privmsg.deliver.dm
│       └── irc.event.emit    (from IRCd.emit_event)
└── irc.client.process_buffer (wraps Message.parse + dispatch)
```

Every span is tagged with:

- `service.name=culture.agentirc` (or your override)
- `service.instance.id=<server_name>`

## Configuration

Telemetry is **off by default**. Enable it in `~/.culture/server.yaml`:

```yaml
telemetry:
  enabled: true
  service_name: culture.agentirc
  otlp_endpoint: http://localhost:4317
  otlp_protocol: grpc
  otlp_timeout_ms: 5000
  otlp_compression: gzip
  traces_enabled: true
  traces_sampler: parentbased_always_on
```

- `enabled: false` (default) → no SDK init, no export, no overhead. Traceparent tags on inbound messages are still parsed and validated (for the future mitigation metric), but no spans are created.
- `traces_sampler: parentbased_always_on` → accept upstream sampling decisions via W3C `traceparent` flags; sample everything otherwise. Alternative: `parentbased_traceidratio:0.1` for 10% sampling, or `always_off` to fully suppress.

Standard OpenTelemetry env vars override YAML: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_TRACES_SAMPLER`.

## Running a local collector

Install `otelcol-contrib` from <https://github.com/open-telemetry/opentelemetry-collector-releases/releases>. Start with the template at `docs/agentirc/otelcol-template.yaml`:

```bash
otelcol-contrib --config=docs/agentirc/otelcol-template.yaml
```

The template ships with a `debug` exporter — traces print to stdout. Swap in Tempo, Loki, Grafana Cloud, Honeycomb, or any OTLP-compatible backend by editing the `exporters:` section.

## Trace context over IRC

When telemetry is enabled and a span is active, outbound client messages carry two IRCv3 tags:

- `culture.dev/traceparent` — W3C traceparent header value.
- `culture.dev/tracestate` — W3C tracestate (optional).

Protocol details, length caps, and inbound mitigation rules: see [`tracing`](../../culture/protocol/extensions/tracing.md).

## What's not in 8.2.0

The design spec at `docs/superpowers/specs/2026-04-24-otel-observability-design.md` covers the full three-pillar scope. These pieces ship in later releases:

- Federation trace-context relay across `ServerLink` (so a trace spans multiple servers).
- Metrics pillar (message counters, histograms, federation health).
- Audit JSONL sink.
- Harness-side tracing for `claude`/`codex`/`copilot`/`acp`.
- Bot webhook HTTP instrumentation.

Each will get an entry under "What you get in \<version\>" as it lands.
