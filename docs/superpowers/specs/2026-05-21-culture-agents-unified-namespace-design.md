# Design: `culture agents` — unified agent namespace (lifecycle + steward alignment)

- **Date:** 2026-05-21
- **Status:** Approved (brainstorming complete) — pending implementation plan
- **Version target:** 13.0.0 (major — removes the `culture agent` CLI noun)
- **Supersedes naming from:** the original "`culture steward` passthrough" idea explored
  at the start of this brainstorm. That idea was dropped in favor of folding steward
  into a unified `culture agents` noun.

## Summary

Culture has two distinct "agent management" surfaces that today look unrelated:

1. `culture agent` (singular) — imperative lifecycle of one **running daemon** on the
   mesh: `create` / `join` / `start` / `stop` / `status` / `sleep` / `wake` / … (~20 verbs).
2. **steward** (`steward-cli`, the sibling alignment tool) — declarative health of the
   **population of agent definitions** across the sibling corpus: `show` (one agent's
   full config), `doctor` (diagnose a repo or the whole corpus), `overview` (ecosystem
   inventory + relationship graph).

This design merges both under a single plural noun, **`culture agents`**, and **removes
the singular `culture agent` noun entirely**. `culture agents` becomes a *hybrid* noun:
culture-owned lifecycle verbs plus a small set of verbs forwarded verbatim to the
`steward` CLI. The skill-broadcast verb (`announce-skill-update`) lands under the
existing `culture skills` noun, where it belongs semantically.

The structure is not novel — it is exactly the pattern `culture server` already uses
(culture-owned `start`/`stop`/`status` alongside `restart`/`link`/`logs`/`version`/`serve`
forwarded to `agentirc.cli.dispatch`).

## Motivation

- **One mental model for "agents".** A newcomer should not have to know that
  *running* an agent is `culture agent` while *diagnosing* the fleet is a separate
  tool called "steward". Both are agent management; both belong under `culture agents`.
- **Avoid a singular/plural footgun.** An `agent` (singular, lifecycle) and `agents`
  (plural, alignment) pair that did *different* things would be one keystroke apart —
  a classic CLI hazard. Removing the singular noun eliminates the ambiguity instead
  of institutionalizing it.
- **Surface steward through the front door.** Culture is the integrated front-door CLI
  (it already embeds `agex`/`afi`/`irc-lens`); steward is the last major sibling not
  reachable through `culture`.

## Decisions (locked during brainstorming)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | `culture agents` is the unified noun (lifecycle **+** steward alignment). | One place for all agent management. |
| 2 | `culture agents` is a **hybrid noun**, not a passthrough — modeled on `culture server`. | Lifecycle verbs need native argparse/IPC; only alignment verbs forward. |
| 3 | **Hard-remove** `culture agent` (singular). No deprecation alias. | User choice. Cleanest tree; accepts a coordinated cutover (see Migration). |
| 4 | Forward `doctor` / `show` / `overview` under `culture agents`. | These are agent-centric steward verbs. |
| 5 | `announce-skill-update` → `culture skills announce-update` (forwarded, verb remapped). | It is skill-broadcast, not agent management; `culture skills` already exists. |
| 6 | `steward-cli>=0.16,<1.0` as a **hard dependency**. | Zero new transitive weight (steward needs only `pyyaml`, already pinned); matches the other six sibling deps. |
| 7 | Major version bump → **13.0.0**. | Removing a CLI noun is a breaking change. |
| 8 | Brief steward to add `explain` / `learn` / `--json` (cross-repo follow-up). | steward is not yet agent-first compliant; implement culture-side, hand off the sibling work. |

## Architecture

### The hybrid noun (precedent: `culture server`)

`culture/cli/server.py` already demonstrates the exact shape: a `_AGENTIRC_FORWARDED_VERBS`
tuple registered as thin `REMAINDER` subparsers, short-circuited before argparse by
`_maybe_forward_to_agentirc()` in `culture/cli/__init__.py` (because argparse `REMAINDER`
cannot capture `--help` reliably), then replayed through `agentirc.cli.dispatch`.

`culture agents` mirrors this:

- **Native lifecycle verbs** — moved verbatim from today's `agent.py`. Real argparse
  subparsers, real handlers (IPC to the daemon, PID files, `~/.culture/server.yaml`).
  Behavior unchanged except the parent noun (`agent` → `agents`).
- **Forwarded steward verbs** — `_STEWARD_FORWARDED_VERBS = ("doctor", "show", "overview")`,
  registered as thin `REMAINDER` subparsers (`add_help=False`), short-circuited by a new
  `_maybe_forward_to_steward()` and replayed through `steward.cli.main([...])` verbatim.

### Steward delegation mechanism

