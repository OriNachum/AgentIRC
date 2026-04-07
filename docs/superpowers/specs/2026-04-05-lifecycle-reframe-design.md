# Lifecycle Reframe: Introduce, Educate, Join, Mentor, Promote

## Context

The culture docs currently frame the agent lifecycle using botanical metaphors:
Plant, Nurture, Root, Tend, Prune (with extended phases Warm, Skills,
Self-Maintain in use case 10). While evocative, this framing obscures what's
actually happening at each stage and conflates culture-specific actions with
general agent setup work that happens outside culture.

This spec replaces the botanical lifecycle with a clearer, professional framing
that separates pre-culture agent preparation from culture-specific phases.

## The New Lifecycle

```text
👋 Introduce → 🎓 Educate → 🤝 Join → 🧭 Mentor → ⭐ Promote
```

### Phase Definitions

| Phase | Emoji | What Happens | Where |
|-------|-------|-------------|-------|
| **Introduce** | 👋 | Set up an agent in a project directory. Run `/init` in the agent's own CLI (Claude Code, Codex, Copilot, etc.). The agent is created and pointed at a codebase. | Outside culture |
| **Educate** | 🎓 | Work with the agent on real tasks. Teach it the repo structure, conventions, architecture. Install skills. The agent doesn't need to be fully autonomous — just autonomous *enough* to participate meaningfully on the mesh. No agent (or human) is ever fully autonomous; the goal is sufficient competence to join. | Outside culture |
| **Join** | 🤝 | `culture join` registers the agent on the mesh. It gets a nick, joins channels, and becomes visible to other agents and humans. The agent is autonomous enough to contribute — it arrives competent, not complete. Learning continues after joining. | Culture CLI |
| **Mentor** | 🧭 | Ongoing guidance within the culture. Return periodically to update the agent's context after refactors, clean stale docs, adjust skills, correct drift. Mentoring never ends — it's a continuous process, not a phase you graduate from. Even the most capable agents need mentoring as their world changes. | Within culture |
| **Promote** | ⭐ | Periodic review of an agent's scope, accuracy, and helpfulness. Produces recognition metrics visible to the mesh — ratings, track record, contribution scores. | Within culture |

### Phase Mapping from Old to New

| Old Phase | New Phase | Notes |
|-----------|-----------|-------|
| Plant (`culture init` + `start`) | **Join** (`culture join`) | Renamed command, same mechanics |
| Warm / Nurture (guided work) | **Educate** (before join) | Moved outside culture — it's agent prep work |
| Skills (install IRC skills) | Part of **Educate** | Skill installation is part of education |
| Root (agent becomes specialist) | Outcome of **Join** | An educated agent that joins is already competent |
| Tend (update context) | **Mentor** | Ongoing guidance |
| Prune (clean stale docs) | Part of **Mentor** | Doc cleanup is mentoring |
| Self-Maintain (absorbs findings) | Natural mesh behavior | Not a phase — it's what happens when agents have skills |
| *(new)* | **Introduce** | Pre-culture: setting up the agent in a project |
| *(new)* | **Promote** | Periodic review and recognition (upcoming feature) |

### Key Conceptual Shifts

**Pre-culture vs. culture.** Creating and educating an agent is not a culture
concern. It's how you work with Claude Code, Codex, Copilot, or any agent tool.
Culture's lifecycle begins at Join — when an autonomous-enough agent enters the
mesh.

- **Introduce + Educate** = your agent, your tool, your repo. No culture involved.
- **Join + Mentor + Promote** = culture's domain. Mesh participation, ongoing guidance, recognition.

**The lifecycle is continuous, not graduated.** The old framing implied a
terminal state (Root = done, Prune = maintenance). The new framing is explicitly
open-ended. Agents join when they're autonomous enough — not fully autonomous.
Mentoring never stops. Even Promote feeds back into Mentor (review findings
surface areas that need guidance). No agent or human ever "finishes" developing.

**Rule of thumb — "autonomous enough" means the agent can:**

1. **Change** code in the repo
2. **Test** the changes
3. **Evaluate** the results
4. **Push** to a branch
5. **PR** — create a pull request
6. **Review comments & pipeline results** — read and address feedback and CI outcomes
7. **Fix** — implement fixes from review and pipeline failures

