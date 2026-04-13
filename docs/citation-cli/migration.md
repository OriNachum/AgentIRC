---
title: Migration
nav_order: 5
permalink: /migration/
sites: [citation-cli]
---

## Migration from Assimilai v1

citation-cli supersedes the earlier **assimilai** project. The
schema and vocabulary map one-to-one:

| Assimilai v1 | Citation CLI v1 |
| ------------ | --------------- |
| `[tool.assimilai]` | `[tool.citation]` |
| `"assimilai"` (package.json) | `"citation"` (package.json) |
| `assimilated` field | `cited` field |
| status `verbatim` | status `quote` |
| status `adapted` | status `paraphrase` |
| status `dissolved` | status `synthesize` |
| (no `schema` field) | `schema = 2` |

### Run the migration

From the root of any project that has a legacy manifest:

```bash
cite migrate             # rewrite pyproject.toml or package.json in place
cite migrate --dry-run   # preview the translation
```

`cite migrate` refuses to run if a `[tool.citation]` / `"citation"`
block already exists, and errors on any unrecognized file status.

### Before / after (Python)

Legacy `pyproject.toml`:

```toml
[tool.assimilai.packages.harness-claude]
source = "../packages/agent-harness"
version = "0.6.0"
target = "src/clients/claude"
assimilated = "2026-03-24"

[tool.assimilai.packages.harness-claude.files]
"daemon.py" = { status = "adapted" }
"irc_transport.py" = { status = "verbatim", sha256 = "e3b0c44..." }
"config.py" = { status = "dissolved", into = "src/clients/claude/settings.py" }
```

After `cite migrate`:

```toml
[tool.citation.packages.harness-claude]
schema = 2
source = "../packages/agent-harness"
version = "0.6.0"
target = "src/clients/claude"
cited = "2026-03-24"

[tool.citation.packages.harness-claude.files]
"daemon.py" = { status = "paraphrase" }
"irc_transport.py" = { status = "quote", sha256 = "e3b0c44..." }
"config.py" = { status = "synthesize", into = "src/clients/claude/settings.py" }
```

### Before / after (npm)

Legacy `package.json`:

```json
{
  "assimilai": {
    "packages": {
      "harness-claude": {
        "source": "../packages/agent-harness",
        "version": "0.6.0",
        "target": "src/clients/claude",
        "assimilated": "2026-03-24",
        "files": {
          "daemon.js": { "status": "adapted" },
          "transport.js": { "status": "verbatim", "sha256": "e3b0c44..." },
          "config.js": { "status": "dissolved", "into": "src/clients/claude/settings.js" }
        }
      }
    }
  }
}
```

After `cite migrate`:

```json
{
  "citation": {
    "packages": {
      "harness-claude": {
        "schema": 2,
        "source": "../packages/agent-harness",
        "version": "0.6.0",
        "target": "src/clients/claude",
        "cited": "2026-03-24",
        "files": {
          "daemon.js": { "status": "paraphrase" },
          "transport.js": { "status": "quote", "sha256": "e3b0c44..." },
          "config.js": { "status": "synthesize", "into": "src/clients/claude/settings.js" }
        }
      }
    }
  }
}
```

### The old packages

The `assimilai` package is frozen at `0.1.1` on both PyPI and npm,
with a deprecation notice pointing at `citation-cli`. There is no
shim or forwarding — install `citation-cli` directly.