Add to `culture/cli/__init__.py` a `_maybe_forward_to_steward(argv)` parallel to
`_maybe_forward_to_agentirc(argv)`:

```text
_maybe_forward_to_steward(argv):
    if len(argv) < 2: return None
    if argv[0] == "agents" and argv[1] in agents._STEWARD_FORWARDED_VERBS:
        return _steward_main([argv[1], *argv[2:]])          # verb name unchanged
    if argv[0] == "skills" and argv[1] in skills._STEWARD_FORWARDED:   # {"announce-update": "announce-skill-update"}
        return _steward_main([skills._STEWARD_FORWARDED[argv[1]], *argv[2:]])  # verb remapped
    return None
```

`_steward_main` imports `steward.cli.main` lazily and, on `ImportError`, prints
`steward-cli is not installed: …` to stderr and exits 2 — the same guard `devex`/`afi`
use. `main()` calls `_maybe_forward_to_steward` alongside the existing agentirc
short-circuit, before building the parser.

The short-circuit must run **before** argparse so that `culture agents doctor --help`
and `culture skills announce-update --help` reach steward's own argparse intact. Native
lifecycle verbs (`start`, `stop`, …) are *not* in `_STEWARD_FORWARDED_VERBS`, so they
fall through to argparse unchanged.

## Verb map

### `culture agents` — native lifecycle (from `agent.py`, unchanged behavior)

`create`, `join`, `start`, `stop`, `status`, `rename`, `assign`, `sleep`, `wake`,
`learn`, `message`, `read`, `archive`, `unarchive`, `delete`, `register`, `unregister`,
`install`, `uninstall`, `migrate`.

### `culture agents` — forwarded to steward

| culture invocation | forwards to | purpose |
|--------------------|-------------|---------|
| `culture agents doctor [target] [--scope …]` | `steward doctor …` | diagnose a repo or the corpus |
| `culture agents show <target>` | `steward show …` | one agent's full config in one view |
| `culture agents overview [--scope …]` | `steward overview …` | ecosystem inventory + relationship graph |

### `culture skills` — forwarded to steward (new)

| culture invocation | forwards to | purpose |
|--------------------|-------------|---------|
| `culture skills announce-update …` | `steward announce-skill-update …` | broadcast a migration brief to consumers of a vendored skill |

(`culture skills install …` stays culture-native, unchanged.)

### The three inspection lenses are complementary, not colliding

A check during brainstorming confirmed the two verb sets are **string-disjoint** — no
rename is needed. What looked like overlap is three deliberately distinct lenses, which
the `culture explain agents` text will document:

- `culture agents status` → runtime liveness (which daemons are up on this server) — *native*
- `culture agents show <nick>` → one agent's static config — *steward*
- `culture agents overview` → cross-repo ecosystem graph — *steward*

## Removing `culture agent` (singular)

Hard removal. `culture agent <verb>` will exit with argparse's "invalid choice" error.
Everything that referenced the singular noun must be updated in lockstep:

### Code emitting `culture agent …` strings (must change to `culture agents …`)

- `culture/persistence.py:71` — **systemd `ExecStart` generator** (the operator hazard, see Migration).
- `culture/learn_prompt.py:170-171` — the onboarding prompt agents read on first run.
- `culture/cli/server.py:296` — `culture agent stop --all && culture agent start --all` hint.
- `culture/cli/mesh.py:271` — inline comment.
- `culture/cli/agent.py` (→ `agents.py`) — self-referential hints at lines 366, 422, 820, 865, 1040, 1160.

### Migration for operators (consequence of hard-remove)

Existing installed systemd units were written by `culture agent install` with
`ExecStart=… culture agent start …`. After upgrading to 13.0.0 that `ExecStart` is
invalid and the agent will not (re)start. Remediation, to be documented in
`docs/reference/cli/agent-systemd.md` and CHANGELOG:

> After upgrading, re-run `culture agents install <nick>` for each managed agent to
> rewrite its unit file with the new `ExecStart` (`culture agents start …`), then
> `systemctl --user daemon-reload`.

`culture agents install` (the renamed `culture agent install`) is the supported
remediation path because it regenerates the unit from scratch.

### Out of scope: systemd *service names*

The unit **name** `culture-agent-<nick>.service` is an identifier, not a CLI
invocation. Renaming it to `culture-agents-…` would orphan already-installed units for
no functional gain. Service names stay `culture-agent-<nick>.service`; only the
`ExecStart` command inside changes.

## Introspection

- `culture explain agents` / `culture overview agents` — culture-authored, covering both
  the lifecycle verbs and the forwarded alignment verbs (the three lenses). Replaces
  `_agent_explain` in `culture/cli/introspect.py`; `_NAMESPACES` changes `agent` → `agents`.
