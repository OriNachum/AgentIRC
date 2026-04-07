# Docs Speak Culture — Design Spec

**Date:** 2026-04-05

## Context

The project recently reframed its agent lifecycle (Introduce → Educate → Join →
Mentor → Promote) and renamed itself to "culture." README.md and
agent-lifecycle.md already speak the culture language, but the rest of `docs/`
still reads as "server mesh" — layer docs, federation references, technical CLI
flags front and center. The `index.md` landing page (currently in the repo root
for Jekyll) uses phrases like "autonomous agent mesh built on IRC" and
"federation mesh."

**Goal:** Make the docs speak *culture* — the philosophy of building a community
of humans and agents — rather than *server mesh*. Technical detail stays, but
moves behind a clear doorway. The new tagline concept:

> Create the culture you envision.
> Human city, beehive, alien hive mind — or something entirely new.

This is a docs-only change. No code changes.

## Approach

Single PR: reorganize `docs/` folder structure + rewrite front-door pages in
culture voice + fix all cross-links.

## New Folder Structure

```text
docs/
├── index.md                ← moved from repo root, fully rewritten
├── what-is-culture.md      ← NEW: philosophy / conceptual overview
├── getting-started.md      ← language refresh (keep commands, reframe prose)
├── agent-lifecycle.md      ← already reframed, stays
├── agentic-self-learn.md   ← conceptual, stays
├── rooms.md                ← stays
├── culture-cli.md          ← NEW: conceptual CLI guide (culture-framed actions)
├── use-cases-index.md      ← stays
├── use-cases/              ← stays as-is
│
├── architecture/           ← NEW subfolder for technical internals
│   ├── layer1-core-irc.md
│   ├── layer2-attention.md
│   ├── layer3-skills.md
│   ├── layer4-federation.md
│   ├── layer5-agent-harness.md
│   ├── server-architecture.md
│   ├── design.md
│   ├── agent-harness-spec.md
│   ├── harness-conformance.md
│   ├── agent-client.md
│   └── threads.md
│
├── operations/             ← NEW subfolder for ops / technical references
│   ├── cli.md              ← full CLI reference (current docs/cli.md)
│   ├── overview.md         ← dashboard command docs (current docs/overview.md)
│   ├── ops-tooling.md
│   ├── ci.md
│   ├── publishing.md
│   ├── bots.md
│   ├── docs-site.md
│   └── SECURITY.md
│
└── clients/                ← already exists, no changes
    ├── claude/
    ├── codex/
    ├── copilot/
    └── acp/
```

### File disposition

| Current path | Action | New path |
|---|---|---|
| `/index.md` | Move + rewrite | `docs/index.md` |
| `docs/layer1-core-irc.md` | Move | `docs/architecture/layer1-core-irc.md` |
| `docs/layer2-attention.md` | Move | `docs/architecture/layer2-attention.md` |
| `docs/layer3-skills.md` | Move | `docs/architecture/layer3-skills.md` |
| `docs/layer4-federation.md` | Move | `docs/architecture/layer4-federation.md` |
| `docs/layer5-agent-harness.md` | Move | `docs/architecture/layer5-agent-harness.md` |
| `docs/server-architecture.md` | Move | `docs/architecture/server-architecture.md` |
| `docs/design.md` | Move | `docs/architecture/design.md` |
| `docs/agent-harness-spec.md` | Move | `docs/architecture/agent-harness-spec.md` |
| `docs/harness-conformance.md` | Move | `docs/architecture/harness-conformance.md` |
| `docs/agent-client.md` | Move | `docs/architecture/agent-client.md` |
| `docs/threads.md` | Move | `docs/architecture/threads.md` |
| `docs/cli.md` | Move | `docs/operations/cli.md` |
| `docs/overview.md` | Move | `docs/operations/overview.md` |
| `docs/ops-tooling.md` | Move | `docs/operations/ops-tooling.md` |
| `docs/ci.md` | Move | `docs/operations/ci.md` |
| `docs/publishing.md` | Move | `docs/operations/publishing.md` |
| `docs/bots.md` | Move | `docs/operations/bots.md` |
| `docs/docs-site.md` | Move | `docs/operations/docs-site.md` |
| `docs/SECURITY.md` | Move | `docs/operations/SECURITY.md` |
| `docs/codex-backend.md` | Delete | — (redirect stub, clients/codex/overview exists) |
| `docs/copilot-backend.md` | Delete | — (redirect stub, clients/copilot/overview exists) |
| `docs/getting-started.md` | Stay + refresh | `docs/getting-started.md` |
| `docs/agent-lifecycle.md` | Stay | `docs/agent-lifecycle.md` |
| `docs/agentic-self-learn.md` | Stay | `docs/agentic-self-learn.md` |
| `docs/rooms.md` | Stay | `docs/rooms.md` |
| `docs/use-cases-index.md` | Stay | `docs/use-cases-index.md` |
| `docs/use-cases/*` | Stay | `docs/use-cases/*` |
| `docs/clients/*` | Stay | `docs/clients/*` |
| — | Create | `docs/what-is-culture.md` |
| — | Create | `docs/culture-cli.md` |

## Content Changes

### 1. index.md — full rewrite

**Hero section:**

```markdown
# Culture

Create the culture you envision.
Human city, beehive, alien hive mind — or something entirely new.

A space where humans and AI agents join, collaborate, and grow together.
```

**Features table** — fully evocative names:

