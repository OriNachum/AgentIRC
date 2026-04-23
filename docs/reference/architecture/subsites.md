---
title: "Sub-sites on culture.dev"
parent: "Architecture"
grand_parent: "Reference"
nav_order: 4
sites: [agentirc, culture]
description: The reference pattern for hosting an AgentCulture project's docs as a sub-site under culture.dev (e.g. /agex/, /afi/).
permalink: /reference/architecture/subsites/
---

# Sub-sites on `culture.dev`

AgentCulture projects whose primary docs site should live under the
shared `culture.dev` origin — so navigation between them is same-origin,
cache hits survive cross-project jumps, and external links live at one
canonical host — follow a single reference pattern. `culture.dev/agex/`
and `culture.dev/afi/` are the two current instances; `zehut` and
`shushu` will follow.

This page blesses that pattern as the reference scaffold and lists the
exact edits a new sub-site needs on both the project side and the
culture side.

## When to make a project a sub-site

- The project is an AgentCulture first-class namespace
  (e.g. `culture afi`, `culture devex`) and wants a public docs home.
- The project's docs are natural neighbours of the other
  `culture.dev/*` sub-sites — agents and humans should be able to
  navigate between them without leaving the origin.
- The project is comfortable deploying via Cloudflare Pages with its
  docs rooted at a path prefix (`baseurl: /<project>`), not a
  subdomain.

If any of those don't hold, keep the project's docs on its own origin
and cross-link via `rel=related` only.

## Reference scaffold (project side)

Mirror the `afi-cli` scaffold ([agentculture/afi-cli#7](https://github.com/agentculture/afi-cli/pull/7))
or the earlier `agex-cli` scaffold it was modeled on. Both are blessed;
new sub-sites should start from the afi-cli version because it includes the later
refinements.

Required pieces in the project repo:

- `docs/_config.yml` — Jekyll config with `url: https://culture.dev`
  and `baseurl: /<project>`. Path-prefix hosting, not subdomain.
- **Theme:** [`just-the-docs`](https://just-the-docs.com/) (matches
  the rest of the culture.dev family).
- **Plugin:** `jekyll-sitemap` so `/<project>/sitemap.xml` generates
  automatically.
- `docs/_includes/head_custom.html` — `rel=related` back-links to the
  other culture.dev sub-sites (optional but recommended).
- `.github/workflows/docs.yml` — builds `docs/` and deploys to a
  Cloudflare Pages project named `<project>`. See the afi-cli workflow
  for the canonical job shape.

**Not in the project repo:**

- The Cloudflare Pages project itself, custom-domain binding, DNS
  records, Worker / Redirect Rule for path routing —
  tracked in [agentculture/cloudflare](https://github.com/agentculture/cloudflare).

## Reference scaffold (culture side)

Every sub-site touches exactly five files in this repo. The diff for
`culture.dev/afi/` is the canonical example (PR #289); the `agex`
entries in the same files are the prior example.

| File | Edit |
|------|------|
| `_data/sites.yml` | Add `<project>: https://culture.dev/<project>/`. Centralises every cross-site URL so links never hard-code the origin. |
| `_config.culture.yml` (`aux_links:`) | Add `"Display Name": - "https://culture.dev/<project>/"` — shows up in the top nav bar. |
| `_config.culture.yml` (`footer_content:`) | Add a one-line description + link, parallel to the agex / afi entries. |
| `_includes/head_custom.html` | Add `<link rel="related" href="{{ site.data.sites.<project> }}" title="Display Name">` so cross-site discovery is declarative. |
| `sitemap.html` | Add a `<sitemap>` entry pointing at `/<project>/sitemap.xml` (see the `afi` and `agex` lines in this file) so search engines see the sub-site. |

That is the whole culture-side cost. No `_config.culture.yml` routing
block is needed — the path prefix is served by Cloudflare, not Jekyll.

## Required edits vs. optional

All five culture-side edits above are **required** for a sub-site to be
considered properly wired. A sub-site that skips `rel=related` or
`sitemap.html` is "reachable but not discoverable" and should not ship.

On the project side, `just-the-docs` and `jekyll-sitemap` are
**required**; everything else (landing-page content, `rel=related`
back-links, custom `head_custom.html` tweaks) is project-specific.

## Checklist for a new sub-site

1. Land the Jekyll scaffold in the project repo (model on `afi-cli`'s
   `docs/` + `.github/workflows/docs.yml`).
2. File the Cloudflare companion issue in
   [agentculture/cloudflare](https://github.com/agentculture/cloudflare)
   asking for the Pages project + path routing.
3. Open a PR against this repo adding the five file edits above.
   Reference the Cloudflare issue in the PR body so ordering is
   explicit (the Pages project must exist before nav links go live,
   otherwise the aux-link 404s).
4. After merge, verify `https://culture.dev/<project>/` returns 200
   and `curl -sI https://culture.dev/sitemap.xml | grep
   <project>/sitemap.xml` finds the sub-sitemap entry.

## See also

- [`culture devex` and universal verbs]({{ '/reference/cli/devex/' | relative_url }}) — the CLI-side sibling pattern for embedding a project.
- [`culture afi`]({{ '/reference/cli/afi/' | relative_url }}) — the second live sub-site; files in this PR are the canonical example.
- [agentculture/cloudflare](https://github.com/agentculture/cloudflare) — DNS / Pages / redirect-rule configuration for culture.dev and its sub-sites.
