from dataclasses import dataclass, field
from typing import Any

import pytest

from culture.clients.claude.supervisor import Supervisor, SupervisorVerdict, make_sdk_evaluate_fn


def test_verdict_parsing():
    assert SupervisorVerdict.parse("OK") == SupervisorVerdict(action="OK", message="")
    assert SupervisorVerdict.parse("CORRECTION You're spiraling") == SupervisorVerdict(
        action="CORRECTION", message="You're spiraling"
    )
    assert SupervisorVerdict.parse("THINK_DEEPER This needs more thought") == SupervisorVerdict(
        action="THINK_DEEPER", message="This needs more thought"
    )
    assert SupervisorVerdict.parse("ESCALATION Still stuck") == SupervisorVerdict(
        action="ESCALATION", message="Still stuck"
    )


def test_verdict_empty_defaults_to_ok():
    assert SupervisorVerdict.parse("") == SupervisorVerdict(action="OK", message="")
    assert SupervisorVerdict.parse("   ") == SupervisorVerdict(action="OK", message="")


def test_verdict_unknown_action_defaults_to_ok():
    assert SupervisorVerdict.parse("RANDOM garbage") == SupervisorVerdict(action="OK", message="")


@pytest.mark.asyncio
async def test_rolling_window():
    whispers = []

    async def on_whisper(msg, wtype):
        whispers.append((msg, wtype))

    async def mock_eval(window, task):
        return SupervisorVerdict(action="OK", message="")

    sup = Supervisor(
        window_size=5,
        eval_interval=3,
        escalation_threshold=3,
        evaluate_fn=mock_eval,
        on_whisper=on_whisper,
        on_escalation=None,
        task_description="test task",
    )
    for i in range(6):
        await sup.observe({"turn": i, "type": "response", "content": f"turn {i}"})
    assert len(sup._window) == 5
    assert len(whispers) == 0


@pytest.mark.asyncio
async def test_whisper_on_correction():
    whispers = []

    async def on_whisper(msg, wtype):
        whispers.append((msg, wtype))

    async def mock_eval(window, task):
        return SupervisorVerdict(action="CORRECTION", message="Stop retrying")

    sup = Supervisor(
        window_size=20,
        eval_interval=2,
        escalation_threshold=3,
        evaluate_fn=mock_eval,
        on_whisper=on_whisper,
        on_escalation=None,
        task_description="test task",
    )
    for i in range(2):
        await sup.observe({"turn": i})
    await sup.wait_for_evals()
    assert len(whispers) == 1
    assert whispers[0] == ("Stop retrying", "CORRECTION")


@pytest.mark.asyncio
async def test_escalation_after_threshold():
    whispers = []
    escalated = []

    async def on_whisper(msg, wtype):
        whispers.append((msg, wtype))

    async def on_escalation(msg):
        escalated.append(msg)

    call_count = 0

    async def mock_eval(window, task):
        nonlocal call_count
        call_count += 1
        return SupervisorVerdict(action="CORRECTION", message=f"Attempt {call_count}")

    sup = Supervisor(
        window_size=20,
        eval_interval=1,
        escalation_threshold=3,
        evaluate_fn=mock_eval,
        on_whisper=on_whisper,
        on_escalation=on_escalation,
        task_description="test task",
    )
    for i in range(3):
        await sup.observe({"turn": i})
        await sup.wait_for_evals()
    assert len(whispers) == 2
    assert len(escalated) == 1


@pytest.mark.asyncio
async def test_ok_resets_escalation_counter():
    whispers = []
    escalated = []

    async def on_whisper(msg, wtype):
        whispers.append((msg, wtype))

    async def on_escalation(msg):
        escalated.append(msg)

    verdicts = iter(
        [
            SupervisorVerdict(action="CORRECTION", message="warn1"),
            SupervisorVerdict(action="CORRECTION", message="warn2"),
            SupervisorVerdict(action="OK", message=""),
            SupervisorVerdict(action="CORRECTION", message="warn3"),
            SupervisorVerdict(action="CORRECTION", message="warn4"),
        ]
    )

    async def mock_eval(window, task):
        return next(verdicts)

    sup = Supervisor(
        window_size=20,
        eval_interval=1,
        escalation_threshold=3,
        evaluate_fn=mock_eval,
        on_whisper=on_whisper,
        on_escalation=on_escalation,
        task_description="test task",
    )
    for i in range(5):
        await sup.observe({"turn": i})
        await sup.wait_for_evals()
    assert len(escalated) == 0
    assert len(whispers) == 4


