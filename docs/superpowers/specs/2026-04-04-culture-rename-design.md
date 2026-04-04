# Design Spec: Rename AgentIRC to Culture

**Date:** 2026-04-04
**Issue:** [#78 — Rename AgentIRC to Culture](https://github.com/OriNachum/AgentIRC/issues/78)
**Type:** Naming/branding rename (no new features)

## Context

AgentIRC has evolved beyond an IRC chat layer. It includes automatons,
history, visibility, control over agents, and a philosophy guiding how
agents and humans collaborate. The product is a **Culture** — a space
users shape like a company, city, or hivemind.

This rename reflects that evolution. The chat layer remains available
under legacy names, but the recommended install and brand is **culture**.

## Package Strategy

Three PyPI names publish identical content:

| PyPI Name | Status | CLI Command |
|-----------|--------|-------------|
| `culture` | **Recommended** | `culture` |
| `agentirc-cli` | Legacy alias | `culture` |
| `agentirc` | Legacy alias | `culture` |

All three install the same `culture` module and register the `culture`
console script. Users are directed to `pip install culture` (or
`uv tool install culture`).

### Module Structure

- Python module directory: `culture/` (renamed from `agentirc/`)
- Entry point: `culture = "culture.cli:main"`
- Config directory: `~/.culture/` (replaces `~/.agentirc/`)
  - `~/.culture/agents.yaml`
  - `~/.culture/logs/`
  - `~/.culture/bots/`
- Socket naming: `culture-<nick>.sock`
- macOS launchd: `com.culture.<name>.plist`
- Logger name: `culture`

### GitHub Repository

- Rename `OriNachum/AgentIRC` to `OriNachum/culture` (lowercase)
- GitHub auto-redirects the old URL
- SonarCloud project key updates to `OriNachum_culture`
- Domain (agentirc.dev) migration is a separate follow-up

## Phased Implementation

### Phase 1 — Module Rename (PR)

The core mechanical change. Every Python import and module reference
updates from `agentirc` to `culture`.

**Files affected (~100+ Python files):**

- `git mv agentirc/ culture/`
- `pyproject.toml`:
  - `name = "culture"`
  - `culture = "culture.cli:main"` (entry point)
  - `packages = ["culture"]` (build target)
  - Force-include paths: `culture/...`
  - `known_first_party = ["culture"]` (isort)
  - Coverage source: `["culture"]`
- `culture/__init__.py`: version lookup → `"culture"`
- `culture/__main__.py`: `from culture.cli import main`
- `culture/cli.py`:
  - `prog="culture"`
  - `description="culture — AI agent mesh"`
  - `logger = logging.getLogger("culture")`
- All `from agentirc.` → `from culture.`
- All `import agentirc` → `import culture`
- All test file imports
- `packages/agent-harness/` references

**Verification:**

- `pytest` passes
- `culture --help` works
- `python -m culture` works
- `grep -r "from agentirc\|import agentirc" culture/ tests/` returns zero

### Phase 2 — Config Paths, Branding, and Skills (PR)

User-facing paths and product identity.

**Config paths:**

- `~/.agentirc/` → `~/.culture/` (all occurrences in code and docs)
- Socket: `agentirc-<nick>.sock` → `culture-<nick>.sock`
- macOS plist: `com.agentirc.*` → `com.culture.*`

**CLI branding:**

- Default server name: `"culture"` (was `"agentirc"`)
- Docstrings, help text, error messages

**Skills:**

- `culture/skills/agentirc/` → `culture/skills/culture/`
- `plugins/claude-code/skills/agentirc/` → `plugins/claude-code/skills/culture/`
- Skill name and description in SKILL.md files
- All skill content referencing `agentirc` commands or paths

**Verification:**

- Config files created in `~/.culture/`
- Daemons create `culture-<nick>.sock` sockets
- `grep -r "agentirc" culture/` returns zero (excluding vendored/historical)

### Phase 3 — Docs, CI, External References (PR)

Documentation, CI/CD, and all external-facing references.

**Documentation:**

- `README.md`: rebrand, update install commands, badges
- `index.md`: update Jekyll homepage
- `CHANGELOG.md`: add rename entry at top (historical entries stay as-is)
- `CLAUDE.md`: update project description and references
- `docs/cli.md`: update all command examples
- `docs/publishing.md`: update package names
- `docs/getting-started.md`: update install and plugin references
- `docs/SECURITY.md`: update all URLs
- All design specs and plan docs referencing `agentirc`
- Client docs (`docs/clients/*/irc-tools.md`): update GitHub links

**CI/CD:**

- `.github/workflows/publish.yml`: path filters, package names, publish steps
- `.github/workflows/tests.yml`: path filter (`culture/` instead of `agentirc/`)
- `.github/workflows/security-checks.yml`: bandit, pylint, pytest targets

**Configuration:**

- `_config.yml`: site title → "Culture", footer, GitHub URL
- `sonar-project.properties`: project key → `OriNachum_culture`, sources → `culture`
- `CNAME`: keep `agentirc.dev` for now (domain migration is separate)

**Verification:**

- `bundle exec jekyll build` succeeds
- CI workflows pass on a test branch
- `markdownlint-cli2` passes on edited docs
- `grep -r "agentirc" docs/ .github/ *.md *.yml *.properties` returns only
  CHANGELOG historical entries and CNAME

### Phase 4 — Post-Merge (Manual Steps)

These happen after all PRs are merged:

1. **Rename GitHub repo:** `OriNachum/AgentIRC` → `OriNachum/culture`
2. **SonarCloud:** update or recreate project with new key
3. **PyPI publish:** publish `culture` package; publish `agentirc-cli` and
   `agentirc` aliases with same content via CI name-override mechanism
4. **Domain:** decide on domain migration (separate effort)
5. **Announce:** update any external references (workspace CLAUDE.md,
   other projects referencing agentirc)

## Migration Notes for Users

- Existing `~/.agentirc/` configs must be moved to `~/.culture/`
- Running daemons must be restarted (socket names change)
- The `agentirc` CLI command no longer exists; use `culture`
- `pip install culture` is the recommended install going forward

## What Does NOT Change

- IRC protocol (RFC 2812 base + extensions)
- Nick format (`<server>-<agent>`)
- Agent harness architecture (assimilai pattern)
- All-backends rule
- Mesh linking and federation
- CHANGELOG historical entries (they are history, not references)
- Git commit history
