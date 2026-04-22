"""Universal introspection verb dispatcher.

Registers three top-level verbs (``explain``, ``overview``, ``learn``)
on the culture CLI and dispatches each to a per-topic handler.

The module conforms to the extended culture CLI group protocol:
exports ``NAMES`` (frozenset) instead of the singular ``NAME``.
"""

from __future__ import annotations

import argparse
from typing import Callable

Handler = Callable[[str | None], tuple[str, int]]

NAMES = frozenset({"explain", "overview", "learn"})

_explain: dict[str, Handler] = {}
_overview: dict[str, Handler] = {}
_learn: dict[str, Handler] = {}

_REGISTRIES: dict[str, dict[str, Handler]] = {
    "explain": _explain,
    "overview": _overview,
    "learn": _learn,
}


def register_topic(
    topic: str,
    *,
    explain: Handler | None = None,
    overview: Handler | None = None,
    learn: Handler | None = None,
) -> None:
    """Register handlers for a topic. Any verb may be omitted."""
    if explain is not None:
        _explain[topic] = explain
    if overview is not None:
        _overview[topic] = overview
    if learn is not None:
        _learn[topic] = learn


def _clear_registry() -> None:
    """Test-only: wipe all registries."""
    _explain.clear()
    _overview.clear()
    _learn.clear()


def _resolve(verb: str, topic: str | None) -> tuple[str, int]:
    registry = _REGISTRIES[verb]
    effective = topic if topic is not None else "culture"
    handler = registry.get(effective)
    if handler is None:
        available = sorted(registry.keys())
        msg = (
            f"unknown topic '{effective}' for {verb};"
            f" available: {', '.join(available) or '(none)'}"
        )
        return msg, 1
    return handler(topic)


def explain(topic: str | None) -> tuple[str, int]:
    return _resolve("explain", topic)


def overview(topic: str | None) -> tuple[str, int]:
    return _resolve("overview", topic)


def learn(topic: str | None) -> tuple[str, int]:
    return _resolve("learn", topic)


# --- CLI group protocol ---------------------------------------------------


def register(subparsers: "argparse._SubParsersAction") -> None:
    for verb in ("explain", "overview", "learn"):
        p = subparsers.add_parser(verb, help=f"{verb.capitalize()} a topic (culture by default)")
        p.add_argument("topic", nargs="?", default=None, help="Topic to inspect")


def dispatch(args: argparse.Namespace) -> None:
    import sys

    verb = args.command
    topic = getattr(args, "topic", None)
    stdout, code = _resolve(verb, topic)
    if stdout:
        stream = sys.stdout if code == 0 else sys.stderr
        end = "" if stdout.endswith("\n") else "\n"
        print(stdout, end=end, file=stream)
    if code != 0:
        sys.exit(code)