@pytest.mark.asyncio
async def test_resume_clears_paused_and_counter():
    """After an escalation pauses the supervisor, resume() lets it observe again.

    Without this, an escalated worker stays unsupervised forever, even after
    the operator un-pauses the daemon (which used to leave supervisor.paused
    stuck at True). The daemon's _ipc_resume now calls supervisor.resume().
    """
    whispers = []
    escalated = []

    async def on_whisper(msg, wtype):
        whispers.append((msg, wtype))

    async def on_escalation(msg):
        escalated.append(msg)

    async def mock_eval(window, task):
        return SupervisorVerdict(action="CORRECTION", message="bad")

    sup = Supervisor(
        window_size=20,
        eval_interval=1,
        escalation_threshold=2,
        evaluate_fn=mock_eval,
        on_whisper=on_whisper,
        on_escalation=on_escalation,
        task_description="test",
    )
    # Trigger escalation.
    for i in range(2):
        await sup.observe({"turn": i})
        await sup.wait_for_evals()
    assert sup.paused is True
    assert len(escalated) == 1

    # After resume, observation works again from a clean slate.
    sup.resume()
    assert sup.paused is False
    await sup.observe({"turn": 99})
    await sup.wait_for_evals()
    # consecutive_failures was reset to 0 on resume, so this counts as 1
    # again (a whisper), not an immediate escalation.
    assert len(escalated) == 1  # unchanged
    assert len(whispers) >= 1


# ---------------------------------------------------------------------------
# SDK-based evaluate_fn tests
# ---------------------------------------------------------------------------


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeAssistantMessage:
    content: list = field(default_factory=list)
    model: str = "fake-model"
    parent_tool_use_id: str | None = None
    error: str | None = None
    usage: dict[str, Any] | None = None


@dataclass
class FakeResultMessage:
    session_id: str = "sess-sup-test"
    subtype: str = "result"
    duration_ms: int = 50
    duration_api_ms: int = 40
    is_error: bool = False
    num_turns: int = 1
    stop_reason: str | None = "end_turn"
    total_cost_usd: float | None = 0.001
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None


@pytest.mark.asyncio
async def test_sdk_evaluate_fn_ok(monkeypatch):
    """SDK evaluate_fn parses OK verdict."""

    async def fake_query(*, prompt, options=None, transport=None):
        yield FakeAssistantMessage(content=[FakeTextBlock(text="OK")])
        yield FakeResultMessage()

    monkeypatch.setattr("culture.clients.claude.supervisor.query", fake_query)
    monkeypatch.setattr("culture.clients.claude.supervisor.AssistantMessage", FakeAssistantMessage)
    monkeypatch.setattr("culture.clients.claude.supervisor.TextBlock", FakeTextBlock)

    evaluate = make_sdk_evaluate_fn()
    verdict = await evaluate([{"type": "response", "content": "working"}], "test task")
    assert verdict.action == "OK"
    assert verdict.message == ""


@pytest.mark.asyncio
async def test_sdk_evaluate_fn_correction(monkeypatch):
    """SDK evaluate_fn parses CORRECTION verdict."""

    async def fake_query(*, prompt, options=None, transport=None):
        yield FakeAssistantMessage(
            content=[FakeTextBlock(text="CORRECTION Stop retrying the same approach")]
        )
        yield FakeResultMessage()

    monkeypatch.setattr("culture.clients.claude.supervisor.query", fake_query)
    monkeypatch.setattr("culture.clients.claude.supervisor.AssistantMessage", FakeAssistantMessage)
    monkeypatch.setattr("culture.clients.claude.supervisor.TextBlock", FakeTextBlock)

    evaluate = make_sdk_evaluate_fn()
    verdict = await evaluate([{"type": "response", "content": "retrying"}], "fix bug")
    assert verdict.action == "CORRECTION"
    assert "Stop retrying" in verdict.message


@pytest.mark.asyncio
async def test_sdk_evaluate_fn_escalation(monkeypatch):
    """SDK evaluate_fn parses ESCALATION verdict."""

    async def fake_query(*, prompt, options=None, transport=None):
        yield FakeAssistantMessage(
            content=[FakeTextBlock(text="ESCALATION Agent is stuck, human needed")]
        )
        yield FakeResultMessage()

    monkeypatch.setattr("culture.clients.claude.supervisor.query", fake_query)
    monkeypatch.setattr("culture.clients.claude.supervisor.AssistantMessage", FakeAssistantMessage)
    monkeypatch.setattr("culture.clients.claude.supervisor.TextBlock", FakeTextBlock)

    evaluate = make_sdk_evaluate_fn()
    verdict = await evaluate([{"type": "response", "content": "stuck"}], "deploy fix")
    assert verdict.action == "ESCALATION"
    assert "human needed" in verdict.message


@pytest.mark.asyncio
async def test_sdk_evaluate_fn_error_handling(monkeypatch):
    """SDK evaluate_fn raises on query failure (caught by Supervisor._evaluate)."""

    async def fake_query(*, prompt, options=None, transport=None):
        yield  # async generator — yields nothing before error
        raise RuntimeError("API error")

    monkeypatch.setattr("culture.clients.claude.supervisor.query", fake_query)

    evaluate = make_sdk_evaluate_fn()
    with pytest.raises(RuntimeError, match="API error"):
        await evaluate([{"type": "response", "content": "test"}], "task")
