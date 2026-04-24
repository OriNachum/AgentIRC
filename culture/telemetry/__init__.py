"""OpenTelemetry integration for Culture.

Public surface re-exported here; call sites import from `culture.telemetry`.
"""

from culture.telemetry.context import (
    TRACEPARENT_TAG,
    TRACESTATE_TAG,
    ExtractResult,
    extract_traceparent_from_tags,
    inject_traceparent,
)

__all__ = [
    "TRACEPARENT_TAG",
    "TRACESTATE_TAG",
    "ExtractResult",
    "extract_traceparent_from_tags",
    "inject_traceparent",
]
