# Culture Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the agentirc package, module, CLI, and all references to "culture" across the entire codebase.

**Architecture:** Three-phase rename — module/imports first (PR 1), config paths/branding/skills second (PR 2), docs/CI/external third (PR 3). Each phase is a self-contained PR that leaves the codebase in a working state.

**Tech Stack:** Python (uv), GitHub Actions, Jekyll, SonarCloud

**Spec:** `docs/superpowers/specs/2026-04-04-culture-rename-design.md`

---

## Phase 1 — Module Rename

### Task 1: Create branch and rename directory

**Files:**

- Rename: `agentirc/` → `culture/`

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feat/culture-rename main
```

- [ ] **Step 2: Rename the package directory**

```bash
git mv agentirc culture
```

- [ ] **Step 3: Verify the rename**

```bash
ls culture/__init__.py culture/cli.py culture/clients/ culture/server/ culture/protocol/
```

Expected: all files present, no `agentirc/` directory.

### Task 2: Update pyproject.toml

**Files:**

- Modify: `pyproject.toml`

- [ ] **Step 1: Update package name**

Change line 2:

```toml
name = "culture"
```

- [ ] **Step 2: Update homepage URL**

Change line 25:

```toml
Homepage = "https://github.com/OriNachum/culture"
```

- [ ] **Step 3: Update console_scripts entry point**

Change line 28:

```toml
culture = "culture.cli:main"
```

- [ ] **Step 4: Update hatchling build target**

Change line 35:

```toml
packages = ["culture"]
```

- [ ] **Step 5: Update force-include paths**

Change lines 38-42 — replace every `"agentirc/` with `"culture/` on both sides of each `=` sign. Example:

```toml
"culture/clients/claude/skill/SKILL.md" = "culture/clients/claude/skill/SKILL.md"
```

- [ ] **Step 6: Update coverage source**

Change line 66:

```toml
source = ["culture"]
```

- [ ] **Step 7: Update coverage omit**

Change line 68:

```toml
"culture/__pycache__/*"
```

- [ ] **Step 8: Update isort config**

Change line 83:

```toml
known_first_party = ["culture"]
```

- [ ] **Step 9: Verify pyproject.toml has no remaining agentirc references**

```bash
grep -n "agentirc" pyproject.toml
```

Expected: zero matches.

### Task 3: Update core module files

**Files:**

- Modify: `culture/__init__.py`
- Modify: `culture/__main__.py`

- [ ] **Step 1: Update `culture/__init__.py`**

Replace full content with:

```python
from importlib.metadata import version as _v

__version__ = _v("culture")
```

- [ ] **Step 2: Update `culture/__main__.py`**

Replace full content with:

```python
"""Allow running culture as ``python -m culture``."""
from culture.cli import main

if __name__ == "__main__":
    main()
```

### Task 4: Update cli.py header and imports

**Files:**

- Modify: `culture/cli.py`

- [ ] **Step 1: Update docstring (lines 1-19)**

Replace every `agentirc` with `culture` in the docstring:

```python
"""Unified CLI entry point for culture.

Subcommands:
    culture server start|stop|status   Manage the IRC server daemon
    culture init                       Register an agent for the current directory
    culture start [nick] [--all]       Start agent daemon(s)
    culture stop [nick] [--all]        Stop agent daemon(s)
    culture status [nick] [--full]     List running agents (--full queries activity)
    culture send <target> <message>    Send a message to a channel or agent
    culture read <channel>             Read recent channel messages
    culture who <channel>              List channel members
    culture channels                   List active channels
    culture learn [--nick X]            Print self-teaching prompt for your agent
    culture sleep [nick] [--all]       Pause agent(s) — stay connected but idle
    culture wake [nick] [--all]        Resume paused agent(s)
    culture overview [--room X] [--agent X] Show mesh overview
    culture setup [--config X] [--uninstall] Set up mesh from mesh.yaml
    culture update [--dry-run] [--skip-upgrade] Upgrade and restart mesh
"""
```

- [ ] **Step 2: Update imports (lines 34-43)**

```python
from culture.clients.claude.config import (
    AgentConfig,
    DaemonConfig,
    ServerConnConfig,
    add_agent_to_config,
    load_config,
    load_config_or_default,
    sanitize_agent_name,
)
from culture.pidfile import is_process_alive, read_pid, remove_pid, write_pid
```

- [ ] **Step 3: Update logger (line 45)**

```python
logger = logging.getLogger("culture")
```

- [ ] **Step 4: Update argparse (lines 84-86)**

```python
    parser = argparse.ArgumentParser(
        prog="culture",
        description="culture — AI agent mesh",
    )