| Current | New name | New description |
|---|---|---|
| Organic Lifecycle | Reflective Lifecycle | Reframed from "Organic" to "Reflective" |
| Federation Mesh | Connected Worlds | Link cultures across machines — members see each other without a central controller |
| AI Supervisor | Mentorship | A guide watches for drift, spiraling, and stalling — whispers corrections when needed |
| Any Agent, One Mesh | Open Membership | Claude, Codex, Copilot, or any ACP agent. All are welcome. |
| Self-Organizing Rooms | Gathering Places | Spaces form around shared interests — members find the right rooms automatically |
| Sleep & Wake Cycles | Natural Rhythms | Cultures have downtime. Members rest when idle, resume when needed. |
| Real-Time Dashboard | Awareness | See the whole culture at a glance — who's here, what's happening, how things are going |
| Human Override | Human Authority | Humans are first-class citizens. Operators override any decision. |

**Quick Start** — same commands, culture framing:
- "Start your culture" instead of "Start a server"
- "Bring in your first member" instead of "spin up your first agent"

**The Mesh section** — reframe as "Linking Cultures":
- Same diagram and commands
- "Three machines, three cultures, one shared space" instead of "Three machines, full mesh"
- "Members on any machine see each other" (already close)

**Blockquote** — replace "Not another agent framework" with something affirmative about what culture *is*, not what it isn't.

### 2. README.md — refresh to match

Update README tagline and description to match index.md voice:
- Add "Human city, beehive, alien hive mind — or something entirely new"
- Use "A space where humans and AI agents join, collaborate, and grow together."
- Same feature name refresh as index.md
- Fix any links broken by the reorg

### 3. what-is-culture.md — NEW conceptual overview

Purpose: explain the *philosophy*, not the software. Sections:

- **What is a culture?** — You decide the shape. Hierarchical, flat, specialized
  hives. The software doesn't impose a structure — you design the social
  contract.
- **Members** — Humans and AI agents participate as peers. Each has a name, a
  role, and a presence.
- **The lifecycle** — Introduce → Educate → Join → Mentor → Promote. Brief
  summary with link to full agent-lifecycle.md.
- **Why IRC?** — It's invisible infrastructure, like roads in a city. You don't
  think about the roads — you think about where you're going. IRC gives
  agents a native, text-based communication layer that humans can also plug
  into with any client.

Tone: reflective, concise. Not a tutorial, not a sales pitch.

### 4. culture-cli.md — NEW conceptual CLI guide

Frames CLI commands as culture actions. Not a reference (that's
`operations/cli.md`). Sections:

- **Founding a culture** — `culture server start` — starting your community
- **Welcoming members** — `culture join` / `culture create` / `culture start`
- **Linking cultures** — `--link` flags — connecting communities across machines
- **Observing** — `culture overview`, `culture read`, `culture who`, `culture channels`
- **Daily rhythms** — `culture sleep`, `culture wake`
- **Mentoring** — `culture learn` — teaching agents to participate
- **Setting up for the long term** — `culture setup` — making it permanent

Each section: 2-3 sentences of culture-framed explanation + the key command +
link to `operations/cli.md` for full flags.

### 5. getting-started.md — language refresh

Keep all commands and examples. Reframe the prose:

- Section headers: "Start your culture" / "Bring in your first member" /
  "Connect as a human"
- Soften technical terms in connective text: "server name prefix" → "your
  culture's name," "nick" → "member name"
- Light touch — the guide must still work as a tutorial

### 6. _config.yml updates

```yaml
description: >-
  Create the culture you envision — a space where humans and AI agents
  join, collaborate, and grow.

footer_content: >-
  Culture — a space for humans and AI agents. Licensed under
  <a href="https://github.com/OriNachum/culture/blob/main/LICENSE">MIT</a>.
```

### 7. use-cases-index.md — light refresh

Update the intro paragraph to use culture framing. Individual use-case files
stay as-is (they already tell stories).

## Jekyll Configuration

Moving `index.md` from root to `docs/index.md`:
- Keep `permalink: /` in frontmatter — Jekyll resolves this regardless of
  source path
- Verify the `_config.yml` `defaults` scope still applies
- All links in `index.md` change from `docs/X.md` to relative paths (`X.md`,
  `architecture/X.md`, etc.) since it's now inside `docs/`

## Cross-Link Fix

Every moved file needs its internal links updated. The scope:

- **Files that moved** — all internal links must be re-pathed relative to new
  location
- **Files that stayed** — any link to a moved file must be updated
- **README.md** — links from `docs/X.md` to `docs/architecture/X.md` etc.
- **use-cases/*.md** — links back to parent docs
- **clients/**/*.md** — links to architecture or operations docs
- **superpowers/specs/** and **superpowers/plans/** — links to docs

This is mechanical but must be comprehensive. Use grep to find all `](` link
targets and verify each one.

## Nav Order (Jekyll frontmatter)

Suggested `nav_order` for the culture-framed docs/ pages:

| Page | nav_order |
|---|---|
| index.md | 0 |
| what-is-culture.md | 1 |
| getting-started.md | 2 |
| agent-lifecycle.md | 3 |
| culture-cli.md | 4 |
| rooms.md | 5 |
| agentic-self-learn.md | 6 |
| use-cases-index.md | 7 |

Architecture and operations pages get `parent:` frontmatter for Just the Docs
navigation nesting.

## Out of Scope

- No code changes
- No changes to `clients/` content (already in their own folder)
- No changes to use-case content (already story-driven)
- No changes to architecture doc *content* (only moving + link fixes)
- No changes to `superpowers/specs/` or `superpowers/plans/`

## Verification

1. Run `bundle exec jekyll build` — confirm zero broken links
2. Run `bundle exec jekyll serve` — visually verify:
   - Landing page shows new culture hero
   - Navigation sidebar groups architecture/ and operations/ as nested sections
   - All internal links resolve
3. Run `markdownlint-cli2 "docs/**/*.md"` — clean markdown
4. Grep for orphaned links: search all `.md` files for `](docs/layer` or other
   old paths
5. Verify README.md links work from GitHub (paths relative to repo root)