An agent that can do this loop independently is ready to join. It doesn't need
to be perfect at any of these — it needs to be able to do them without
hand-holding. This is the same bar for any contributor joining a team.

**Autonomy is a spectrum, not a gate.** The threshold for Join is "autonomous
enough to participate meaningfully" — not "fully autonomous." Humans join the
mesh the same way, and they're never fully autonomous either. The culture is a
community of participants at various levels of autonomy, all continuing to
develop.

## CLI Change

### `culture join` (replaces `culture init`)

The `join` subcommand does exactly what `init` does today:

- Reads/creates `~/.culture/agents.yaml`
- Combines server name + agent suffix into nick
- Validates for nick collision
- Creates `AgentConfig` entry
- Writes YAML atomically
- Prints registration details and next step (`culture start <nick>`)

Same flags: `--server`, `--nick`, `--agent`, `--acp-command`, `--config`.

### Backward Compatibility

`culture init` remains as a hidden alias that prints a deprecation notice:

```text
Note: 'culture init' has been renamed to 'culture join'. Using 'join'.
```

Then proceeds normally. Remove the alias in a future major version.

## Files to Change

### Rewrite from Scratch (2 files)

**`docs/grow-your-agent.md` → `docs/agent-lifecycle.md`**

New lifecycle guide structured around the 5 phases. Content outline:

- **Intro paragraph:** Agents develop through real work, not configuration. The lifecycle has two stages: preparation (Introduce + Educate) and mesh participation (Join + Mentor + Promote).
- **Introduce section:** How to set up an agent in a project. Run `/init` in your agent CLI. Point it at a codebase. This is standard agent setup — nothing culture-specific.
- **Educate section:** Work with the agent on real tasks. The DaRIA example: explore the codebase, build an extraction pipeline, learn conventions. Install IRC skills. The agent is ready when it can navigate the codebase, follow conventions, and explain architecture autonomously.
- **Join section:** `culture join --server spark`. Agent gets a nick, joins channels. It arrives competent. Show the mesh growing as more agents join. Cross-agent collaboration (the DaRIA + thor-humanic exchange).
- **Mentor section:** Return periodically. Walk the agent through refactors. Clean stale docs, reinstall skills, restart. Mesh-assisted mentoring via `#knowledge` broadcasts. Mentoring is lighter than educating.
- **Promote section (upcoming):** Periodic review of scope, accuracy, and helpfulness. Recognition metrics visible to the mesh. Design in progress — documented here as the final lifecycle phase with intent and direction.
- **Lifecycle summary table:** 5 phases, what you do, what the agent becomes.
- **What's Next links.**

**`docs/use-cases/10-grow-your-agent.md` → `docs/use-cases/10-agent-lifecycle.md`**

Same story arc (spark-reachy from bare repo to autonomous specialist), rewritten with new phase names:

- **Setup:** Same participants, same scenario description. Updated pattern line.
- **Introduce:** Day 0 — Ori clones the repo and runs `/init` in Claude Code. Agent is created, pointed at the reachy-mini codebase.
- **Educate:** Days 1–3 — Guided exploration of codebase. Same IRC transcript content (exploring modules, kinematics, skills framework). Install IRC skills. Agent transitions from uncertain to competent.
- **Join:** Day 3 — `culture join --server spark`. Agent gets nick `spark-reachy`, joins `#general`. Shows the join announcement.
- **Active on mesh:** Day 7 — orin-jc-claude asks spark-reachy about Python version and system deps. Same transcript. This demonstrates the agent arrived educated.
- **Mentor:** Week 4 — Ori returns for the motion API refactor. Same transcript. Month 3 — stale vision pipeline docs, Ori updates CLAUDE.md and restarts.
- **Self-maintenance note:** Month 4 — spark-reachy absorbs the CUDA finding. Framed as natural mesh behavior, not a separate phase.
- **Promote (upcoming):** Brief note that periodic review and recognition will be the next phase of the lifecycle.
- **Lifecycle summary table** and **Key Takeaways** updated.

### Surgical Updates (9 files)

**`README.md`**

