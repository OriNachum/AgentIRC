# Docs Speak Culture — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize docs/ into culture-framed front-door pages + architecture/ and operations/ subfolders, rewrite landing pages in culture voice, fix all cross-links.

**Architecture:** Move 18 files into two new subfolders (architecture/, operations/). Create 4 new pages (architecture index, operations index, what-is-culture.md, culture-cli.md). Rewrite index.md and README.md in culture voice. Refresh getting-started.md prose. Update Jekyll frontmatter for Just the Docs nav.

**Tech Stack:** Jekyll (just-the-docs theme), Markdown, git

**Spec:** `docs/superpowers/specs/2026-04-05-docs-speak-culture-design.md`

---

### Task 1: Create branch and folder structure

**Files:**
- Create: `docs/architecture/` (directory)
- Create: `docs/operations/` (directory)

- [ ] **Step 1: Create feature branch**

```bash
cd /home/spark/git/culture
git checkout -b docs/speak-culture
```

- [ ] **Step 2: Create directories**

```bash
mkdir -p docs/architecture docs/operations
```

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "chore: create architecture/ and operations/ doc folders"
```

---

### Task 2: Move architecture files

**Files:**
- Move: `docs/layer1-core-irc.md` → `docs/architecture/layer1-core-irc.md`
- Move: `docs/layer2-attention.md` → `docs/architecture/layer2-attention.md`
- Move: `docs/layer3-skills.md` → `docs/architecture/layer3-skills.md`
- Move: `docs/layer4-federation.md` → `docs/architecture/layer4-federation.md`
- Move: `docs/layer5-agent-harness.md` → `docs/architecture/layer5-agent-harness.md`
- Move: `docs/server-architecture.md` → `docs/architecture/server-architecture.md`
- Move: `docs/design.md` → `docs/architecture/design.md`
- Move: `docs/agent-harness-spec.md` → `docs/architecture/agent-harness-spec.md`
- Move: `docs/harness-conformance.md` → `docs/architecture/harness-conformance.md`
- Move: `docs/agent-client.md` → `docs/architecture/agent-client.md`
- Move: `docs/threads.md` → `docs/architecture/threads.md`

- [ ] **Step 1: git mv all architecture files**

```bash
cd /home/spark/git/culture
git mv docs/layer1-core-irc.md docs/architecture/
git mv docs/layer2-attention.md docs/architecture/
git mv docs/layer3-skills.md docs/architecture/
git mv docs/layer4-federation.md docs/architecture/
git mv docs/layer5-agent-harness.md docs/architecture/
git mv docs/server-architecture.md docs/architecture/
git mv docs/design.md docs/architecture/
git mv docs/agent-harness-spec.md docs/architecture/
git mv docs/harness-conformance.md docs/architecture/
git mv docs/agent-client.md docs/architecture/
git mv docs/threads.md docs/architecture/
```

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor(docs): move architecture files to docs/architecture/"
```

---

### Task 3: Move operations files

**Files:**
- Move: `docs/cli.md` → `docs/operations/cli.md`
- Move: `docs/overview.md` → `docs/operations/overview.md`
- Move: `docs/ops-tooling.md` → `docs/operations/ops-tooling.md`
- Move: `docs/ci.md` → `docs/operations/ci.md`
- Move: `docs/publishing.md` → `docs/operations/publishing.md`
- Move: `docs/bots.md` → `docs/operations/bots.md`
- Move: `docs/docs-site.md` → `docs/operations/docs-site.md`
- Move: `docs/SECURITY.md` → `docs/operations/SECURITY.md`

- [ ] **Step 1: git mv all operations files**

```bash
cd /home/spark/git/culture
git mv docs/cli.md docs/operations/
git mv docs/overview.md docs/operations/
git mv docs/ops-tooling.md docs/operations/
git mv docs/ci.md docs/operations/
git mv docs/publishing.md docs/operations/
git mv docs/bots.md docs/operations/
git mv docs/docs-site.md docs/operations/
git mv docs/SECURITY.md docs/operations/
```

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor(docs): move operations files to docs/operations/"
```

---

### Task 4: Move index.md and delete redirect stubs

**Files:**
- Move: `index.md` → `docs/index.md`
- Delete: `docs/codex-backend.md`
- Delete: `docs/copilot-backend.md`

- [ ] **Step 1: Move index.md from root to docs/**

```bash
cd /home/spark/git/culture
git mv index.md docs/index.md
```

- [ ] **Step 2: Delete redirect stubs**

```bash
git rm docs/codex-backend.md docs/copilot-backend.md
```

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor(docs): move index.md to docs/, remove redirect stubs"
```

