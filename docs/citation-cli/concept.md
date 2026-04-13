---
title: The Concept
nav_order: 1
permalink: /concept/
sites: [citation-cli]
---

## The Concept

### The citation metaphor

In any academic or intellectual discipline, there are exactly
three ways to use a source:

- **Quote** — take it as-is. You are citing the text verbatim
  because you need exactly what it is. A quote is a conscious
  choice.
- **Paraphrase** — rewrite it in your terms. The logic stays,
  but you have adapted it to fit your codebase, your language,
  your style. A paraphrase means you understood the source well
  enough to restate it.
- **Synthesize** — absorb it into your own work. The idea
  informed your thinking, but the code is yours now. The boundary
  is gone. A synthesis means you internalized the source
  completely.

Each level implies deeper introspection, which is exactly what
this pattern encodes in the metadata of every cited file.

### The assumption gap

Traditional package management assumes every consumer wants
identical behavior from a shared dependency. You publish a
package, pin a version, and every consumer gets the same code.

That assumption works when consumers are interchangeable. It
breaks when consumers are **expected to diverge** — when each
one wraps a different SDK, speaks a different protocol, or
integrates at fundamentally different points.

Citation CLI starts from the opposite assumption: consumers will
diverge, and the system should make that safe.

### Why cite beats import

When you import a shared package, you accept a contract: the
package controls its own internals, and you call its public API.
That works until you need to change the internals — add a field
to a data structure, swap an I/O layer, rearrange the module
boundaries.

When you cite the reference, you own the result. The reference is
a starting point, not a constraint. You quote what you need
verbatim, paraphrase what has to bend to fit your shape, and
synthesize what dissolves naturally into existing files.

The trade-off is explicit: you give up automatic updates in
exchange for full independence. But the metadata tracks what came
from where, so updates are informed rather than blind.

### Monorepos

Citation CLI is a natural fit for monorepos. In a monorepo, you
already own the source code for your internal packages — publishing
them to a registry just to import them back is unnecessary
ceremony.

Traditional monorepo tooling (npm workspaces, Python namespace
packages, Bazel targets) uses import-time linking to share code
between packages. This avoids the publish step, but creates its
own friction: symlinks, workspace hoisting, version conflicts
between internal and external dependencies, and debugging through
package boundaries instead of just reading the file.

Citation CLI removes the middleman entirely. Copy from `packages/`
into your target directory, modify freely, debug directly. The
code lives where it runs — no indirection, no build-tool magic,
no "which version of the internal package am I actually using?"

The metadata in `pyproject.toml` or `package.json` tracks what
came from where, so you maintain provenance without maintaining a
package registry.

### How it compares

**Vendoring** copies dependencies into your tree, but vendored
code is usually kept separate and untouched — `vendor/` is a
frozen snapshot. Citation CLI expects you to engage with the code
and synthesize it into your own structure.

**Git submodules** link a subdirectory to another repo. You get
updates by pulling, but you don't own the code — changes require
forking or patching. Citation CLI gives you full ownership from
the start.

**Monorepo workspace tooling** (npm workspaces, Python namespace
packages, Bazel) uses import-time linking within the monorepo.
This avoids the external publish step but couples all consumers to
the same version of shared code — changes propagate immediately to
every consumer. Citation CLI is also designed for monorepos but
takes the opposite approach: each consumer gets its own copy and
evolves independently.

**Citation CLI** is closest to vendoring but with three
differences: you are expected to modify the code, you can
synthesize it into existing files, and the metadata tracks
provenance so you can propagate reference updates when you choose
to.
