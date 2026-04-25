"""Wire-level injection tests for ServerLink.send_raw — the single choke point
that re-signs every outbound federation line with the current span's W3C
traceparent (per `culture/protocol/extensions/tracing.md`)."""

from __future__ import annotations

import pytest
from opentelemetry import trace as otel_trace

from culture.agentirc.server_link import _prepend_trace_tags
from culture.telemetry.context import TRACEPARENT_TAG

VALID_TP = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


# --- _prepend_trace_tags helper unit tests --------------------------------


def test_prepend_to_untagged_line():
    line = ":alpha SMSG #room alpha-bob :hi"
    out = _prepend_trace_tags(line, VALID_TP)
    assert out == f"@{TRACEPARENT_TAG}={VALID_TP} {line}"


def test_prepend_merges_into_existing_tag_block():
    line = "@vendor=foo :alpha SMSG #room alpha-bob :hi"
    out = _prepend_trace_tags(line, VALID_TP)
    assert out == f"@vendor=foo;{TRACEPARENT_TAG}={VALID_TP} :alpha SMSG #room alpha-bob :hi"


def test_prepend_replaces_existing_traceparent_in_tag_block():
    stale = "00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00"
    line = f"@{TRACEPARENT_TAG}={stale};vendor=x :alpha SMSG #room alpha-bob :hi"
    out = _prepend_trace_tags(line, VALID_TP)
    assert TRACEPARENT_TAG + "=" + VALID_TP in out
    assert stale not in out
    assert "vendor=x" in out


def test_prepend_empty_line_no_op():
    assert _prepend_trace_tags("", VALID_TP) == ""


# --- ServerLink.send_raw injection (uses ServerLink with a fake writer) ----


class _FakeWriter:
    def __init__(self):
        self.buf: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.buf.append(data)

    async def drain(self) -> None:
        pass

    def get_extra_info(self, *_a, **_kw):
        return None


@pytest.mark.asyncio
async def test_send_raw_injects_traceparent_when_span_active(tracing_exporter):
    from culture.agentirc.server_link import ServerLink

    writer = _FakeWriter()
    link = ServerLink(reader=None, writer=writer, server=None, password=None)
    tracer = otel_trace.get_tracer("test")
    with tracer.start_as_current_span("smoke"):
        await link.send_raw(":alpha SMSG #room alpha-bob :hi")

    assert len(writer.buf) == 1
    line = writer.buf[0].decode("utf-8").rstrip("\r\n")
    assert line.startswith("@")
    assert TRACEPARENT_TAG + "=" in line
    assert ":alpha SMSG #room alpha-bob :hi" in line


@pytest.mark.asyncio
async def test_send_raw_no_injection_when_no_span(tracing_exporter):
    from culture.agentirc.server_link import ServerLink

    writer = _FakeWriter()
    link = ServerLink(reader=None, writer=writer, server=None, password=None)
    # No span started.
    await link.send_raw(":alpha SMSG #room alpha-bob :hi")
    line = writer.buf[0].decode("utf-8").rstrip("\r\n")
    assert TRACEPARENT_TAG not in line


@pytest.mark.asyncio
async def test_send_raw_traceparent_matches_active_span(tracing_exporter):
    from culture.agentirc.server_link import ServerLink
    from culture.telemetry import current_traceparent

    writer = _FakeWriter()
    link = ServerLink(reader=None, writer=writer, server=None, password=None)
    tracer = otel_trace.get_tracer("test")
    with tracer.start_as_current_span("smoke"):
        expected_tp = current_traceparent()
        await link.send_raw(":alpha SMSG #room alpha-bob :hi")

    line = writer.buf[0].decode("utf-8").rstrip("\r\n")
    assert f"{TRACEPARENT_TAG}={expected_tp}" in line