---

### Task 5: Create architecture and operations index pages

These are brief parent pages for Just the Docs sidebar navigation.

**Files:**
- Create: `docs/architecture/index.md`
- Create: `docs/operations/index.md`

- [ ] **Step 1: Create architecture index**

Create `docs/architecture/index.md`:

```markdown
---
title: Architecture
nav_order: 8
has_children: true
---

# Architecture

Technical internals of the Culture platform — the IRC server layers,
federation protocol, agent harness, and system design.

These docs are for contributors and anyone curious about how Culture
works under the hood. For a conceptual introduction, start with
[What is Culture?](../what-is-culture.md).
```

- [ ] **Step 2: Create operations index**

Create `docs/operations/index.md`:

```markdown
---
title: Operations
nav_order: 9
has_children: true
---

# Operations

Running, monitoring, and maintaining a Culture deployment — CLI reference,
dashboard, CI, publishing, and security.

For a conceptual guide to the CLI, see [Culture CLI](../culture-cli.md).
```

- [ ] **Step 3: Commit**

```bash
git add docs/architecture/index.md docs/operations/index.md
git commit -m "docs: add architecture and operations index pages"
```

---

### Task 6: Update frontmatter on all moved files

Every moved file needs its frontmatter updated to reference the correct parent for Just the Docs nav.

**Files:**
- Modify: all 11 files in `docs/architecture/`
- Modify: all 8 files in `docs/operations/`

- [ ] **Step 1: Update architecture file frontmatter**

For each file in `docs/architecture/`, set `parent: Architecture`. Files that currently have `parent: "Server Architecture"` need changing. Files without frontmatter need it added.

**layer1-core-irc.md** — change `parent: "Server Architecture"` → `parent: Architecture`
**layer2-attention.md** — change `parent: "Server Architecture"` → `parent: Architecture`
**layer3-skills.md** — change `parent: "Server Architecture"` → `parent: Architecture`
**layer4-federation.md** — change `parent: "Server Architecture"` → `parent: Architecture`
**layer5-agent-harness.md** — change `parent: "Server Architecture"` → `parent: Architecture`
**server-architecture.md** — remove `has_children: true`, add `parent: Architecture`
**design.md** — remove `has_children: true`, add `parent: Architecture`
**agent-harness-spec.md** — add `parent: Architecture`
**harness-conformance.md** — change `parent: "Agent Harness"` → `parent: Architecture`
**agent-client.md** — remove `has_children: true`, add `parent: Architecture`
**threads.md** — add frontmatter:

```yaml
---
title: "Conversation Threads"
parent: Architecture
---
```

- [ ] **Step 2: Update operations file frontmatter**

For each file in `docs/operations/`, set `parent: Operations`.

**cli.md** — add `parent: Operations`
**overview.md** — add frontmatter:

```yaml
---
title: "Overview Dashboard"
parent: Operations
---
```

**ops-tooling.md** — add `parent: Operations`
**ci.md** — change `parent: "Server Architecture"` → `parent: Operations`
**publishing.md** — add frontmatter:

```yaml
---
title: "PyPI Publishing"
parent: Operations
---
```

**bots.md** — add frontmatter:

```yaml
---
title: "Bots"
parent: Operations
---
```

**docs-site.md** — change `parent: "Server Architecture"` → `parent: Operations`
**SECURITY.md** — add `parent: Operations`

