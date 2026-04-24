from culture.protocol.message import Message
from culture.telemetry.context import (
    TRACEPARENT_TAG,
    TRACESTATE_TAG,
    ExtractResult,
    extract_traceparent_from_tags,
    inject_traceparent,
)

VALID_TP = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


def test_extract_absent_returns_missing():
    msg = Message(command="PRIVMSG", params=["#c", "hi"])
    result = extract_traceparent_from_tags(msg, peer=None)
    assert result.status == "missing"
    assert result.traceparent is None
    assert result.tracestate is None


def test_extract_valid_passes_through():
    msg = Message(
        tags={TRACEPARENT_TAG: VALID_TP, TRACESTATE_TAG: "vendor=abc"},
        command="PRIVMSG",
        params=["#c", "hi"],
    )
    result = extract_traceparent_from_tags(msg, peer="thor")
    assert result.status == "valid"
    assert result.traceparent == VALID_TP
    assert result.tracestate == "vendor=abc"
    assert result.peer == "thor"


def test_extract_malformed_traceparent_is_dropped():
    msg = Message(tags={TRACEPARENT_TAG: "not-a-traceparent"}, command="PRIVMSG")
    result = extract_traceparent_from_tags(msg, peer="thor")
    assert result.status == "malformed"
    assert result.traceparent is None


def test_extract_wrong_length_traceparent_is_dropped():
    # Valid hex, but wrong length (trace-id is 30 hex instead of 32)
    bad = "00-4bf92f3577b34da6a3ce929d0e0e47-00f067aa0ba902b7-01"
    msg = Message(tags={TRACEPARENT_TAG: bad}, command="PRIVMSG")
    result = extract_traceparent_from_tags(msg, peer=None)
    assert result.status == "malformed"


def test_extract_oversize_tracestate_is_dropped_tp_retained():
    oversize = "x=" + ("y" * 520)
    msg = Message(
        tags={TRACEPARENT_TAG: VALID_TP, TRACESTATE_TAG: oversize},
        command="PRIVMSG",
    )
    result = extract_traceparent_from_tags(msg, peer=None)
    assert result.status == "valid"
    assert result.traceparent == VALID_TP
    assert result.tracestate is None  # dropped for length


def test_inject_roundtrip():
    msg = Message(command="PRIVMSG", params=["#c", "hi"])
    inject_traceparent(msg, traceparent=VALID_TP, tracestate="vendor=abc")
    assert msg.tags[TRACEPARENT_TAG] == VALID_TP
    assert msg.tags[TRACESTATE_TAG] == "vendor=abc"

    result = extract_traceparent_from_tags(msg, peer=None)
    assert result.status == "valid"
    assert result.traceparent == VALID_TP
    assert result.tracestate == "vendor=abc"


def test_inject_none_tracestate_does_not_set_tag():
    msg = Message(command="PRIVMSG", params=["#c", "hi"])
    inject_traceparent(msg, traceparent=VALID_TP, tracestate=None)
    assert TRACEPARENT_TAG in msg.tags
    assert TRACESTATE_TAG not in msg.tags


def test_wire_roundtrip_through_parse_format():
    msg = Message(command="PRIVMSG", params=["#c", "hi"])
    inject_traceparent(msg, traceparent=VALID_TP, tracestate="vendor=abc")
    wire = msg.format()
    reparsed = Message.parse(wire)
    result = extract_traceparent_from_tags(reparsed, peer="alpha")
    assert result.status == "valid"
    assert result.traceparent == VALID_TP
    assert result.tracestate == "vendor=abc"
