## Why

Anthropic moved every engineering article from `/engineering/*` to `/research/*` on 2026-10-20 while retaining `/engineering` as a curated landing page. The sitemap therefore contains no `/engineering/*` articles, so the completeness guard correctly fails every run. The same site revision added news section landing pages and research team pages to the sitemap, which the current prefix-only classifier would misreport as content.

## What Changes

- Fetch the exact `https://www.anthropic.com/engineering` page as a required category source.
- Extract trusted, sitemap-backed article links from that page and classify them as engineering even though their canonical path is now `/research/*`.
- Remove those engineering articles from research to preserve exclusive category ownership.
- Exclude known news section landing pages and nested research team routes.
- Migrate baselines monotonically so URL moves and resurfaced historical pages are not replayed.
- Preserve genuinely new items first observed after the last successful run.

## Capabilities

### Modified Capabilities
- `sitemap-parser`: Support curated engineering classification and structural exclusions.
- `issue-state`: Document the verified one-time baseline migration required by an upstream URL taxonomy change.

## Impact

- Changes to `src/sitemap.py`, `src/main.py`, tests, bilingual documentation, repository guidance, and OpenSpec.
- One-time verified GitHub Issue baseline unions before deployment.
- The workflow schedule and delivery guarantees remain unchanged.