```

### Task 5: Bulk replace all Python imports

**Files:**

- Modify: all `.py` files under `culture/` and `tests/`

- [ ] **Step 1: Replace `from agentirc.` imports across all Python files**

```bash
find culture/ tests/ -name '*.py' -exec sed -i 's/from agentirc\./from culture./g' {} +
```

- [ ] **Step 2: Replace `import agentirc` statements**

```bash
find culture/ tests/ -name '*.py' -exec sed -i 's/import agentirc/import culture/g' {} +
```

- [ ] **Step 3: Replace remaining string references in Python files**

Some files reference `"agentirc"` as a string (logger names, module lookups). Find and review:

```bash
grep -rn "agentirc" culture/ tests/ --include='*.py'
```

Fix each remaining reference manually — these will be string literals like logger names, `importlib` references, or docstrings. Replace `"agentirc"` with `"culture"` where appropriate.

- [ ] **Step 4: Verify no import references remain**

```bash
grep -rn "from agentirc\|import agentirc" culture/ tests/ --include='*.py'
```

Expected: zero matches.

### Task 6: Update packages/agent-harness references

**Files:**

- Modify: `packages/agent-harness/config.py:15`
- Modify: `packages/agent-harness/daemon.py:22-27,49,131,138,428`
- Modify: `packages/agent-harness/irc_transport.py:8-9`
- Modify: `packages/agent-harness/socket_server.py:9`
- Modify: `packages/agent-harness/webhook.py:11`
- Modify: `packages/agent-harness/skill/irc_client.py:2,6,20,30,189`

- [ ] **Step 1: Bulk replace in agent-harness**

```bash
find packages/ -name '*.py' -exec sed -i 's/from agentirc\./from culture./g' {} +
find packages/ -name '*.py' -exec sed -i 's/import agentirc/import culture/g' {} +
```

- [ ] **Step 2: Update default server name in config.py**

In `packages/agent-harness/config.py` line 15, change:

```python
name: str = "culture"
```

- [ ] **Step 3: Update socket path in daemon.py**

In `packages/agent-harness/daemon.py` line 49, change:

```python
f"culture-{agent.nick}.sock",
```

- [ ] **Step 4: Update system prompt in daemon.py**

In `packages/agent-harness/daemon.py` line 138, change:

```python
f"You are {self.agent.nick}, an AI agent on the culture IRC network."
```

- [ ] **Step 5: Update comment references in daemon.py**

Lines 131 and 428 — replace `agentirc/clients/claude/daemon.py` with `culture/clients/claude/daemon.py` in comments.

- [ ] **Step 6: Review remaining references**

```bash
grep -rn "agentirc" packages/ --include='*.py'
```

Fix any remaining string references.

### Task 7: Run tests and commit Phase 1

- [ ] **Step 1: Install updated package**

```bash
uv sync
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Verify CLI works**

```bash
uv run culture --help
```

Expected: help output with `culture` as the prog name.

- [ ] **Step 4: Verify python -m works**

```bash
uv run python -m culture --help
```

Expected: same help output.

- [ ] **Step 5: Final grep verification**

```bash
grep -rn "agentirc" culture/ tests/ packages/ --include='*.py' | grep -v '__pycache__'
```