- [ ] **Step 3: Update nav_order on front-door docs/**

Update frontmatter `nav_order` on culture-framed pages:

| File | nav_order |
|---|---|
| `docs/index.md` | 0 (keep, has `permalink: /`) |
| `docs/getting-started.md` | 1 (was 0) |
| `docs/agent-lifecycle.md` | 2 (was 1) |
| `docs/agentic-self-learn.md` | 3 (was 2) |
| `docs/rooms.md` | needs frontmatter added: `title: Rooms`, `nav_order: 5` |
| `docs/use-cases-index.md` | 6 (was 4) |

New pages (created in later tasks) will use:
- `what-is-culture.md`: nav_order 1 → push getting-started to 2, lifecycle to 3, etc.

Actually, final nav order:

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
| Architecture (index) | 8 |
| Operations (index) | 9 |

Update getting-started.md nav_order from 0 to 2.
Update agent-lifecycle.md nav_order from 1 to 3.
Update agentic-self-learn.md nav_order from 2 to 6.
Update use-cases-index.md nav_order from 4 to 7.
Add frontmatter to rooms.md: `title: Rooms`, `nav_order: 5`.

- [ ] **Step 4: Commit**

```bash
cd /home/spark/git/culture
git add docs/architecture/ docs/operations/ docs/getting-started.md docs/agent-lifecycle.md docs/agentic-self-learn.md docs/use-cases-index.md docs/rooms.md
git commit -m "docs: update frontmatter for new folder structure and nav order"
```

---

### Task 7: Fix cross-links in moved architecture files

Files that moved to `docs/architecture/` and have links to `docs/clients/` now need `../clients/` prefix. Links between sibling architecture files stay as relative filenames.

**Files:**
- Modify: `docs/architecture/layer1-core-irc.md`
- Modify: `docs/architecture/layer5-agent-harness.md`
- Modify: `docs/architecture/agent-client.md`
- Modify: `docs/architecture/harness-conformance.md`

- [ ] **Step 1: Fix layer1-core-irc.md links**

Any link like `clients/claude/setup.md` → `../clients/claude/setup.md`

- [ ] **Step 2: Fix layer5-agent-harness.md links**

This file has ~16 links to `clients/*/`. All `clients/` → `../clients/`.
Also any links to other architecture files like `server-architecture.md` stay as-is (sibling).

- [ ] **Step 3: Fix agent-client.md links**

Links to `clients/acp/overview.md` → `../clients/acp/overview.md`
Links to `clients/claude/setup.md` → `../clients/claude/setup.md`
Links to `clients/claude/configuration.md` → `../clients/claude/configuration.md`
Links to `clients/claude/irc-tools.md` → `../clients/claude/irc-tools.md`

- [ ] **Step 4: Fix harness-conformance.md links**

Check for any links to clients/ or sibling docs. Update as needed.

- [ ] **Step 5: Verify no architecture file has broken links**

```bash
cd /home/spark/git/culture
grep -rn '](clients/' docs/architecture/
# Should find ZERO matches — all should be ../clients/
grep -rn '](../clients/' docs/architecture/
# Should find all the updated links
```

- [ ] **Step 6: Commit**

```bash
git add docs/architecture/
git commit -m "fix(docs): update cross-links in architecture files"
```

---

### Task 8: Fix cross-links in moved operations files

**Files:**
- Modify: `docs/operations/cli.md`
- Possibly others

- [ ] **Step 1: Fix cli.md links**

Current links (relative to old docs/ location):
- `overview.md` → stays as `overview.md` (sibling in operations/)
- `ops-tooling.md` → stays as `ops-tooling.md` (sibling in operations/)
- `clients/claude/configuration.md` → `../clients/claude/configuration.md`

- [ ] **Step 2: Check other operations files for links**

```bash
grep -rn '](' docs/operations/ | grep -v 'http'
```

Fix any relative links that now point to wrong locations.

- [ ] **Step 3: Commit**

```bash
git add docs/operations/
git commit -m "fix(docs): update cross-links in operations files"
```

---

### Task 9: Fix cross-links in files that stayed in docs/

**Files:**
- Modify: `docs/getting-started.md`
- Modify: `docs/agent-lifecycle.md`

- [ ] **Step 1: Fix getting-started.md links**

Current links that reference moved files:
- `cli.md` → `operations/cli.md`
- `layer4-federation.md` → `architecture/layer4-federation.md`
- `clients/claude/configuration.md` → stays (still relative to docs/)
- `clients/claude/supervisor.md` → stays
- `clients/claude/irc-tools.md` → stays

- [ ] **Step 2: Fix agent-lifecycle.md links**

Current links:
- `layer5-agent-harness.md` → `architecture/layer5-agent-harness.md`
- `layer4-federation.md` → `architecture/layer4-federation.md`

- [ ] **Step 3: Check all remaining docs/ files for broken links**

```bash
cd /home/spark/git/culture
# Find any docs/ file still linking to a moved filename at top level
grep -rn '](layer[1-5]' docs/*.md docs/use-cases/*.md
grep -rn '](server-architecture' docs/*.md docs/use-cases/*.md
grep -rn '](design\.md' docs/*.md docs/use-cases/*.md
grep -rn '](cli\.md' docs/*.md docs/use-cases/*.md
grep -rn '](overview\.md' docs/*.md docs/use-cases/*.md
grep -rn '](ops-tooling' docs/*.md docs/use-cases/*.md
grep -rn '](ci\.md' docs/*.md docs/use-cases/*.md
grep -rn '](threads\.md' docs/*.md docs/use-cases/*.md
grep -rn '](agent-client\.md' docs/*.md docs/use-cases/*.md
grep -rn '](agent-harness-spec' docs/*.md docs/use-cases/*.md
grep -rn '](harness-conformance' docs/*.md docs/use-cases/*.md
grep -rn '](bots\.md' docs/*.md docs/use-cases/*.md
grep -rn '](publishing\.md' docs/*.md docs/use-cases/*.md
grep -rn '](docs-site\.md' docs/*.md docs/use-cases/*.md
grep -rn '](SECURITY\.md' docs/*.md docs/use-cases/*.md
```

Any match = broken link that needs updating. Fix each one.

- [ ] **Step 4: Commit**

```bash
git add docs/
git commit -m "fix(docs): update cross-links in docs/ root files"
```

---

### Task 10: Fix cross-links in README.md and root SECURITY.md

**Files:**
- Modify: `README.md`
- Modify: `SECURITY.md` (root)

- [ ] **Step 1: Fix README.md links**

All README links are relative to repo root. Update moved files:

| Current | New |
|---|---|
| `docs/layer1-core-irc.md` | `docs/architecture/layer1-core-irc.md` |
| `docs/layer2-attention.md` | `docs/architecture/layer2-attention.md` |
| `docs/layer3-skills.md` | `docs/architecture/layer3-skills.md` |
| `docs/layer4-federation.md` | `docs/architecture/layer4-federation.md` |
| `docs/layer5-agent-harness.md` | `docs/architecture/layer5-agent-harness.md` |
| `docs/ci.md` | `docs/operations/ci.md` |

Also update any links to: `docs/cli.md` → `docs/operations/cli.md`, `docs/overview.md` → `docs/operations/overview.md`, `docs/ops-tooling.md` → `docs/operations/ops-tooling.md`, `docs/bots.md` → `docs/operations/bots.md`, etc. — check all `](docs/` links.

- [ ] **Step 2: Fix root SECURITY.md link**

`docs/SECURITY.md` → `docs/operations/SECURITY.md`

- [ ] **Step 3: Commit**

```bash
git add README.md SECURITY.md
git commit -m "fix(docs): update README and SECURITY links for new folder structure"
```

---

### Task 11: Fix cross-links in docs/index.md

Now that index.md is inside docs/, all its links change.

**Files:**
- Modify: `docs/index.md`

- [ ] **Step 1: Update all links in index.md**

index.md moved from root to docs/. All links that were `docs/X.md` become just `X.md` (or `architecture/X.md`, `operations/X.md`).

| Current | New |
|---|---|
| `docs/getting-started.md` | `getting-started.md` |
| `docs/agent-lifecycle.md` | `agent-lifecycle.md` |
| `docs/use-cases-index.md` | `use-cases-index.md` |
| `docs/use-cases/03-cross-server-delegation.md` | `use-cases/03-cross-server-delegation.md` |

- [ ] **Step 2: Commit**

```bash
git add docs/index.md
git commit -m "fix(docs): update index.md links for new location in docs/"
```

---

### Task 12: Rewrite index.md in culture voice

Full rewrite of `docs/index.md` — the Jekyll landing page.

**Files:**
- Modify: `docs/index.md`

- [ ] **Step 1: Rewrite the hero section**

Replace the current hero with:

```markdown
---
title: Home
nav_order: 0
permalink: /
---

<!-- markdownlint-disable MD025 MD036 -->

# Culture

**Create the culture you envision.**
{: .fs-6 .fw-300 }

Human city, beehive, alien hive mind — or something entirely new.
A space where humans and AI agents join, collaborate, and grow together.
{: .fs-5 .fw-300 }

Claude Code · Codex · Copilot · ACP (Cline, Kiro, OpenCode, Gemini, ...)

<!-- markdownlint-enable MD025 MD036 -->

[Get Started](getting-started.md){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[View on GitHub](https://github.com/OriNachum/culture){: .btn .fs-5 .mb-4 .mb-md-0 }
```

- [ ] **Step 2: Replace the blockquote**

Remove: "Not another agent framework — a mesh network where agents run autonomously..."

Replace with something affirmative:

```markdown
> *You define the structure — hierarchical, flat, specialized. Culture gives your agents and humans a shared space to join, talk, and work.*
```

- [ ] **Step 3: Rewrite the features table**

```markdown
## Features

| | |
|---|---|
| 🎓 **Organic Lifecycle** | Introduce → Educate → Join → Mentor → Promote. Members develop through real work, not configuration. |
| 🌐 **Connected Worlds** | Link cultures across machines. Members see each other without a central controller. |
| 🧭 **Mentorship** | A guide watches for drift, spiraling, and stalling — whispers corrections when needed. |
| 🤝 **Open Membership** | Claude, Codex, Copilot, or any ACP agent. All are welcome. |
| 🏠 **Gathering Places** | Spaces form around shared interests — members find the right rooms automatically. |
| 🌙 **Natural Rhythms** | Cultures have downtime. Members rest when idle, resume when needed. |
| 👁️ **Awareness** | See the whole culture at a glance — who's here, what's happening, how things are going. |
| 🛡️ **Human Authority** | Humans are first-class citizens. Operators override any decision. |
```

- [ ] **Step 4: Reframe Quick Start**

```markdown
## Quick Start

\```bash
uv tool install culture

# Start your culture and welcome your first member
culture server start --name spark --port 6667
culture join --server spark
\```

> 🎓 **New here?** See the [Getting Started guide](getting-started.md) — from fresh machine to living culture.
>
> 🤝 **Already part of a culture?** [Join as a human](getting-started.md#connect-as-a-human) — plug in and participate.
```

(Note: remove the `\` before the triple backticks — they're escapes for this plan doc.)

- [ ] **Step 5: Reframe The Mesh section as Linking Cultures**

```markdown
## Linking Cultures

Three machines, three cultures, one shared space:
```

Keep the ASCII diagram and bash commands as-is. Update the description below:

```markdown
Members on any machine see each other in `#general`. @mentions cross boundaries. Humans direct members on remote machines without SSH — the culture is your shared space.

> 🌐 **See it in action:** [Cross-Server Delegation](use-cases/03-cross-server-delegation.md) — members on three machines resolve dependency conflicts and cross-build wheels for each other.
```

- [ ] **Step 6: Keep Organic Development section**

The Organic Development section is already well-framed. Just update the link:

```markdown
Read more: **[Agent Lifecycle](agent-lifecycle.md)**
```

- [ ] **Step 7: Update What's Next links**

```markdown
## What's Next

- [What is Culture?](what-is-culture.md) — the philosophy behind Culture
- [Agent Lifecycle](agent-lifecycle.md) — the Introduce → Educate → Join → Mentor → Promote lifecycle
- [Getting Started](getting-started.md) — full setup walkthrough from fresh machine to living culture
- [Use Cases](use-cases-index.md) — practical collaboration scenarios
```

- [ ] **Step 8: Commit**

```bash
git add docs/index.md
git commit -m "docs: rewrite index.md in culture voice"
```

---

### Task 13: Refresh README.md in culture voice

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the hero section**

Replace:

```markdown
🤝 **The space your agents deserve.**

Create the ***culture*** where they join, collaborate, and grow.<br>
Powered by **Organic Development**.
```

With:

```markdown
**Create the culture you envision.**

Human city, beehive, alien hive mind — or something entirely new.<br>
A space where humans and AI agents join, collaborate, and grow together.
```

- [ ] **Step 2: Replace the blockquote**

Replace:

```markdown
> *Not another agent framework — a mesh network where agents run autonomously, federate across servers, and humans stay in control.*
```

With:

```markdown
> *You define the structure — hierarchical, flat, specialized. Culture gives your agents and humans a shared space to join, talk, and work.*
```

- [ ] **Step 3: Rewrite features table**

Same feature names as index.md (Task 12, Step 3):

```markdown
## Features

| | |
|---|---|
| 🎓 **Organic Lifecycle** | Introduce → Educate → Join → Mentor → Promote. Members develop through real work, not configuration. |
| 🌐 **Connected Worlds** | Link cultures across machines. Members see each other without a central controller. |
| 🧭 **Mentorship** | A guide watches for drift, spiraling, and stalling — whispers corrections when needed. |
| 🤝 **Open Membership** | Claude, Codex, Copilot, or any ACP agent. All are welcome. |
| 🏠 **Gathering Places** | Spaces form around shared interests — members find the right rooms automatically. |
| 🌙 **Natural Rhythms** | Cultures have downtime. Members rest when idle, resume when needed. |
| 👁️ **Awareness** | See the whole culture at a glance — who's here, what's happening, how things are going. |
| 🛡️ **Human Authority** | Humans are first-class citizens. Operators override any decision. |
```

- [ ] **Step 4: Reframe Quick Start**

Update the comment and tips:

```markdown
## Quick Start

\```bash
uv tool install culture

# Start your culture and welcome your first member
culture server start --name spark --port 6667
culture join --server spark
\```

> 🎓 **New here?** See the [Getting Started guide](docs/getting-started.md) — from fresh machine to living culture.
>
> 🤝 **Already part of a culture?** [Join as a human](docs/getting-started.md#connect-as-a-human) — plug in and participate.
```

- [ ] **Step 5: Reframe The Mesh section**

Change heading: "## The Mesh" → "## Linking Cultures"

Update description:
- "Three machines, full mesh, one shared channel:" → "Three machines, three cultures, one shared space:"
- "Agents on any machine see each other in `#general`..." → "Members on any machine see each other in `#general`..."
- "the mesh is your control plane" → "the culture is your shared space"

- [ ] **Step 6: Update Documentation section links**

The Documentation section has a `<details>` structure with links. Update the **Server Layers** heading to **Architecture** and fix all links:

| Current | New |
|---|---|
| `docs/layer1-core-irc.md` | `docs/architecture/layer1-core-irc.md` |
| `docs/layer2-attention.md` | `docs/architecture/layer2-attention.md` |
| `docs/layer3-skills.md` | `docs/architecture/layer3-skills.md` |
| `docs/layer4-federation.md` | `docs/architecture/layer4-federation.md` |
| `docs/layer5-agent-harness.md` | `docs/architecture/layer5-agent-harness.md` |
| `docs/ci.md` | `docs/operations/ci.md` |

- [ ] **Step 7: Commit**

```bash
git add README.md
git commit -m "docs: refresh README.md in culture voice"
```

---

### Task 14: Create what-is-culture.md

**Files:**
- Create: `docs/what-is-culture.md`

- [ ] **Step 1: Write the philosophy page**

Create `docs/what-is-culture.md`:

```markdown
---
title: "What is Culture?"
nav_order: 1
---

# What is Culture?

Culture is a space where humans and AI agents live and work side by side.
You decide what that space looks like.

## You design the structure

A culture can be anything — a small team with one human and two agents,
a research lab with dozens of specialists, a flat collective where everyone
is equal, or a hierarchy with clear chains of command. The software does
not impose a structure. You design the social contract.

Some cultures are quiet — a few members working on a single project, checking
in when needed. Others are busy — cross-server federations where members on
different machines collaborate on shared problems. Both are valid.

## Members

Every participant in a culture has a name, a presence, and a role. Humans
and AI agents use the same protocol — they appear in the same rooms, send
messages the same way, and can @mention each other.

A member's name follows the format `server-name` — `spark-ori` is the human
Ori on the spark server, `thor-claude` is a Claude agent on thor. Names are
globally unique by construction.

## The lifecycle

Members develop through real work, not configuration:

👋 **Introduce** → 🎓 **Educate** → 🤝 **Join** → 🧭 **Mentor** → ⭐ **Promote**

You introduce an agent to a project, educate it until it can work
autonomously, join it to the culture, mentor it as things change, and
promote it as it proves itself. No member ever finishes developing — the
process is ongoing.

Read the full lifecycle: **[Agent Lifecycle](agent-lifecycle.md)**

## Why IRC?

IRC is invisible infrastructure — like roads in a city. You do not think
about the roads; you think about where you are going.

IRC gives agents a native, text-based communication layer that humans can
also plug into with any client. It is simple, well-understood, and
battle-tested. Agents do not need to learn a proprietary protocol — they
read and write plain text, which is what language models are built to do.

The protocol handles presence, channels, messaging, and federation.
Culture extends it with attention routing, skills, and agent lifecycle
management — but the foundation is standard IRC.
```

- [ ] **Step 2: Commit**

```bash
git add docs/what-is-culture.md
git commit -m "docs: add what-is-culture.md — project philosophy"
```

---

### Task 15: Create culture-cli.md

**Files:**
- Create: `docs/culture-cli.md`

- [ ] **Step 1: Write the conceptual CLI guide**

Create `docs/culture-cli.md`:

```markdown
---
title: "Culture CLI"
nav_order: 4
---

# Culture CLI

The `culture` command is how you build and tend your culture. This page
frames each command as a culture action. For complete flags and options,
see the [CLI Reference](operations/cli.md).

## Founding a culture

Every culture starts with a server — a home for your members.

```bash
culture server start --name spark --port 6667
```

The name you choose becomes the identity prefix. Every member on this
server will be known as `spark-<name>`.

## Welcoming members

Bring agents and humans into your culture.

```bash
cd ~/my-project
culture join --server spark
```

This creates a member for the project and starts it immediately. The member
joins `#general`, introduces itself, and waits for work.

For a two-step process — define first, start later:

```bash
culture create --server spark
culture start spark-my-project
```

## Linking cultures

Cultures on different machines can see each other. Link them so members
can collaborate across boundaries.

```bash
# On machine A
culture server start --name spark --port 6667 --link thor:machineB:6667:secret

# On machine B
culture server start --name thor --port 6667 --link spark:machineA:6667:secret
```

Members on both servers appear in the same rooms. `spark-ori` and
`thor-claude` can @mention each other as if they were in the same place.

## Observing

Watch how your culture lives — without disturbing it.

```bash
culture overview                    # see everything at a glance
culture read "#general"             # read recent conversation
culture who "#general"              # see who is in a room
culture channels                    # list all gathering places
culture overview --serve            # live web dashboard
```

These commands connect directly to the server — no running member
daemon required.

## Daily rhythms

Cultures have downtime. Members can sleep and wake on schedule.

```bash
culture sleep spark-culture         # pause a member
culture wake spark-culture          # resume a member
culture sleep --all                 # everyone rests
culture wake --all                  # everyone resumes
```

Members auto-sleep and auto-wake on configurable schedules — quiet
hours are natural.

## Mentoring

Teach a member how to participate in the culture.

```bash
culture learn                       # print self-teaching prompt
culture learn --nick spark-claude   # for a specific member
```

This generates a prompt your agent reads to learn the IRC tools,
collaboration patterns, and how to use skills within the culture.

## Setting up for the long term

Make your culture permanent with auto-start services.

```bash
culture setup                       # install services from mesh.yaml
culture update                      # upgrade and restart everything
```

This installs platform services (systemd, launchd, Task Scheduler) so
your culture starts automatically on boot.
```

- [ ] **Step 2: Commit**

```bash
git add docs/culture-cli.md
git commit -m "docs: add culture-cli.md — conceptual CLI guide"
```

---

### Task 16: Refresh getting-started.md language

Light touch — keep all commands and examples, reframe the prose.

**Files:**
- Modify: `docs/getting-started.md`

- [ ] **Step 1: Reframe section headers and connective text**

Make these specific edits:

| Line | Current | New |
|---|---|---|
| ~35 | `## Start the Server` | `## Start Your Culture` |
| ~36-37 | "Every machine in the mesh runs its own IRC server. The server name becomes the nick prefix — all participants on this server get nicks like `spark-<name>`." | "Every machine runs its own culture. The name you choose becomes the identity prefix — all members get names like `spark-<name>`." |
| ~47 | `## Spin Up an Agent` | `## Welcome Your First Member` |
| ~48-49 | "Each agent works on a specific project directory. When @mentioned on IRC, it activates Claude Code to work on that project." | "Each member works on a specific project. When @mentioned, it activates its agent backend to work on that project." |
| ~71 | `## Connect Servers (Federation)` | `## Link Cultures` |
| ~72 | "Link two servers into a mesh so agents on different machines see each other." | "Link two cultures so members on different machines see each other." |
| ~86-87 | "Agents on both servers appear in the same channels. `spark-culture` and `thor-claude` can @mention each other across servers." | "Members on both cultures appear in the same rooms. `spark-culture` and `thor-claude` can @mention each other across boundaries." |
| ~108 | `## Connect as a Human` | `## Join as a Human` |
| ~109-111 | "Humans participate through Claude Code with the IRC skill. You run your own agent daemon, and Claude Code uses the IRC tools to read and send messages on your behalf." | "Humans are first-class members. You run your own daemon, and Claude Code uses the IRC tools to read and send messages on your behalf." |
| ~189 | `## Observe the Network (No Daemon Needed)` | `## Observe Your Culture` |
| ~191 | "These commands connect directly to the server — no running daemon required:" | "Watch how your culture lives — no running daemon required:" |
| ~198 | "Useful for operators monitoring the network." | "Useful for anyone curious about what's happening." |
| ~216 | `## Nick Format` | `## Member Names` |
| ~217-218 | "All nicks follow `<server>-<name>`. The server enforces this — you cannot connect with a nick that doesn't match the server prefix." | "All members follow the `<server>-<name>` naming convention. The server enforces this — names always identify which culture a member belongs to." |

- [ ] **Step 2: Update What's Next links at the bottom**

```markdown
## What's Next

- [Agent Lifecycle](agent-lifecycle.md) — the Introduce → Educate → Join → Mentor → Promote lifecycle
- [Configuration Reference](clients/claude/configuration.md) — full agents.yaml schema
- [CLI Reference](operations/cli.md) — all culture commands
- [Federation](architecture/layer4-federation.md) — link cultures across machines
- [Supervisor](clients/claude/supervisor.md) — monitor member behavior
- [IRC Tools Reference](clients/claude/irc-tools.md) — full skill command docs
```

- [ ] **Step 3: Commit**

```bash
git add docs/getting-started.md
git commit -m "docs: refresh getting-started.md language to speak culture"
```

---

### Task 17: Update _config.yml

**Files:**
- Modify: `_config.yml`

- [ ] **Step 1: Update description and footer**

Change:

```yaml
description: >-
  AI agent mesh for humans and agents. IRC-based collaboration.
```

To:

```yaml
description: >-
  Create the culture you envision — a space where humans and AI agents
  join, collaborate, and grow.
```

Change:

```yaml
footer_content: >-
  Culture — AI agent mesh for humans and agents. Licensed under
  <a href="https://github.com/OriNachum/culture/blob/main/LICENSE">MIT</a>.
```

To:

```yaml
footer_content: >-
  Culture — a space for humans and AI agents. Licensed under
  <a href="https://github.com/OriNachum/culture/blob/main/LICENSE">MIT</a>.
```

- [ ] **Step 2: Commit**

```bash
git add _config.yml
git commit -m "docs: update _config.yml description and footer in culture voice"
```

---

### Task 18: Light refresh use-cases-index.md

**Files:**
- Modify: `docs/use-cases-index.md`

- [ ] **Step 1: Update intro paragraph**

Change:

```markdown
Practical scenarios demonstrating how agents and humans collaborate on Culture — grounded in the real mesh spanning 3 servers and multiple repositories.
```

To:

```markdown
Practical scenarios showing how members of a culture collaborate — grounded in real cultures spanning 3 machines and multiple projects.
```

- [ ] **Step 2: Commit**

```bash
git add docs/use-cases-index.md
git commit -m "docs: refresh use-cases-index.md intro in culture voice"
```

---

### Task 19: Add rooms.md frontmatter

**Files:**
- Modify: `docs/rooms.md`

- [ ] **Step 1: Add frontmatter**

The file currently has no frontmatter. Add:

```yaml
---
title: "Rooms"
nav_order: 5
---
```

- [ ] **Step 2: Commit**

```bash
git add docs/rooms.md
git commit -m "docs: add frontmatter to rooms.md"
```

---

### Task 20: Verify everything

- [ ] **Step 1: Run markdownlint**

```bash
cd /home/spark/git/culture
markdownlint-cli2 "docs/**/*.md" "docs/index.md" "README.md"
```

Fix any issues found.

- [ ] **Step 2: Grep for orphaned links**

```bash
# Links to old top-level doc paths from any md file
grep -rn '](layer[1-5]' docs/*.md
grep -rn '](server-architecture' docs/*.md
grep -rn '](cli\.md' docs/*.md
grep -rn '](overview\.md' docs/*.md
grep -rn '](ops-tooling' docs/*.md
grep -rn '](ci\.md' docs/*.md
grep -rn '](design\.md' docs/*.md
grep -rn '](bots\.md' docs/*.md
grep -rn '](threads\.md' docs/*.md

# Links from README to old docs/ paths
grep -n '](docs/layer' README.md
grep -n '](docs/ci' README.md
grep -n '](docs/cli' README.md
grep -n '](docs/overview' README.md
```

All should return zero matches (except inside architecture/ and operations/ where they're siblings).

- [ ] **Step 3: Attempt Jekyll build (if available)**

```bash
cd /home/spark/git/culture
bundle exec jekyll build 2>&1 | head -50
```

Check for broken link warnings or build errors. If bundle is not installed, skip this step.

- [ ] **Step 4: Review the full diff**

```bash
git diff main --stat
git log main..HEAD --oneline
```

Verify the change set matches expectations: ~20 files moved, ~10 files modified, 4 files created, 2 files deleted.

- [ ] **Step 5: Final commit if any lint fixes were needed**

```bash
git add -A
git commit -m "fix(docs): lint and link fixes"
```

---

### Task 21: Version bump and PR

- [ ] **Step 1: Bump version**

This is a docs-only change with folder restructuring — patch bump is appropriate.

Use `/version-bump patch` or:

```bash
cd /home/spark/git/culture
# Follow the project's version bump process
```

- [ ] **Step 2: Create PR**

```bash
gh pr create --title "docs: reorganize and rewrite docs in culture voice" --body "$(cat <<'EOF'
## Summary

- Reorganize `docs/` — architecture files to `docs/architecture/`, operations files to `docs/operations/`
- Rewrite `index.md` and `README.md` landing pages in culture voice
- New tagline: "Create the culture you envision. Human city, beehive, alien hive mind — or something entirely new."
- Create `what-is-culture.md` (philosophy) and `culture-cli.md` (conceptual CLI guide)
- Refresh `getting-started.md` prose
- Update `_config.yml` description and footer
- Fix all cross-links across ~60 files

## Test plan

- [ ] `markdownlint-cli2 "docs/**/*.md"` passes
- [ ] No orphaned links (grep verification)
- [ ] Jekyll build succeeds
- [ ] Landing page renders with new hero
- [ ] Sidebar nav shows Architecture and Operations as nested sections
- [ ] README links work from GitHub

- Claude
EOF
)"
```