- `culture explain agents --json` enumerates verbs via `_collect_verbs("agents")`, which
  reads the registered subparsers — the forwarded steward verbs appear because they are
  registered as (thin) subparsers. No change to the JSON contract code is required.
- Because `agents` is a **native** noun (not in `_PASSTHROUGHS`), katvan reference-sync
  treats it as culture-owned. The forwarded steward verbs' deep reference depends on the
  cross-repo follow-up below.

## Dependency & versioning

- Add `steward-cli>=0.16,<1.0` to `[project.dependencies]` in `pyproject.toml`.
- Regenerate and stage `uv.lock` in the same change.
- `/version-bump major` → 13.0.0 (updates `pyproject.toml`, `culture/__init__.py`,
  `CHANGELOG.md`).

## Implementation phasing

One spec, two PRs, to keep the mechanical rename reviewable apart from the new dependency:

### PR 1 — `agent` → `agents` rename + hard removal (major, 13.0.0)

- Rename `culture/cli/agent.py` → `agents.py`; `NAME = "agents"`; update `agent_command`
  dest → `agents_command` and all internal references.
- Update `GROUPS` and imports in `culture/cli/__init__.py`; update the module docstring.
- Fix every `culture agent …` string in `persistence.py`, `learn_prompt.py`,
  `cli/server.py`, `cli/mesh.py`, and the moved module.
- `introspect.py`: `_NAMESPACES` `agent`→`agents`; `_agent_explain` → `_agents_explain`
  (expanded to describe the lenses).
- Update tests (≈14 files): `test_cli_agent.py` → `test_cli_agents.py`,
  `test_agent_argparse_errors.py`, `test_agent_install_cli.py`, `test_archive.py`,
  `test_channel_cli.py`, `test_cli_introspect.py`, `test_culture_config.py`,
  `test_cutover_daemon_factories.py`, `test_learn_prompt.py`, `test_migrate_cli.py`,
  `test_observer_peek_nick.py`, `test_register_cli.py`, `test_setup_update_cli.py`,
  `test_persistence.py` / `test_persistence_timeout.py` (ExecStart assertions),
  `conftest.py`.
- Update docs: `CLAUDE.md` (root + `culture/cli/CLAUDE.md`), `README.md`,
  `docs/reference/cli/{commands,index,agent-systemd}.md`, `docs/culture/quickstart.md`,
  `docs/reference/harnesses/*.md`, `docs/shared/guides/*.md`, plus the migration note.
- `/version-bump major`; stage `uv.lock` if touched.

### PR 2 — steward dependency + forwarding

- Add `steward-cli>=0.16,<1.0`; regenerate `uv.lock`.
- `agents.py`: `_STEWARD_FORWARDED_VERBS = ("doctor", "show", "overview")` + thin subparsers.
- `skills.py`: `_STEWARD_FORWARDED = {"announce-update": "announce-skill-update"}` + thin subparser.
- `__init__.py`: `_maybe_forward_to_steward()` + wire into `main()`.
- Expand `_agents_explain` to document the forwarded verbs; add the `culture skills`
  forwarded verb to `_skills_explain`.
- Tests: forwarding (verbatim + remapped), `--help` reaches steward, `ImportError`→exit 2,
  `explain agents` lists the forwarded verbs.
- New doc: `docs/reference/cli/agents.md` (or extend `commands.md`) covering the hybrid noun.
- Run the `doc-test-alignment` subagent before first push (new CLI surface).

## Testing strategy

- Per `culture` convention, use `/run-tests` (parallel) and `/run-tests --ci` for coverage.
- No mocks for the server; lifecycle tests keep their real-socket / real-server approach.
- Forwarding tests assert the **argv handed to `steward.cli.main`** (verb verbatim for
  `agents`, remapped for `skills announce-update`) and the `ImportError` exit path —
  mirroring `tests/test_cli_passthrough.py` and the server-forwarding tests.

## Cross-repo hand-off (separate from these PRs)

steward (`agentculture/steward`) implements neither `explain` nor `learn` nor the
`--json` agent-first contract. File an issue via the `communicate` skill
(`post-issue.sh`) requesting them so the forwarded verbs gain a deep, katvan-syncable
reference. Per the cross-repo rule: implement only the culture side here; brief the
sibling agent for the steward work. Until steward ships them, the forwarded verbs work
functionally; only their structured introspection is deferred.

## Out of scope (YAGNI)

- No deprecation alias for `culture agent` (decision #3 — hard remove).
- No renaming of `culture-agent-<nick>.service` unit names.
- Not implementing steward's `explain`/`learn`/`--json` here (hand-off).
- No consolidation of `status`/`show`/`overview` — they are complementary lenses.
- No `--apply` / repair behavior (steward does not implement it yet).

## Open questions

None — all forks resolved during brainstorming (decisions table above).
