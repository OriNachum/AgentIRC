---
title: When Not to Use
nav_order: 4
permalink: /when-not-to-use/
sites: [citation-cli]
---

## When Not to Use Citation CLI

Citation CLI is designed for a specific situation: multiple
consumers that share infrastructure code but need to diverge
independently. Outside that situation, traditional approaches are
often better.

### Compliance and provenance requirements

If your environment requires traceability to a specific published
artifact — compliance audits, regulated industries, SBOM
requirements that trace back to an exact audited package version —
traditional dependencies remain the right choice.

Synthesizing code into your own files breaks the chain of custody
by design. There is no published artifact to point to, no version
to audit against. The code becomes yours, indistinguishable from
code you wrote yourself.

### Code that must stay identical

If shared code **must** remain identical across all consumers —
crypto primitives, protocol parsers, security-critical validation
logic — citation-cli is the wrong tool. The entire point of the
pattern is that consumers can modify their copies. Use a versioned
package with pinned dependencies instead.

### Few consumers, low divergence

If you have two or three consumers that mostly use the shared code
as-is with minimal engagement, the overhead of tracking citation
metadata may not be worth it. A shared internal package with
well-defined extension points might serve you better.

Citation CLI's value scales with divergence. If consumers barely
diverge, the pattern adds complexity without adding freedom.

### When vendoring is sufficient

If you want to copy code but don't need organic placement
(synthesis) or metadata tracking, plain vendoring works fine.
Copy the files into a `vendor/` directory, leave them untouched,
and update manually when needed.

Citation CLI adds value over vendoring when you need to:

- Track which files were quoted, paraphrased, or synthesized.
- Absorb code into existing files.
- Detect drift in quoted files.
- Inform future updates with provenance metadata.

### Summary

| Situation | Use |
| --------- | --- |
| Consumers expected to diverge | citation-cli |
| Monorepo, skip the publish step | citation-cli |
| Compliance/provenance required | Traditional packages |
| Code must stay identical | Pinned dependencies |
| Few consumers, low divergence | Shared internal package |
| Copy but don't modify | Plain vendoring |
