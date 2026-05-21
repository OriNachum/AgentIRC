# `culture agents` Unified Namespace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the `culture agent` lifecycle and the steward alignment CLI under one plural `culture agents` noun, hard-remove the singular `culture agent`, and surface `announce-skill-update` under `culture skills`.

**Architecture:** `culture agents` becomes a *hybrid* noun modeled on `culture server`: culture-owned lifecycle verbs (native argparse + IPC) plus alignment verbs (`doctor`/`show`/`overview`) forwarded verbatim to `steward.cli.main`, short-circuited before argparse so `--help` reaches steward. `culture skills announce-update` forwards (verb-remapped) to `steward announce-skill-update`.

**Tech Stack:** Python 3.12, argparse, `uv`, `pytest` + `pytest-xdist`, `steward-cli>=0.16,<1.0`.

**Spec:** `docs/superpowers/specs/2026-05-21-culture-agents-unified-namespace-design.md`

---

## ⚠️ Critical guard: rename CLI nouns, NOT identifiers

This is the single highest-risk part of the plan. In `culture/cli/agent.py` two kinds of `agent` token coexist and must be treated **oppositely**:

| Token | Meaning | Action |
|-------|---------|--------|
| `culture agent ` (space-delimited), `add_parser("agent"`, `dest="agent_command"`, `NAME = "agent"`, `[culture_bin, "agent", "start"]` | the **CLI noun** | **CHANGE → `agents`** |
| `f"culture-agent-{full_nick}"` (svc name, hyphens) | systemd **service name** | **KEEP** |
| `f"agent-{nick}"`, `f"agent-{nick}.log"` (PID/log files) | **runtime identifiers** | **KEEP** |

A blind `agent`→`agents` replace would rename the service unit and PID files, orphaning every running agent. **Never** global-replace. Use the targeted rules below. **Final Phase-1 verification** (run after Task 1.7, once code + docs are done):

```bash
# These MUST still be present (identifiers preserved):
grep -rn 'culture-agent-' culture/cli/agents.py        # → svc names intact (2 hits)
grep -rn 'f"agent-{' culture/cli/agents.py             # → PID/log names intact
# These MUST be gone (noun renamed):
grep -rn '"agent", "start"' culture/                   # → no hits
grep -rn 'agent_command' culture/                      # → no hits
grep -rn 'culture agent ' culture/ docs/ README.md | grep -vE 'CHANGELOG|agent-systemd'  # → no hits
```

---

## File Structure

**Phase 1 — rename + hard-remove (PR1, → 13.0.0):**
- Rename: `culture/cli/agent.py` → `culture/cli/agents.py` (NAME, parser, dispatch, install command, hint strings)
- Modify: `culture/cli/__init__.py` (imports, `GROUPS`, docstring), `culture/cli/introspect.py` (`_NAMESPACES`, `_agents_explain`), `culture/learn_prompt.py`, `culture/cli/server.py:296`, `culture/cli/mesh.py:271`
- Rename test: `tests/test_cli_agent.py` → `tests/test_cli_agents.py`
- Modify tests (≈13): see Task 1.6
- Docs: `CLAUDE.md`, `culture/cli/CLAUDE.md`, `README.md`, `docs/reference/cli/{commands,index,agent-systemd}.md`, `docs/culture/quickstart.md`, `docs/reference/harnesses/*.md`, `docs/shared/guides/*.md`

**Phase 2 — steward dependency + forwarding (PR2, → 13.1.0):**
- Modify: `pyproject.toml` (+`steward-cli`), `uv.lock`, `culture/cli/agents.py` (`_STEWARD_FORWARDED_VERBS`), `culture/cli/skills.py` (`_STEWARD_FORWARDED`), `culture/cli/__init__.py` (`_maybe_forward_to_steward`), `culture/cli/introspect.py` (expand explainers)
- Create test: `tests/test_cli_steward_forwarding.py`
- Docs: `docs/reference/cli/agents.md` (or extend `commands.md`)

---

# Phase 1 — Rename `agent` → `agents` + hard-remove (PR1)

### Task 1.1: Failing tests for the renamed noun