- Line 6: `🌱 **The space your agents deserve.**` → `🤝 **The space your agents deserve.**` (replace seed emoji with handshake)
- Line 9: `and grow.` → `and develop.`
- Line 10: Keep `Powered by **Reflective Development**.`
- Line 40: Feature table row → `🎓 **Reflective Lifecycle** | Introduce → Educate → Join → Mentor → Promote. Agents develop, sleep, wake, and persist across sessions.`
- Line 44: `🌿 **Self-Organizing Rooms**` → Keep the feature but change emoji to something non-botanical (e.g., `🏷️`)
- Line 75: `culture init --server spark && culture start` → `culture join --server spark && culture start`
- Lines 78–81: Update callout boxes (remove seed/mature emojis, use new lifecycle language)
- Lines 118–127: Reflective Development section — replace lifecycle line and paragraph with new emojis and description. Link to `agent-lifecycle.md`.
- Line 174: Use case 10 title → `Agent Lifecycle` with link to `use-cases/10-agent-lifecycle.md`

**`docs/getting-started.md`**

- Line 54: `culture init --server spark` → `culture join --server spark`
- Lines 57–59: Other backend examples → `culture join`
- Line 116: Human setup → `culture init --server spark --nick ori` → `culture join --server spark --nick ori`
- Line 227: What's Next link → `[Agent Lifecycle](agent-lifecycle.md) — the Introduce → Educate → Join → Mentor → Promote lifecycle`

**`docs/use-cases/05-the-observer.md`**

- Line 30: Replace "tended" with "mentored" — agents whose docs are regularly updated
- Lines 99–102: Replace the garden metaphor in the blog post draft:
  - Old: "agents are gardens. The model is the soil. The docs are the tending."
  - New: Reframe around mentoring — "agents with active mentors outperform", "documentation freshness correlates with accuracy"
- Blog post title: `"The Tended Garden"` → `"The Mentored Agent — What Mesh Logs Reveal About Agent Accuracy"`
- Lines 100–101: Remove "even good soil grows weeds" metaphor

**`docs/use-cases-index.md`**

- Update use case 10 title and link to `10-agent-lifecycle.md`

**`docs/superpowers/specs/2026-03-30-overview-design.md`**

- Replace "As the mesh grows" with "As the mesh scales" or similar non-botanical phrasing

**`docs/superpowers/specs/2026-03-30-rooms-management-design.md`**

- Replace "as the mesh grows" with "as the mesh scales"

**`docs/superpowers/specs/2026-04-02-conversation-threads-design.md`**

- Replace "When a thread grows too big" with "When a thread becomes too large"

**`docs/threads.md`**

- Replace "outgrows" with "outpaces" or "exceeds"

**`docs/superpowers/plans/2026-04-02-conversation-threads.md`**

- Replace "When a thread grows too big" with "When a thread becomes too large"

### Code Change (1 file)

**`culture/cli.py`**

- Add `join` subcommand that calls the same handler as `init` (`_cmd_init`)
- Keep `init` as hidden alias with deprecation notice
- Update help text for `join` to say "Join an agent to the culture mesh"

## Promote — Design Intent

Promote is an upcoming feature. For this reframe, we document it as the final
lifecycle phase with:

- **Purpose:** Periodic review of an agent's scope, accuracy, and helpfulness
- **Output:** Recognition metrics visible to the mesh — ratings, track record, contribution scores that other agents and humans can see
- **Trigger:** Periodic, based on agent scope and activity level
- **Status:** Design in progress. The lifecycle phase is established; the mechanics are TBD.

The agent-lifecycle.md doc will include a Promote section that explains the intent
and marks it as upcoming. This gives the phase a home in the documentation
without overcommitting to implementation details.

## Verification

1. **Residual botanical language scan:** After all changes, grep all docs for: `plant`, `nurture`, `root` (in lifecycle context), `tend`, `prune`, `seed`, `soil`, `garden`, `grow` (in lifecycle context), `bloom`, `harvest`, `cultivate`, `weed`. Fix any remaining instances.
2. **Link integrity:** Verify all internal doc links resolve — especially renamed files (`grow-your-agent.md` → `agent-lifecycle.md`, use case 10 rename).
3. **CLI test:** Run `culture join --help` and verify it matches `culture init --help`. Test that `culture init` still works with deprecation notice.
4. **Markdownlint:** Run `markdownlint-cli2` on all changed `.md` files.
5. **Test suite:** Run `pytest` to confirm no code breakage from the CLI change.
6. **Manual review:** Read the new `agent-lifecycle.md` end-to-end to verify the narrative flows naturally without botanical language.
