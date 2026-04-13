---
title: Python CLI
nav_order: 2
permalink: /python/
sites: [citation-cli]
---

## Python CLI

The `citation-cli` Python package tracks cited code in
`pyproject.toml` under the `[tool.citation]` section.

### Install

```bash
uv tool install citation-cli
```

Or with pip:

```bash
pip install citation-cli
```

### Commands

#### `cite add`

Record a citation. Scans files in the target directory and records
each as a quote with its sha256 hash.

```bash
cite add <name> \
  --source <path-or-url> \
  --version <semver> \
  --target <local-dir>
```

| Flag | Required | Description |
| ---- | -------- | ----------- |
| `<name>` | yes | Entry name (e.g. `agent-harness`) |
| `--source` | yes | Path or URL to the reference package |
| `--version` | yes | Semver of the reference at citation time |
| `--target` | yes | Local directory where files were placed |
| `--pyproject` | no | Path to pyproject.toml (default: `pyproject.toml`) |

**What it does:**

1. Reads the existing `pyproject.toml`.
2. Scans all files in `--target` (skipping hidden directories).
3. Computes sha256 for each file.
4. Records everything as `status = "quote"` under
   `[tool.citation.packages.<name>]`.
5. Sets `cited` to today's date.
6. Writes `schema = 2` on the package entry.

#### `cite check`

Verify integrity of cited files.

```bash
cite check [name]
```

| Flag | Required | Description |
| ---- | -------- | ----------- |
| `[name]` | no | Check a specific package (omit to check all) |
| `--pyproject` | no | Path to pyproject.toml (default: `pyproject.toml`) |

**What it reports:**

- **OK** — file hash matches the recorded sha256.
- **DRIFT** — file was modified (hash mismatch).
- **MISSING** — file was deleted.
- **SKIP** — file is a `paraphrase` or `synthesize` (expected to
  differ).

Exit code 0 if all quoted files match; non-zero if any drift or
missing files are detected, or if a requested package name is not
found.

#### `cite migrate`

Migrate a legacy `[tool.assimilai]` manifest to the v2
`[tool.citation]` schema.

```bash
cite migrate [--dry-run]
```

| Flag | Required | Description |
| ---- | -------- | ----------- |
| `--pyproject` | no | Path to pyproject.toml (default: `pyproject.toml`) |
| `--dry-run` | no | Preview the translation without writing |

Refuses to run if `[tool.citation]` already exists, and errors on
any unknown file status.

#### `cite sync`

Reserved for the 0.2.0 release — will update quoted files from
the source reference, following the propagation rules in the
[Specification]({{ '/spec/#propagation' | relative_url }}).

### pyproject.toml schema

```toml
[tool.citation.packages.harness-claude]
schema = 2
source = "../packages/agent-harness"
version = "0.6.0"
target = "src/clients/claude"
cited = "2026-04-13"

[tool.citation.packages.harness-claude.files]
"daemon.py" = { status = "paraphrase" }
"irc_transport.py" = { status = "quote", sha256 = "e3b0c44..." }
"config.py" = { status = "synthesize", into = "src/clients/claude/settings.py" }
```

### File status

After `cite add`, all files start as `quote`. To reclassify a file
as a paraphrase or synthesis, edit `pyproject.toml` directly:

```toml
# Rewrote this file to fit our backend
"daemon.py" = { status = "paraphrase" }

# Absorbed into our existing settings module
"config.py" = { status = "synthesize", into = "src/settings.py" }
```

`cite check` will then skip these files.

### Walkthrough

```bash
# 1. Copy reference files into your project
cp -r ../packages/agent-harness/ ./src/clients/claude/

# 2. Record the citation
cite add harness-claude \
  --source ../packages/agent-harness \
  --version 0.6.0 \
  --target ./src/clients/claude

# 3. Engage with the files
# Rewrite daemon.py → mark it status = "paraphrase"
# Absorb config.py into settings.py → mark it status = "synthesize"

# 4. Update pyproject.toml to reflect those decisions

# 5. Check integrity of the remaining quotes
cite check harness-claude
```