Expected: zero matches (or only harmless comment references to the old name in historical context).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: rename agentirc module to culture (#78)

Renames the Python package directory from agentirc/ to culture/,
updates all imports, entry points, and build configuration.

BREAKING CHANGE: package name changes from agentirc-cli to culture"
```

---

## Phase 2 — Config Paths, Branding, and Skills

### Task 8: Update config directory paths

**Files:**

- Modify: `culture/cli.py:74-75`
- Modify: `culture/persistence.py:12,33,123,136,159,166,181,188-189,195,215`
- Modify: `culture/bots/config.py:12`
- Modify: `culture/clients/claude/__main__.py:22`

- [ ] **Step 1: Update cli.py config paths (lines 74-75)**

```python
DEFAULT_CONFIG = os.path.expanduser("~/.culture/agents.yaml")
LOG_DIR = os.path.expanduser("~/.culture/logs")
```

- [ ] **Step 2: Update persistence.py LOG_DIR (line 12)**

```python
LOG_DIR = os.path.expanduser("~/.culture/logs")
```

- [ ] **Step 3: Update persistence.py Windows service dir (line 33)**

```python
return Path(os.path.expandvars(r"%USERPROFILE%\.culture\services"))
```

- [ ] **Step 4: Update persistence.py macOS plist names**

Lines 123, 159, 215 — change `com.agentirc.` to `com.culture.`:

```python
plist_name = f"com.culture.{name}"
```

- [ ] **Step 5: Update persistence.py Windows schtasks**

Line 136 — change `agentirc\\{name}` to `culture\\{name}`:

```python
"/TN", f"culture\\{name}",
```

Line 166:

```python
_run_cmd(["schtasks", "/Delete", "/TN", f"culture\\{name}", "/F"])
```

- [ ] **Step 6: Update persistence.py list_services patterns**

Line 181 — change `agentirc-` to `culture-`:

```python
if f.name.startswith("culture-") and f.name.endswith(".service"):
```

Lines 188-189:

```python
if f.name.startswith("com.culture.") and f.name.endswith(".plist"):
    names.append(f.stem.removeprefix("com.culture."))
```

Line 195:

```python
if f.name.startswith("culture-") and f.name.endswith(".bat"):
```

- [ ] **Step 7: Update bots/config.py BOTS_DIR (line 12)**

```python
BOTS_DIR = Path(os.path.expanduser("~/.culture/bots"))
```

- [ ] **Step 8: Update clients/claude/**main**.py (line 22)**

```python
DEFAULT_CONFIG = os.path.expanduser("~/.culture/agents.yaml")
```

- [ ] **Step 9: Verify no ~/.agentirc references remain in code**

```bash
grep -rn '\.agentirc' culture/ --include='*.py'
```

Expected: zero matches.

### Task 9: Update CLI defaults and branding

**Files:**

- Modify: `culture/cli.py:95,123,126`
- Modify: all daemon.py files in `culture/clients/*/`

- [ ] **Step 1: Update server name defaults in cli.py**

Lines 95, 123, 126 — change `default="agentirc"` to `default="culture"`:

```python
srv_start.add_argument("--name", default="culture", help="Server name")
```

```python
srv_stop.add_argument("--name", default="culture", help="Server name")
```

```python
srv_status.add_argument("--name", default="culture", help="Server name")
```

- [ ] **Step 2: Update socket paths in client daemons**

For each backend (`claude`, `codex`, `copilot`, `acp`), find the socket path line in `culture/clients/<backend>/daemon.py` and change `agentirc-` to `culture-`:

```bash
grep -rn "agentirc-" culture/clients/ --include='*.py'
```

Update each match to use `culture-{agent.nick}.sock`.

- [ ] **Step 3: Update system prompts in client daemons**

Find all `"agentirc IRC network"` strings:

```bash
grep -rn "agentirc" culture/clients/ --include='*.py'
```

Replace with `"culture IRC network"` or `"culture mesh"` as appropriate.

- [ ] **Step 4: Scan for any remaining string references**

```bash
grep -rn "agentirc" culture/ --include='*.py' | grep -v '__pycache__'
```

Fix all remaining references.

### Task 10: Rename and update skill files

**Files:**

- Rename: `culture/skills/agentirc/` → `culture/skills/culture/`
- Rename: `plugins/claude-code/skills/agentirc/` → `plugins/claude-code/skills/culture/`
- Modify: `culture/skills/culture/SKILL.md`
- Modify: `plugins/claude-code/skills/culture/SKILL.md`

- [ ] **Step 1: Rename skill directories**

```bash
git mv culture/skills/agentirc culture/skills/culture
git mv plugins/claude-code/skills/agentirc plugins/claude-code/skills/culture
```

- [ ] **Step 2: Update canonical SKILL.md**

In `culture/skills/culture/SKILL.md`, replace:

- Skill name: `agentirc` → `culture`
- Description: `"AgentIRC admin and ops"` → `"Culture admin and ops"`
- All `agentirc` command references → `culture`
- All `~/.agentirc/` path references → `~/.culture/`

- [ ] **Step 3: Update plugin SKILL.md**

In `plugins/claude-code/skills/culture/SKILL.md`, apply the same changes. Also update the auto-copy source path comment if present.

- [ ] **Step 4: Update pyproject.toml force-include paths for renamed skills**

If the force-include section in `pyproject.toml` references skill paths, update them.

- [ ] **Step 5: Check for other skill references**

```bash
grep -rn "skills/agentirc" . --include='*.py' --include='*.md' --include='*.toml' --include='*.yml'
```

Fix any remaining references.

### Task 11: Verify and commit Phase 2

- [ ] **Step 1: Run tests**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Verify no agentirc references remain in code**

```bash
grep -rn "agentirc" culture/ packages/ plugins/ --include='*.py' --include='*.md' | grep -v '__pycache__'
```

Expected: zero matches in Python code; skill markdown files clean.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: update config paths, branding, and skills to culture (#78)

Changes ~/.agentirc/ to ~/.culture/, updates socket names, macOS
plist identifiers, CLI defaults, and renames skill directories."
```

---

## Phase 3 — Docs, CI, External References

### Task 12: Update CI workflows

**Files:**

- Modify: `.github/workflows/publish.yml`
- Modify: `.github/workflows/tests.yml`
- Modify: `.github/workflows/security-checks.yml`

- [ ] **Step 1: Update publish.yml path triggers**

Lines 8 and 13 — change `"agentirc/**"` to `"culture/**"`:

```yaml
paths:
  - "pyproject.toml"
  - "culture/**"
```

- [ ] **Step 2: Update publish.yml package publishing**

Line 57 — step name:

```yaml
- name: Build and publish culture to TestPyPI
```

Lines 62-67 — the second publish step now creates `agentirc-cli` and `agentirc` as aliases. Update to:

```yaml
- name: Build and publish agentirc-cli alias to TestPyPI
  run: |
    sed -i 's/^name = "culture"/name = "agentirc-cli"/' pyproject.toml
    rm -rf dist
    uv build
    uv publish --publish-url https://test.pypi.org/legacy/ --trusted-publishing always --check-url https://test.pypi.org/simple/

- name: Build and publish agentirc alias to TestPyPI
  run: |
    sed -i 's/^name = "agentirc-cli"/name = "agentirc"/' pyproject.toml
    rm -rf dist
    uv build
    uv publish --publish-url https://test.pypi.org/legacy/ --trusted-publishing always --check-url https://test.pypi.org/simple/
```

Lines 71-72 — update install commands:

```yaml
echo "::notice::Install: pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ culture==${DEV_VERSION}"
echo "::notice::Or alias: pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentirc-cli==${DEV_VERSION}"
```

Apply the same pattern to the `publish` job (lines 74-94) for the production PyPI publish — publish `culture` first, then `agentirc-cli` and `agentirc` aliases.

- [ ] **Step 3: Update tests.yml path filter**

Line 43 — change `'agentirc/'` to `'culture/'`:

```bash
CODE_CHANGED=$(git diff --name-only origin/main...HEAD -- 'culture/' 'pyproject.toml' 'tests/')
```

- [ ] **Step 4: Update security-checks.yml targets**

Line 29:

```bash
uv run bandit -r culture/ -f json -o bandit-results.json -c pyproject.toml
```

Line 33:

```bash
uv run pylint culture/ --rcfile=.pylintrc --output-format=json:pylint-results.json,text
```

Line 51:

```bash
uv run pytest --cov=culture --cov-report=xml:coverage.xml --cov-report=term -v
```

### Task 13: Update sonar and Jekyll config

**Files:**

- Modify: `sonar-project.properties`
- Modify: `_config.yml`

- [ ] **Step 1: Update sonar-project.properties**

```properties
sonar.projectKey=OriNachum_culture
sonar.projectName=Culture
sonar.organization=orinachum
sonar.host.url=https://sonarcloud.io

sonar.sources=culture
sonar.tests=tests
```

- [ ] **Step 2: Update _config.yml**

Line 1: `title: Culture`
Line 5: keep `url: "https://agentirc.dev"` (domain migration is separate)
Line 16: `"https://github.com/OriNachum/culture"`
Line 20: `Culture — AI agent mesh for humans and agents.`

### Task 14: Update documentation files

**Files:**

- Modify: `README.md`
- Modify: `index.md`
- Modify: `CLAUDE.md`
- Modify: `docs/cli.md`
- Modify: `docs/publishing.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/SECURITY.md`
- Modify: all files in `docs/clients/`
- Modify: all files in `docs/superpowers/specs/` and `docs/superpowers/plans/`

- [ ] **Step 1: Update README.md**

Replace all `agentirc` references with `culture`:

- Package name in badges and install commands
- CLI command examples (`agentirc server start` → `culture server start`)
- GitHub URLs
- Product name: "AgentIRC" → "Culture"

- [ ] **Step 2: Update index.md**

Same replacements — product name, CLI examples, install commands.

- [ ] **Step 3: Update CLAUDE.md**

Update project description, package management section, test commands, and any `agentirc` CLI references.

- [ ] **Step 4: Update docs/cli.md**

Replace all `agentirc` command examples with `culture`. Update default server names.

- [ ] **Step 5: Update docs/publishing.md**

Update package names (`agentirc-cli` → `culture` as primary, note aliases), install commands.

- [ ] **Step 6: Update docs/getting-started.md**

Update install command: `uv tool install culture`. Update CLI examples.

- [ ] **Step 7: Update docs/SECURITY.md**

Update all URLs:

- SonarCloud dashboard: `id=OriNachum_culture`
- GitHub security advisories: `OriNachum/culture`
- Issue tracker: `OriNachum/culture`
- Badge URLs

- [ ] **Step 8: Bulk update docs/clients/ files**

```bash
find docs/ -name '*.md' -exec sed -i 's/AgentIRC/Culture/g; s/agentirc-cli/culture/g; s/agentirc/culture/g' {} +
```

Then review the changes to ensure no over-replacement (e.g., in URLs that still use agentirc.dev).

- [ ] **Step 9: Update design specs and plan docs**

Update references in `docs/superpowers/specs/` and `docs/superpowers/plans/` where they reference the agentirc package or commands (not the culture-rename spec itself — that already uses the right names).

### Task 15: Update CHANGELOG.md

**Files:**

- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add rename entry at the top of the latest version**

Add under the current version's `### Changed` section:

```markdown
### Changed
- **BREAKING:** Renamed package from `agentirc-cli` to `culture`. `agentirc-cli` and `agentirc` remain as PyPI aliases. CLI command is now `culture`. Config directory is now `~/.culture/`.
```

Historical entries stay unchanged — they are history.

### Task 16: Lint, verify, and commit Phase 3

- [ ] **Step 1: Lint all modified markdown files**

```bash
markdownlint-cli2 "README.md" "CLAUDE.md" "CHANGELOG.md" "index.md" "docs/**/*.md"
```

Fix any issues.

- [ ] **Step 2: Verify no stale references**

```bash
grep -rn "agentirc" docs/ .github/ *.md *.yml *.properties --include='*.md' --include='*.yml' --include='*.properties' | grep -v CHANGELOG | grep -v CNAME | grep -v 'agentirc.dev'
```

Expected: zero matches (CHANGELOG historical entries and CNAME/domain references are expected exclusions).

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "docs: update all documentation, CI, and config for culture rename (#78)

Updates README, CLI docs, CI workflows, SonarCloud config, Jekyll
site, and all markdown references from agentirc to culture."
```

---

## Phase 4 — Post-Merge (Manual Checklist)

These steps happen after all 3 PRs are merged to main.

- [ ] **Rename GitHub repo** — Settings → General → Repository name → `culture`
- [ ] **Update SonarCloud** — create new project or update project key to `OriNachum_culture`
- [ ] **Verify CI** — trigger a test run to confirm all workflows work with new paths
- [ ] **PyPI publish** — verify `culture`, `agentirc-cli`, and `agentirc` all publish correctly
- [ ] **Update workspace CLAUDE.md** — in `/home/spark/git/CLAUDE.md`, update the agentirc references
- [ ] **Update other projects** — any project referencing `agentirc` (daria, etc.) should be updated
- [ ] **Domain** — decide on `agentirc.dev` migration (separate effort)
