---
title: npm CLI
nav_order: 3
permalink: /npm/
sites: [citation-cli]
---

## npm CLI

The `citation-cli` npm package tracks cited code in `package.json`
under the `"citation"` key.

### Install

```bash
npm install -g citation-cli
```

Or as a dev dependency:

```bash
npm install --save-dev citation-cli
```

Or run without installing:

```bash
npx citation-cli --help
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
| `--package-json` | no | Path to package.json (default: `package.json`) |

**What it does:**

1. Reads the existing `package.json`.
2. Scans all files in `--target` (skipping hidden directories).
3. Computes sha256 for each file.
4. Records everything as `"status": "quote"` under
   `"citation.packages.<name>"`.
5. Sets `"cited"` to today's date.
6. Writes `"schema": 2` on the package entry.

#### `cite check`

Verify integrity of cited files.

```bash
cite check [name]
```

| Flag | Required | Description |
| ---- | -------- | ----------- |
| `[name]` | no | Check a specific package (omit to check all) |
| `--package-json` | no | Path to package.json (default: `package.json`) |

**What it reports:**

- **OK** — file hash matches the recorded sha256.
- **DRIFT** — file was modified (hash mismatch).
- **MISSING** — file was deleted.
- **SKIP** — file is a `paraphrase` or `synthesize` (expected to
  differ).

#### `cite migrate`

Migrate a legacy `"assimilai"` key in `package.json` to the v2
`"citation"` schema.

```bash
cite migrate [--dry-run]
```

Refuses to run if `"citation"` already exists and errors on any
unknown file status.

#### `cite sync`

Reserved for 0.2.0 — will update quoted files from the source,
following the propagation rules in the
[Specification]({{ '/spec/#propagation' | relative_url }}).

### package.json schema

```json
{
  "citation": {
    "packages": {
      "harness-claude": {
        "schema": 2,
        "source": "../packages/agent-harness",
        "version": "0.6.0",
        "target": "src/clients/claude",
        "cited": "2026-04-13",
        "files": {
          "daemon.js": { "status": "paraphrase" },
          "transport.js": {
            "status": "quote",
            "sha256": "e3b0c44..."
          },
          "config.js": {
            "status": "synthesize",
            "into": "src/clients/claude/settings.js"
          }
        }
      }
    }
  }
}
```

### File status

After `cite add`, all files start as `quote`. To reclassify a file
as a paraphrase or synthesis, edit `package.json` directly:

```json
{
  "daemon.js": { "status": "paraphrase" },
  "config.js": {
    "status": "synthesize",
    "into": "src/settings.js"
  }
}
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
# Rewrite daemon.js → mark it "status": "paraphrase"
# Absorb config.js into settings.js → mark it "status": "synthesize"

# 4. Update package.json to reflect those decisions

# 5. Check integrity of the remaining quotes
cite check harness-claude
```
