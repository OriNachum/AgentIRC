---
title: Citation CLI
nav_order: 0
permalink: /
sites: [citation-cli]
description: Cite, don't import — a code distribution pattern with Quote / Paraphrase / Synthesize semantics.
---

## Citation CLI

**Cite, don't import.** A code distribution pattern for codebases
where consumers are expected to diverge — each consumer copies
the reference into its own tree and owns the result.

```text
packages/reference/       -->  cite  -->  clients/backend-a/
                          -->  cite  -->  clients/backend-b/
                          -->  cite  -->  clients/backend-c/
```

No shared imports. No version pinning. No breakage when one
project evolves.

### Quote, Paraphrase, Synthesize

The citation metaphor is literal. Every file lands at one of three
levels of engagement with the source:

- **Quote** — copied verbatim. You are saying: *this code, exactly
  as it is, is what I need.* Integrity is checked via sha256 so
  drift is detected.
- **Paraphrase** — rewritten in your terms. The logic stays, but
  the code has been adapted to fit your codebase. A paraphrase
  means you understood the source well enough to restate it.
- **Synthesize** — absorbed into an existing consumer file. No
  standalone copy remains. A synthesis means you internalized the
  source completely — the boundary is gone.

### Install

Python (`[tool.citation]` in `pyproject.toml`):

```bash
uv tool install citation-cli
cite add my-pkg --source ../ref --version 1.0.0 --target ./src/my-pkg
cite check
```

Node.js (`"citation"` key in `package.json`):

```bash
npm install -g citation-cli
cite add my-pkg --source ../ref --version 1.0.0 --target ./src/my-pkg
cite check
```

### Migrating from assimilai

citation-cli is the successor to the earlier **assimilai** project.
The schema and vocabulary map one-to-one
(`verbatim`/`adapted`/`dissolved` → `quote`/`paraphrase`/`synthesize`).
To migrate an existing manifest:

```bash
cite migrate             # rewrite pyproject.toml or package.json in place
cite migrate --dry-run   # preview the translation
```

See [Migration]({{ '/migration/' | relative_url }}) for a full
before/after walkthrough.

### Learn more

- [The Concept]({{ '/concept/' | relative_url }}) — why cite beats
  import, and how the three levels of engagement work
- [Python CLI]({{ '/python/' | relative_url }}) — install, commands,
  flags, and `pyproject.toml` schema
- [npm CLI]({{ '/npm/' | relative_url }}) — install, commands,
  flags, and `package.json` schema
- [When Not to Use]({{ '/when-not-to-use/' | relative_url }}) —
  compliance, provenance, and cases where traditional packages are
  the right choice
- [Migration]({{ '/migration/' | relative_url }}) — from assimilai
  v1 to citation-cli v2
- [Specification]({{ '/spec/' | relative_url }}) — formal schema
  definition, field reference, propagation rules

### Origin

citation-cli was developed as part of
[Culture](https://culture.dev), where multiple AI agent backends
(Claude, Codex, and others) need to share infrastructure code while
maintaining full independence in their agent-specific integration
layers. Claude's backend synthesized `config.py` into its own
`settings.py`, while Codex kept it as a quote — same reference,
different engagement strategies.