**Files:**
- Create: `tests/test_cli_agents.py` (will replace the git-mv'd file in Task 1.6; create the new-behavior tests here first)

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for the unified `culture agents` noun (replaces singular `culture agent`)."""

from __future__ import annotations

import argparse
import subprocess
import sys


def _top_choices() -> set[str]:
    from culture.cli import _build_parser

    parser = _build_parser()
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    return set(sub.choices)


def test_agents_noun_is_registered():
    assert "agents" in _top_choices()


def test_singular_agent_noun_is_removed():
    assert "agent" not in _top_choices()


def test_culture_agent_singular_is_rejected_at_runtime():
    result = subprocess.run(
        [sys.executable, "-m", "culture", "agent", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower()


def test_culture_agents_status_parses():
    # `status` needs no daemon to parse; --help exits 0 after printing usage.
    result = subprocess.run(
        [sys.executable, "-m", "culture", "agents", "status", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/test_cli_agents.py -v`
Expected: `test_agents_noun_is_registered` FAILS (`agents` not yet a choice); others fail too.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_cli_agents.py
git commit -m "test(cli): failing tests for unified culture agents noun"
```

### Task 1.2: Rename the module and wire it into the parser

**Files:**
- Rename: `culture/cli/agent.py` → `culture/cli/agents.py`
- Modify: `culture/cli/__init__.py`

- [ ] **Step 1: git-mv the module**

```bash
git mv culture/cli/agent.py culture/cli/agents.py
```

- [ ] **Step 2: Apply the targeted noun edits inside `culture/cli/agents.py`**

Make exactly these replacements (NOT a global replace — see the Critical Guard):

```bash
# 1. CLI-noun string occurrences (space-delimited — safe, misses hyphenated identifiers):
sed -i 's/culture agent /culture agents /g' culture/cli/agents.py
# 2. parser dest:
sed -i 's/agent_command/agents_command/g' culture/cli/agents.py
```

Then make these three edits by hand (Edit tool), because they are not space-delimited:

- `NAME = "agent"` → `NAME = "agents"`
- `subparsers.add_parser("agent", help="Manage AI agents")` → `subparsers.add_parser("agents", help="Manage AI agents")`
- Line ~1164: `agent_cmd = [culture_bin, "agent", "start", full_nick, "--foreground"]` → `agent_cmd = [culture_bin, "agents", "start", full_nick, "--foreground"]`

Leave untouched: `svc = f"culture-agent-{full_nick}"` (×2), `f"agent-{...}"` PID/log names, the Python variable name `agent_cmd`, and `for agent in ...` loop variables.

- [ ] **Step 3: Update `culture/cli/__init__.py`**

In the import block (lines ~28-39), change `agent,` → `agents,` (keep alphabetical position). In `GROUPS` (line 43) change `agent` → `agents`:

```python
from culture.cli import (
    afi,
    agents,
    bot,
    channel,
    console,
    devex,
    introspect,
    mesh,
    server,
    skills,
)
...
GROUPS = [agents, server, mesh, channel, bot, skills, devex, afi, console, introspect]
```

Update the module docstring (lines 4-12): `culture agent    {...}` → `culture agents   {...}`.

- [ ] **Step 4: Run the Task 1.1 tests**

Run: `python -m pytest tests/test_cli_agents.py -v`
Expected: all 4 PASS.

- [ ] **Step 5: Verify the module-level keep/change invariants**

```bash
grep -n 'culture-agent-' culture/cli/agents.py   # present (2 hits — svc names kept)
grep -n 'f"agent-{' culture/cli/agents.py        # present (PID/log names kept)
grep -n '"agent", "start"' culture/cli/agents.py # no hits (install argv renamed)
grep -n 'agent_command' culture/cli/agents.py    # no hits (dest renamed)
```

Expected: first two print lines; last two print nothing. (The full-tree guard at the top runs at the end of Phase 1.)

- [ ] **Step 6: Commit**

```bash
git add culture/cli/agents.py culture/cli/__init__.py
git commit -m "feat(cli)!: rename culture agent -> culture agents (hard remove singular)"
```

### Task 1.3: Update `introspect.py` for the renamed noun

**Files:**
- Modify: `culture/cli/introspect.py`

- [ ] **Step 1: Update the namespace registry and explainer**

In `_NAMESPACES` (line ~111) change `"agent"` → `"agents"`.

Rename `_agent_explain` → `_agents_explain` and update its body (lifecycle-only for Phase 1; Phase 2 expands it):

```python
def _agents_explain(_topic: str | None) -> tuple[str, int]:
    return (
        "# culture agents\n\n"
        "The unified agent namespace. Manage the lifecycle of agents on the "
        "mesh — each agent runs as a daemon with its own IRC connection and "
        "harness.\n\n"
        "## Lifecycle verbs\n\n"
        "- `create` / `join` — scaffold or register an agent directory "
        "(claude / codex / copilot / acp)\n"
        "- `register` / `unregister` — add or remove from `~/.culture/server.yaml`\n"
        "- `start` / `stop` / `status` — agent daemon lifecycle\n"
        "- `sleep` / `wake` — pause and resume without unregistering\n"
        "- `install` / `uninstall` — manage the per-agent systemd/launchd unit\n"
        "- `message` / `read` — DM other agents\n"
        "- `learn` — print the onboarding prompt the agent reads on first run\n"
        "- `rename` / `assign` / `archive` / `unarchive` / `delete` / `migrate` — admin\n",
        0,
    )
```

In `_NAMESPACE_EXPLAINERS` (line ~293) change the entry `"agent": _agent_explain,` → `"agents": _agents_explain,`.

- [ ] **Step 2: Run the introspect tests**

Run: `python -m pytest tests/test_cli_introspect.py -v`
Expected: failures referencing the old `agent` namespace — fixed in Task 1.6. For now confirm no import errors:
Run: `python -c "from culture.cli import introspect; print('agents' in introspect._NAMESPACES)"`
Expected: `True`.

- [ ] **Step 3: Commit**

```bash
git add culture/cli/introspect.py
git commit -m "feat(cli): introspect knows the agents namespace"
```

### Task 1.4: Fix the install command + user-facing hint strings outside the module

**Files:**
- Modify: `culture/learn_prompt.py`, `culture/cli/server.py`, `culture/cli/mesh.py`

- [ ] **Step 1: Replace the CLI-noun strings**

```bash
sed -i 's/culture agent /culture agents /g' culture/learn_prompt.py culture/cli/server.py culture/cli/mesh.py
```

This rewrites `learn_prompt.py:166-172` (the onboarding block), `server.py:296` (`culture agents stop --all && culture agents start --all`), and `mesh.py:271` (comment). None of these files reference the hyphenated service/PID identifiers, so the replace is safe.

- [ ] **Step 2: Verify no stray singular noun remains in code**

Run: `grep -rn 'culture agent ' culture/`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add culture/learn_prompt.py culture/cli/server.py culture/cli/mesh.py
git commit -m "feat(cli): point agent hints + onboarding prompt at culture agents"
```

### Task 1.5: Update the install-CLI test (command + description; keep service name)

**Files:**
- Modify: `tests/test_agent_install_cli.py`

- [ ] **Step 1: Update the import and assertions**

- Change `from culture.cli.agent import _cmd_install` → `from culture.cli.agents import _cmd_install`.
- Line ~49: `assert command == ["/usr/bin/culture", "agent", "start", "spark-claude", "--foreground"]` → replace `"agent"` with `"agents"`.
- Line ~50: `assert description == "culture agent spark-claude"` → `assert description == "culture agents spark-claude"`.
- **Leave** `assert svc_name == "culture-agent-spark-claude"` (lines ~48, ~68) UNCHANGED — the service name is preserved.

- [ ] **Step 2: Run the test**

Run: `python -m pytest tests/test_agent_install_cli.py -v`
Expected: PASS (command/description now `agents`, service name still `culture-agent-`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_agent_install_cli.py
git commit -m "test(cli): install argv uses agents; service name preserved"
```

### Task 1.6: Migrate the remaining tests to the `agents` noun

**Files:**
- Rename: `tests/test_cli_agent.py` → fold into `tests/test_cli_agents.py` (append its cases)
- Modify: `tests/test_agent_argparse_errors.py`, `tests/test_archive.py`, `tests/test_channel_cli.py`, `tests/test_cli_introspect.py`, `tests/test_culture_config.py`, `tests/test_cutover_daemon_factories.py`, `tests/test_learn_prompt.py`, `tests/test_migrate_cli.py`, `tests/test_observer_peek_nick.py`, `tests/test_register_cli.py`, `tests/test_setup_update_cli.py`, `tests/conftest.py`

- [ ] **Step 1: Move the old agent CLI test cases into the new file**

```bash
# Append the old file's test bodies (minus its imports/module docstring) into the new one,
# then remove the old file. Do this with the Edit tool: copy each test function from
# tests/test_cli_agent.py into tests/test_cli_agents.py, updating noun references, then:
git rm tests/test_cli_agent.py
```

- [ ] **Step 2: Apply the keep/change rules across the test suite**

```bash
FILES="tests/test_agent_argparse_errors.py tests/test_archive.py tests/test_channel_cli.py \
tests/test_cli_introspect.py tests/test_culture_config.py tests/test_cutover_daemon_factories.py \
tests/test_learn_prompt.py tests/test_migrate_cli.py tests/test_observer_peek_nick.py \
tests/test_register_cli.py tests/test_setup_update_cli.py tests/conftest.py tests/test_cli_agents.py"

# CLI noun, parser dest, module import, and subprocess argv token:
sed -i 's/culture agent /culture agents /g' $FILES
sed -i 's/agent_command/agents_command/g' $FILES
sed -i 's/from culture\.cli\.agent /from culture.cli.agents /g; s/from culture\.cli\.agent import/from culture.cli.agents import/g; s/culture\.cli\.agent\b/culture.cli.agents/g' $FILES
sed -i 's/"-m", "culture", "agent"/"-m", "culture", "agents"/g; s/"culture", "agent",/"culture", "agents",/g' $FILES
```

Then **manually inspect** each file's diff for the keep-list: any `culture-agent-<nick>` service-name or `agent-<nick>` PID/log assertions must remain unchanged (the sed rules above don't touch hyphenated forms, but verify).

- [ ] **Step 3: Run the full CLI + affected suites**

Run: `python -m pytest tests/test_cli_agents.py tests/test_cli_introspect.py tests/test_register_cli.py tests/test_migrate_cli.py tests/test_setup_update_cli.py tests/test_learn_prompt.py tests/test_archive.py tests/test_channel_cli.py -v`
Expected: all PASS.

- [ ] **Step 4: Run the whole suite to catch stragglers**

Run: `python -m pytest -n auto -q`
Expected: green. Fix any remaining `agent`-noun references the sed missed.

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test(cli): migrate suite to culture agents noun"
```

### Task 1.7: Update docs + migration note

**Files:**
- Modify: `CLAUDE.md`, `culture/cli/CLAUDE.md`, `README.md`, `docs/reference/cli/{commands,index,agent-systemd}.md`, `docs/culture/quickstart.md`, `docs/reference/harnesses/*.md`, `docs/shared/guides/*.md`

- [ ] **Step 1: Bulk-replace the CLI noun in docs (excluding CHANGELOG history)**

```bash
grep -rl 'culture agent ' CLAUDE.md README.md culture/cli/CLAUDE.md docs/ \
  | grep -v '/.claude/worktrees/' \
  | xargs sed -i 's/culture agent /culture agents /g'
```

Do **not** touch `CHANGELOG.md` (its historical entries describe what actually shipped under the old noun).

- [ ] **Step 2: Add the operator migration note to `docs/reference/cli/agent-systemd.md`**

Append:

````markdown
## Migrating from `culture agent` (13.0.0)

The singular `culture agent` noun was removed in 13.0.0; all verbs moved to
`culture agents`. Units installed by older versions still contain
`ExecStart=… culture agent start …`, which is now invalid. For each managed
agent, re-run:

```bash
culture agents install <nick>
systemctl --user daemon-reload
```

This rewrites the unit's `ExecStart` to `culture agents start …`. The service
**name** (`culture-agent-<nick>.service`) is unchanged.
````

- [ ] **Step 3: Verify**

Run: `grep -rn 'culture agent ' CLAUDE.md README.md docs/ | grep -vE '/.claude/worktrees/|agent-systemd'`
Expected: no output (the migration note in `agent-systemd.md` intentionally cites the old noun). Then `markdownlint-cli2 docs/reference/cli/agent-systemd.md`.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md culture/cli/CLAUDE.md docs/
git commit -m "docs: culture agent -> culture agents; add systemd migration note"
```

### Task 1.8: Version bump + final gate (PR1)

- [ ] **Step 1: Bump to 13.0.0**

Run the `version-bump` skill: `/version-bump major` (updates `pyproject.toml`, `culture/__init__.py`, `CHANGELOG.md`). Stage `uv.lock` if it changes.

The CHANGELOG entry must call out the breaking change and the migration command from Task 1.7.

- [ ] **Step 2: Full test run**

Run the `run-tests` skill (`/run-tests`).
Expected: all green.

- [ ] **Step 3: Commit + open PR1**

```bash
git add -A
git commit -m "chore: bump 13.0.0 (culture agents namespace, hard-remove agent)"
```

Then use the `cicd` skill to push and open PR1.

---

# Phase 2 — Steward dependency + forwarding (PR2)

### Task 2.1: Add the steward-cli dependency

**Files:**
- Modify: `pyproject.toml`, `uv.lock`

- [ ] **Step 1: Add the dependency**

In `[project.dependencies]` add (after `afi-cli>=0.3,<1.0`):

```toml
    "steward-cli>=0.16,<1.0",
```

- [ ] **Step 2: Lock + verify import**

```bash
uv lock
python -c "from steward.cli import main; print('steward ok')"
```
Expected: `steward ok`.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add steward-cli dependency"
```

### Task 2.2: Failing tests for steward forwarding

**Files:**
- Create: `tests/test_cli_steward_forwarding.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for steward verbs forwarded through `culture agents` / `culture skills`."""

from __future__ import annotations

import subprocess
import sys

import pytest


def test_forwards_agents_doctor_verbatim(monkeypatch):
    calls = []
    import steward.cli

    monkeypatch.setattr(steward.cli, "main", lambda argv: calls.append(argv) or 0)
    from culture.cli import _maybe_forward_to_steward

    rc = _maybe_forward_to_steward(["agents", "doctor", "--scope", "siblings"])
    assert rc == 0
    assert calls == [["doctor", "--scope", "siblings"]]


def test_forwards_skills_announce_update_remapped(monkeypatch):
    calls = []
    import steward.cli

    monkeypatch.setattr(steward.cli, "main", lambda argv: calls.append(argv) or 0)
    from culture.cli import _maybe_forward_to_steward

    rc = _maybe_forward_to_steward(["skills", "announce-update", "communicate"])
    assert rc == 0
    assert calls == [["announce-skill-update", "communicate"]]


def test_native_verbs_are_not_forwarded():
    from culture.cli import _maybe_forward_to_steward

    assert _maybe_forward_to_steward(["agents", "start", "spark-claude"]) is None
    assert _maybe_forward_to_steward(["skills", "install", "claude"]) is None
    assert _maybe_forward_to_steward(["agents"]) is None


def test_agents_doctor_help_reaches_steward():
    result = subprocess.run(
        [sys.executable, "-m", "culture", "agents", "doctor", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "doctor" in result.stdout.lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_cli_steward_forwarding.py -v`
Expected: ImportError / AttributeError — `_maybe_forward_to_steward` does not exist yet.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli_steward_forwarding.py
git commit -m "test(cli): failing tests for steward forwarding"
```

### Task 2.3: Implement the forwarding

**Files:**
- Modify: `culture/cli/agents.py`, `culture/cli/skills.py`, `culture/cli/__init__.py`

- [ ] **Step 1: Add forwarded verbs to `culture/cli/agents.py`**

Near the top (after `NAME = "agents"`):

```python
# Verbs forwarded verbatim to steward.cli.main. Registered as thin REMAINDER
# subparsers and short-circuited before argparse (see _maybe_forward_to_steward
# in culture.cli.__init__) so --help reaches steward's own parser.
_STEWARD_FORWARDED_VERBS = ("doctor", "show", "overview")
```

At the top of `register()`, before the lifecycle subparsers are added (right after `agents_sub = agents_parser.add_subparsers(dest="agents_command")`):

```python
    for verb in _STEWARD_FORWARDED_VERBS:
        fwd = agents_sub.add_parser(
            verb, help=f"(forwarded to steward {verb})", add_help=False
        )
        fwd.add_argument("argv", nargs=argparse.REMAINDER)
```

- [ ] **Step 2: Add the forwarded verb to `culture/cli/skills.py`**

After `NAME = "skills"`:

```python
# culture-facing verb -> steward verb. Forwarded verbatim via
# _maybe_forward_to_steward (culture.cli.__init__).
_STEWARD_FORWARDED = {"announce-update": "announce-skill-update"}
```

In `register()`, after the `install` subparser:

```python
    for culture_verb, steward_verb in _STEWARD_FORWARDED.items():
        fwd = skills_sub.add_parser(
            culture_verb, help=f"(forwarded to steward {steward_verb})", add_help=False
        )
        fwd.add_argument("argv", nargs=argparse.REMAINDER)
```

- [ ] **Step 3: Add `_maybe_forward_to_steward` to `culture/cli/__init__.py`**

Import `agents` and `skills` are already in the import block. Add this function next to `_maybe_forward_to_agentirc`:

```python
def _maybe_forward_to_steward(argv: list[str]) -> int | None:
    """Bypass argparse for steward verbs forwarded under `agents` / `skills`.

    Mirrors `_maybe_forward_to_agentirc`: argparse REMAINDER can't capture
    `--help` reliably, so forwarded steward verbs are short-circuited here and
    replayed through `steward.cli.main` verbatim (the `skills` verb is remapped
    to steward's canonical name). Returns the exit code, or None to let
    argparse handle a native verb.
    """
    if len(argv) < 2:
        return None
    noun, verb = argv[0], argv[1]
    if noun == "agents" and verb in agents._STEWARD_FORWARDED_VERBS:
        steward_argv = [verb, *argv[2:]]
    elif noun == "skills" and verb in skills._STEWARD_FORWARDED:
        steward_argv = [skills._STEWARD_FORWARDED[verb], *argv[2:]]
    else:
        return None
    try:
        from steward.cli import main as steward_main
    except ImportError as exc:  # pragma: no cover — declared dep
        print(f"steward-cli is not installed: {exc}", file=sys.stderr)
        return 2
    return steward_main(steward_argv) or 0
```

In `main()`, right after the existing agentirc short-circuit block:

```python
        forwarded = _maybe_forward_to_steward(sys.argv[1:])
        if forwarded is not None:
            sys.exit(forwarded)
```

- [ ] **Step 4: Run the forwarding tests**

Run: `python -m pytest tests/test_cli_steward_forwarding.py -v`
Expected: all 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add culture/cli/agents.py culture/cli/skills.py culture/cli/__init__.py
git commit -m "feat(cli): forward steward verbs under culture agents / skills"
```

### Task 2.4: Expand the explainers to document forwarded verbs

**Files:**
- Modify: `culture/cli/introspect.py`

- [ ] **Step 1: Add the alignment section to `_agents_explain`**

Append before the final `return`'s closing — add to the markdown body:

```python
        "\n## Alignment verbs (forwarded to steward)\n\n"
        "- `doctor` — diagnose this repo or the whole sibling corpus\n"
        "- `show <target>` — one agent's full configuration in one view\n"
        "- `overview` — ecosystem inventory + relationship graph\n\n"
        "Three inspection lenses: `status` (runtime liveness), `show` (static "
        "config), `overview` (cross-repo graph).\n"
```

- [ ] **Step 2: Update `_skills_explain`**

Add a bullet for the forwarded verb:

```python
        "- `announce-update` — broadcast a vendored-skill migration brief "
        "(forwarded to `steward announce-skill-update`)\n"
```

- [ ] **Step 3: Test**

Run: `python -m pytest tests/test_cli_introspect.py -v`
Expected: PASS. Then spot-check:
Run: `python -m culture explain agents | grep -i doctor`
Expected: the doctor bullet prints.

- [ ] **Step 4: Commit**

```bash
git add culture/cli/introspect.py
git commit -m "docs(cli): explain agents/skills document forwarded steward verbs"
```

### Task 2.5: Reference doc + doc-test alignment

**Files:**
- Create: `docs/reference/cli/agents.md`
- Modify: `docs/reference/cli/commands.md`, `docs/reference/cli/index.md`

- [ ] **Step 1: Write `docs/reference/cli/agents.md`**

Document the hybrid noun: the lifecycle verbs (native) and the forwarded steward verbs (`doctor`/`show`/`overview`), plus `culture skills announce-update`. Note that forwarded verbs require `steward-cli` (a declared dependency) and pass flags through verbatim. Mirror the structure of `docs/reference/cli/afi.md`.

- [ ] **Step 2: Run doc-test-alignment**

```text
Agent(subagent_type="doc-test-alignment", ...)  # audit the branch diff for doc gaps
```
Address any flagged gaps.

- [ ] **Step 3: Lint + commit**

```bash
markdownlint-cli2 "docs/reference/cli/agents.md"
git add docs/reference/cli/
git commit -m "docs(cli): reference page for the culture agents hybrid noun"
```

### Task 2.6: Version bump + final gate (PR2)

- [ ] **Step 1: Bump to 13.1.0**

Run `/version-bump minor` (new feature: steward forwarding). Stage `uv.lock`.

- [ ] **Step 2: Full test run**

Run `/run-tests --ci`.
Expected: green with coverage.

- [ ] **Step 3: Commit + open PR2**

```bash
git add -A
git commit -m "chore: bump 13.1.0 (steward forwarding under agents/skills)"
```

Use the `cicd` skill to push and open PR2.

---

# Phase 3 — Cross-repo hand-off (separate, not a culture PR)

### Task 3.1: Brief steward to add `explain`/`learn`/`--json`

- [ ] **Step 1: File the issue**

Use the `communicate` skill's `post-issue.sh` to open an issue on `agentculture/steward` requesting the agent-first introspection contract: `explain` and `learn` verbs plus `--json` (per `docs/reference/cli/learn-explain-json.md`), so the verbs forwarded under `culture agents` gain a deep, katvan-syncable reference. Implement only the culture side here; the steward work is the sibling agent's.

---

## Self-Review

**Spec coverage:**
- Architecture (hybrid noun, server precedent) → Tasks 2.1-2.3 ✓
- Verb map: native lifecycle → Phase 1; forwarded `doctor`/`show`/`overview` → 2.3; `skills announce-update` → 2.3 ✓
- Hard-remove `culture agent` → Tasks 1.1-1.2; rejection test 1.1 ✓
- ExecStart / systemd migration → Tasks 1.5, 1.7 ✓ (plus the PID/service identifier guard, which is *stricter* than the spec)
- Introspection (`_agents_explain`, `_NAMESPACES`) → 1.3, 2.4 ✓
- Dependency + versioning (13.0.0, 13.1.0) → 1.8, 2.1, 2.6 ✓
- Cross-repo hand-off → Task 3.1 ✓
- Three inspection lenses documented → 2.4 ✓

**Placeholder scan:** No TBD/TODO. The one doc-authoring step (2.5 Step 1) gives a concrete content spec + a mirror file (`afi.md`); acceptable for prose. All code steps show complete code.

**Type/name consistency:** `_maybe_forward_to_steward`, `_STEWARD_FORWARDED_VERBS` (tuple, agents.py), `_STEWARD_FORWARDED` (dict, skills.py), `agents_command` (dest) used consistently across Tasks 1.2, 2.2, 2.3. `_agents_explain` defined in 1.3, extended in 2.4 — same name.

**Risk note:** The keep-vs-change identifier guard (service name `culture-agent-`, PID/log `agent-`) is the highest-risk area and is called out at the top, enforced with verification commands in Task 1.2 Step 5.
